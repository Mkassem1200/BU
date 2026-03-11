#!/usr/bin/env python3
"""
Dubai Cares Website Monitor
Checks website availability every hour and sends email + mobile notifications.
"""

import os
import sys
import time
import logging
import smtplib
import ssl
import json
import requests
import schedule
import yaml
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log"),
    ],
)
log = logging.getLogger(__name__)


# ── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class SiteStatus:
    name: str
    url: str
    is_up: bool
    status_code: Optional[int]
    response_time_ms: Optional[float]
    error: Optional[str]
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> str:
        if self.is_up:
            return (
                f"✅ {self.name} | {self.url}\n"
                f"   Status: {self.status_code} | Response: {self.response_time_ms:.0f}ms"
            )
        return (
            f"❌ {self.name} | {self.url}\n"
            f"   Error: {self.error or f'HTTP {self.status_code}'}"
        )


# ── Config loader ─────────────────────────────────────────────────────────────
def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ── Website checker ──────────────────────────────────────────────────────────
def check_site(site: dict, timeout: int, retries: int, retry_delay: int) -> SiteStatus:
    url = site["url"]
    name = site["name"]
    expected_status = site.get("expected_status", 200)

    for attempt in range(1, retries + 1):
        try:
            start = time.monotonic()
            resp = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": "DubaiCaresMonitor/1.0"},
                verify=site.get("check_ssl", True),
            )
            elapsed = (time.monotonic() - start) * 1000

            is_up = resp.status_code == expected_status
            return SiteStatus(
                name=name,
                url=url,
                is_up=is_up,
                status_code=resp.status_code,
                response_time_ms=elapsed,
                error=None if is_up else f"Unexpected HTTP {resp.status_code}",
            )
        except requests.exceptions.SSLError as e:
            err = f"SSL Error: {e}"
        except requests.exceptions.ConnectionError as e:
            err = f"Connection Error: {e}"
        except requests.exceptions.Timeout:
            err = f"Timed out after {timeout}s"
        except requests.exceptions.RequestException as e:
            err = f"Request Error: {e}"

        log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, name, err)
        if attempt < retries:
            time.sleep(retry_delay)

    return SiteStatus(
        name=name, url=url, is_up=False,
        status_code=None, response_time_ms=None, error=err,
    )


# ── Email notifications ───────────────────────────────────────────────────────
def send_email(cfg: dict, subject: str, html_body: str, text_body: str):
    email_cfg = cfg["notifications"]["email"]
    if not email_cfg.get("enabled"):
        return

    smtp_host = os.getenv("SMTP_HOST", email_cfg.get("smtp_host", "smtp.gmail.com"))
    smtp_port = int(os.getenv("SMTP_PORT", email_cfg.get("smtp_port", 587)))
    from_addr = os.getenv("EMAIL_FROM", email_cfg.get("from_address", ""))
    password   = os.getenv("EMAIL_PASSWORD", "")

    raw_to = os.getenv("EMAIL_TO", "")
    to_addrs = [a.strip() for a in raw_to.split(",") if a.strip()]
    if not to_addrs:
        to_addrs = email_cfg.get("to_addresses", [])
    to_addrs = [a for a in to_addrs if a]

    if not from_addr or not password or not to_addrs:
        log.warning("Email not configured – skipping email alert.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Dubai Cares Monitor <{from_addr}>"
    msg["To"]      = ", ".join(to_addrs)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if email_cfg.get("use_tls", True):
                server.starttls(context=context)
                server.ehlo()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        log.info("Email sent to %s", to_addrs)
    except Exception as e:
        log.error("Failed to send email: %s", e)


# ── Pushover mobile notifications ────────────────────────────────────────────
def send_pushover(cfg: dict, title: str, message: str):
    po_cfg = cfg["notifications"]["pushover"]
    if not po_cfg.get("enabled"):
        return

    user_key  = os.getenv("PUSHOVER_USER_KEY", "")
    api_token = os.getenv("PUSHOVER_API_TOKEN", "")
    if not user_key or not api_token:
        log.warning("Pushover not configured – skipping mobile push.")
        return

    payload = {
        "token":    api_token,
        "user":     user_key,
        "title":    title,
        "message":  message,
        "priority": po_cfg.get("priority", 1),
        "sound":    po_cfg.get("sound", "siren"),
    }
    # Emergency priority requires retry + expire
    if payload["priority"] == 2:
        payload["retry"]  = 60
        payload["expire"] = 3600

    try:
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data=payload, timeout=10,
        )
        resp.raise_for_status()
        log.info("Pushover notification sent.")
    except Exception as e:
        log.error("Failed to send Pushover notification: %s", e)


