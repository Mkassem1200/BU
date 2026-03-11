# Dubai Cares Website Monitor

Monitors Dubai Cares websites every hour and sends **email** and **mobile push notifications** (+ optional SMS) when any site is down or recovers.

## Features

- Checks all configured websites every 60 minutes (configurable)
- Retries failed checks 3 times before alerting
- **Email alerts** via Gmail (or any SMTP server)
- **Mobile push notifications** via [Pushover](https://pushover.net) (iOS & Android)
- **SMS alerts** via [Twilio](https://twilio.com) (optional)
- **Slack alerts** (optional)
- Cooldown period to avoid alert fatigue
- Recovery notifications when a site comes back online
- Daily summary report
- Persists state across restarts (no duplicate alerts)

---

## Quick Start

### 1. Clone & configure

```bash
cd dubai-cares-monitor
cp .env.example .env
```

Edit `.env` with your credentials (see below).

### 2. Add your websites

Edit `config.yaml` and add all Dubai Cares related URLs under `websites:`:

```yaml
websites:
  - name: "Dubai Cares Main Website"
    url: "https://www.dubaicares.ae"
    expected_status: 200
    check_ssl: true

  - name: "My Custom Site"
    url: "https://custom.dubaicares.ae"
    expected_status: 200
    check_ssl: true
```

### 3. Run with Docker (recommended)

```bash
mkdir -p data
docker-compose up -d

# View live logs
docker-compose logs -f
```

### 4. Run directly (Python 3.12+)

```bash
pip install -r requirements.txt
python monitor.py
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `EMAIL_FROM` | Gmail address to send alerts from |
| `EMAIL_PASSWORD` | Gmail **App Password** (not your login password) |
| `EMAIL_TO` | Recipient email(s), comma-separated |
| `PUSHOVER_USER_KEY` | Your Pushover user key |
| `PUSHOVER_API_TOKEN` | Your Pushover application token |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID (optional) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token (optional) |
| `TWILIO_FROM` | Twilio phone number (optional) |
| `TWILIO_TO` | Your mobile number, e.g. `+9715XXXXXXXX` (optional) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL (optional) |

### Setting up Gmail App Password

1. Go to **Google Account → Security → 2-Step Verification** (enable it)
2. Go to **App Passwords** → Select app: `Mail` → Device: `Other`
3. Copy the 16-character password into `EMAIL_PASSWORD`

### Setting up Pushover (Mobile Push)

1. Sign up at [pushover.net](https://pushover.net) (~$5 one-time, free trial)
2. Install the **Pushover app** on your iPhone or Android
3. Create an **Application** at pushover.net → copy the API token
4. Copy your **User Key** from the dashboard
5. Set both in `.env`

### Setting up Twilio SMS (Optional)

1. Sign up at [twilio.com](https://twilio.com)
2. Get a phone number
3. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`, `TWILIO_TO` in `.env`
4. Enable `twilio_sms.enabled: true` in `config.yaml`

---

## Monitoring Configuration (`config.yaml`)

```yaml
monitoring:
  interval_minutes: 60    # Check frequency
  timeout_seconds: 10     # Per-site timeout
  retry_attempts: 3       # Retries before alerting
  retry_delay_seconds: 5  # Delay between retries

alerting:
  cooldown_minutes: 60    # Min time between repeat alerts for same site
  send_daily_summary: true
  daily_summary_hour: 8   # 8 AM UTC daily report
```

---

## Alert Examples

**Down Alert (Email subject):** `🚨 ALERT: 2 Dubai Cares Site(s) DOWN`

**Recovery Alert (Email subject):** `✅ RECOVERY: 2 Dubai Cares Site(s) Back Online`

**Mobile push (Pushover):** Immediate notification with site name and error

---

## Files

```
dubai-cares-monitor/
├── monitor.py          # Main monitoring application
├── config.yaml         # Website list & notification settings
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── Dockerfile          # Container image
├── docker-compose.yml  # Container orchestration
└── data/               # Auto-created: logs + alert state
    ├── monitor.log
    └── alert_state.json
```