# ── Twilio SMS (optional) ────────────────────────────────────────────────────
def send_sms(cfg: dict, message: str):
    sms_cfg = cfg["notifications"].get("twilio_sms", {})
    if not sms_cfg.get("enabled"):
        return

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM", sms_cfg.get("from_number", ""))
    raw_to      = os.getenv("TWILIO_TO", "")
    to_numbers  = [n.strip() for n in raw_to.split(",") if n.strip()]
    if not to_numbers:
        to_numbers = sms_cfg.get("to_numbers", [])
    to_numbers = [n for n in to_numbers if n]

    if not all([account_sid, auth_token, from_number, to_numbers]):
        log.warning("Twilio SMS not configured – skipping SMS alert.")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    for to_num in to_numbers:
        try:
            resp = requests.post(
                url,
                auth=(account_sid, auth_token),
                data={"From": from_number, "To": to_num, "Body": message},
                timeout=10,
            )
            resp.raise_for_status()
            log.info("SMS sent to %s", to_num)
        except Exception as e:
            log.error("Failed to send SMS to %s: %s", to_num, e)


# ── Slack (optional) ─────────────────────────────────────────────────────────
def send_slack(message: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook:
        return
    try:
        requests.post(webhook, json={"text": message}, timeout=10)
        log.info("Slack notification sent.")
    except Exception as e:
        log.error("Failed to send Slack notification: %s", e)


# ── Alert builders ────────────────────────────────────────────────────────────
def _html_alert_table(statuses: list[SiteStatus], alert_type: str) -> str:
    color  = "#d32f2f" if alert_type == "DOWN" else "#2e7d32"
    header = f"🚨 ALERT: Sites DOWN" if alert_type == "DOWN" else "✅ RECOVERY: Sites Back Online"
    rows   = ""
    for s in statuses:
        icon = "❌" if not s.is_up else "✅"
        rows += (
            f"<tr>"
            f"<td style='padding:8px;border:1px solid #ddd'>{icon} {s.name}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'><a href='{s.url}'>{s.url}</a></td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{s.error or s.status_code or 'OK'}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'>"
            f"{'N/A' if s.response_time_ms is None else f'{s.response_time_ms:.0f}ms'}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{s.checked_at.strftime('%Y-%m-%d %H:%M UTC')}</td>"
            f"</tr>"
        )
    return f"""
    <html><body style='font-family:Arial,sans-serif'>
    <h2 style='color:{color}'>{header}</h2>
    <p>The following Dubai Cares websites require attention:</p>
    <table style='border-collapse:collapse;width:100%'>
      <tr style='background:{color};color:white'>
        <th style='padding:8px'>Site</th>
        <th style='padding:8px'>URL</th>
        <th style='padding:8px'>Issue</th>
        <th style='padding:8px'>Response Time</th>
        <th style='padding:8px'>Checked At (UTC)</th>
      </tr>
      {rows}
    </table>
    <p style='color:#666;font-size:12px'>Dubai Cares Website Monitor – checking every hour</p>
    </body></html>
    """


def _text_alert(statuses: list[SiteStatus], alert_type: str) -> str:
    header = "ALERT: Sites DOWN" if alert_type == "DOWN" else "RECOVERY: Sites Back Online"
    lines  = [f"Dubai Cares Monitor – {header}", "=" * 50]
    for s in statuses:
        lines.append(s.summary())
    lines.append(f"\nChecked at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    return "\n".join(lines)


# ── Alert state tracker ───────────────────────────────────────────────────────
class AlertState:
    STATE_FILE = "alert_state.json"

    def __init__(self, cooldown_minutes: int):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self._state: dict[str, dict] = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        with open(self.STATE_FILE, "w") as f:
            json.dump(self._state, f, default=str, indent=2)

    def was_up(self, url: str) -> bool:
        return self._state.get(url, {}).get("is_up", True)

    def last_alerted(self, url: str) -> Optional[datetime]:
        ts = self._state.get(url, {}).get("last_alerted")
        return datetime.fromisoformat(ts) if ts else None

    def should_alert_down(self, url: str) -> bool:
        """True if this is a new outage or cooldown has passed."""
        if self.was_up(url):
            return True  # New outage
        last = self.last_alerted(url)
        if last and (datetime.utcnow() - last) < self.cooldown:
            return False
        return True

    def should_alert_recovery(self, url: str) -> bool:
        return not self.was_up(url)

    def record(self, status: SiteStatus, alerted: bool):
        self._state[status.url] = {
            "name":       status.name,
            "is_up":      status.is_up,
            "last_alerted": datetime.utcnow().isoformat() if alerted else
                            (self._state.get(status.url, {}).get("last_alerted")),
        }
        self._save()


# ── Daily summary ─────────────────────────────────────────────────────────────
_check_results: list[SiteStatus] = []


def send_daily_summary(cfg: dict):
    global _check_results
    if not _check_results:
        return

    now = datetime.utcnow().strftime("%Y-%m-%d")
    subject = f"[Dubai Cares Monitor] Daily Summary – {now}"
    down = [s for s in _check_results if not s.is_up]
    up   = [s for s in _check_results if s.is_up]

    text = (
        f"Daily Summary for {now}\n{'='*50}\n"
        f"Sites UP: {len(up)}/{len(_check_results)}\n"
        f"Sites DOWN: {len(down)}/{len(_check_results)}\n\n"
    )
    for s in _check_results:
        text += s.summary() + "\n"

    html = f"""
    <html><body style='font-family:Arial,sans-serif'>
    <h2>Dubai Cares Monitor – Daily Summary ({now})</h2>
    <p>✅ Up: <b>{len(up)}</b> &nbsp; ❌ Down: <b>{len(down)}</b> &nbsp; Total: <b>{len(_check_results)}</b></p>
    {"<p style='color:green'>All sites are operating normally.</p>" if not down else ""}
    """ + (_html_alert_table(_check_results, "SUMMARY").split("<body")[1].split("</body>")[0]
           if _check_results else "") + "</body></html>"

    send_email(cfg, subject, html, text)
    send_pushover(cfg, "Daily Summary", f"Up:{len(up)} Down:{len(down)} of {len(_check_results)} Dubai Cares sites")
    log.info("Daily summary sent.")


# ── Main check loop ───────────────────────────────────────────────────────────
def run_checks(cfg: dict, state: AlertState):
    global _check_results
    mon   = cfg["monitoring"]
    sites = cfg["websites"]
    notif = cfg["notifications"]

    log.info("Starting check for %d sites...", len(sites))
    statuses: list[SiteStatus] = []

    for site in sites:
        s = check_site(
            site,
            timeout=mon["timeout_seconds"],
            retries=mon["retry_attempts"],
            retry_delay=mon["retry_delay_seconds"],
        )
        statuses.append(s)
        log.info(s.summary())

    _check_results = statuses

    newly_down     = []
    newly_recovered = []

    for s in statuses:
        if not s.is_up:
            if state.should_alert_down(s.url):
                if notif["email"].get("alert_on_down", True):
                    newly_down.append(s)
            state.record(s, alerted=bool(newly_down and s in newly_down))
        else:
            if state.should_alert_recovery(s.url):
                if notif["email"].get("alert_on_recovery", True):
                    newly_recovered.append(s)
            state.record(s, alerted=False)

    # Send DOWN alerts
    if newly_down:
        subject  = f"🚨 ALERT: {len(newly_down)} Dubai Cares Site(s) DOWN"
        txt_body = _text_alert(newly_down, "DOWN")
        html_body = _html_alert_table(newly_down, "DOWN")
        push_msg = "\n".join(f"❌ {s.name}: {s.error or s.status_code}" for s in newly_down)

        send_email(cfg, subject, html_body, txt_body)
        send_pushover(cfg, "Dubai Cares Sites DOWN 🚨", push_msg)
        send_sms(cfg, f"Dubai Cares Monitor:\n{push_msg}")
        send_slack(txt_body)

    # Send RECOVERY alerts
    if newly_recovered:
        subject   = f"✅ RECOVERY: {len(newly_recovered)} Dubai Cares Site(s) Back Online"
        txt_body  = _text_alert(newly_recovered, "RECOVERY")
        html_body = _html_alert_table(newly_recovered, "RECOVERY")
        push_msg  = "\n".join(f"✅ {s.name} is back online" for s in newly_recovered)

        send_email(cfg, subject, html_body, txt_body)
        send_pushover(cfg, "Dubai Cares Sites Recovered ✅", push_msg)
        send_sms(cfg, f"Dubai Cares Monitor:\n{push_msg}")
        send_slack(txt_body)

    log.info(
        "Check complete. Up: %d, Down: %d",
        sum(s.is_up for s in statuses),
        sum(not s.is_up for s in statuses),
    )


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    cfg   = load_config()
    state = AlertState(cfg["alerting"]["cooldown_minutes"])
    mon   = cfg["monitoring"]

    log.info("Dubai Cares Monitor started – checking every %d minute(s).", mon["interval_minutes"])

    # Run immediately on startup
    run_checks(cfg, state)

    # Schedule recurring checks
    schedule.every(mon["interval_minutes"]).minutes.do(run_checks, cfg=cfg, state=state)

    # Schedule daily summary
    if cfg["alerting"].get("send_daily_summary"):
        hour = cfg["alerting"].get("daily_summary_hour", 8)
        schedule.every().day.at(f"{hour:02d}:00").do(send_daily_summary, cfg=cfg)
        log.info("Daily summary scheduled at %02d:00 UTC.", hour)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
