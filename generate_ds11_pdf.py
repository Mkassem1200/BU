"""
Generate an editable/fillable DS-11 U.S. Passport Application PDF.
Pre-populated from passport scan of KASSEM, NOAH MOHAMAD (DOB 01/22/2016).
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfform
import io, os

OUTPUT = "/home/user/BU/DS-11_KASSEM_NOAH_MOHAMAD_editable.pdf"

# ── Passport data ──────────────────────────────────────────────────────────────
PASSPORT = {
    "last_name":        "KASSEM",
    "first_name":       "NOAH",
    "middle_name":      "MOHAMAD",
    "dob":              "01/22/2016",
    "place_of_birth":   "United Arab Emirates",
    "sex":              "Male (M)",
    "passport_no":      "673827855",
    "issue_date":       "05/24/2021",
    "exp_date":         "05/23/2026",
    "issue_auth":       "United States Department of State",
    "app_date":         "05/10/2026",
}

NAVY   = colors.HexColor("#00008B")
RED    = colors.HexColor("#CC0000")
LBLUE  = colors.HexColor("#CCD8EC")
CREAM  = colors.HexColor("#FFFFF0")
WARN   = colors.HexColor("#FFF3CD")
W      = letter[0]
H      = letter[1]
MARGIN = 0.55 * inch
INNER  = W - 2 * MARGIN

# ── Canvas-level helpers ───────────────────────────────────────────────────────

def draw_header(c, w, h):
    # Red stripe
    c.setFillColor(RED)
    c.rect(0, h - 10, w, 10, fill=1, stroke=0)
    # Navy bar
    c.setFillColor(NAVY)
    c.rect(0, h - 46, w, 36, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, h - 28, "U.S. DEPARTMENT OF STATE")
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, h - 42, "DS-11  |  Application for a U.S. Passport  |  OMB 1405-0004")
    # Right side text
    c.setFont("Helvetica", 7)
    c.drawRightString(w - MARGIN, h - 28, "Exp. 10-31-2026")
    c.drawRightString(w - MARGIN, h - 38, "Estimated Burden: 85 min")


def draw_footer(c, w, page_num):
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica-Oblique", 7)
    c.drawCentredString(
        w / 2, 20,
        f"DS-11 | Pre-filled from passport scan for KASSEM, NOAH MOHAMAD | "
        f"Generated 05/10/2026 | Page {page_num}"
    )
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(MARGIN, 30, w - MARGIN, 30)


def section_bar(c, y, text, w):
    c.setFillColor(LBLUE)
    c.rect(MARGIN, y - 2, INNER, 14, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(MARGIN, y - 2, 4, 14, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN + 9, y + 2, text)
    return y - 20


def notice_box(c, y, text, w, bg=WARN, border=RED):
    lines = []
    words = text.split()
    line = ""
    max_w = INNER - 16
    c.setFont("Helvetica-Oblique", 7.5)
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, "Helvetica-Oblique", 7.5) < max_w:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    box_h = len(lines) * 10 + 8
    c.setFillColor(bg)
    c.setStrokeColor(border)
    c.setLineWidth(0.8)
    c.rect(MARGIN, y - box_h, INNER, box_h, fill=1, stroke=1)
    c.setFillColor(RED)
    c.setFont("Helvetica-Oblique", 7.5)
    for i, ln in enumerate(lines):
        c.drawString(MARGIN + 8, y - 10 - i * 10, ln)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    return y - box_h - 6


def field_row(c, y, label, field_name, prefill="", w_label=180, field_h=16, note=""):
    """Draw label + editable text field."""
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(MARGIN, y, label)
    fx = MARGIN + w_label
    fw = INNER - w_label - (80 if note else 0)
    # field background
    c.setFillColor(CREAM)
    c.setStrokeColor(colors.HexColor("#999999"))
    c.rect(fx, y - 3, fw, field_h, fill=1, stroke=1)
    # pre-filled value
    if prefill:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(fx + 4, y + 2, prefill)
    # AcroForm text field overlaid
    c.acroForm.textfield(
        name=field_name,
        tooltip=label,
        x=fx, y=y - 3,
        width=fw, height=field_h,
        value=prefill,
        fontSize=9,
        borderColor=colors.HexColor("#999999"),
        fillColor=CREAM,
        textColor=NAVY,
        fieldFlags="",
    )
    if note:
        c.setFillColor(RED)
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(fx + fw + 4, y + 2, note)
    return y - field_h - 6


def two_field_row(c, y, label1, name1, pre1, label2, name2, pre2,
                  w_label1=120, w_field1=120, w_label2=80, w_field2=80):
    x = MARGIN
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(x, y, label1)
    fx1 = x + w_label1
    c.setFillColor(CREAM)
    c.setStrokeColor(colors.HexColor("#999999"))
    c.rect(fx1, y - 3, w_field1, 16, fill=1, stroke=1)
    if pre1:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(fx1 + 4, y + 2, pre1)
    c.acroForm.textfield(name=name1, tooltip=label1, x=fx1, y=y - 3,
                         width=w_field1, height=16, value=pre1,
                         fontSize=9, borderColor=colors.HexColor("#999999"),
                         fillColor=CREAM, textColor=NAVY)
    x2 = fx1 + w_field1 + 12
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(x2, y, label2)
    fx2 = x2 + w_label2
    c.setFillColor(CREAM)
    c.rect(fx2, y - 3, w_field2, 16, fill=1, stroke=1)
    if pre2:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(fx2 + 4, y + 2, pre2)
    c.acroForm.textfield(name=name2, tooltip=label2, x=fx2, y=y - 3,
                         width=w_field2, height=16, value=pre2,
                         fontSize=9, borderColor=colors.HexColor("#999999"),
                         fillColor=CREAM, textColor=NAVY)
    return y - 22


def checkbox_row(c, y, name, label, checked=False):
    c.acroForm.checkbox(
        name=name, tooltip=label,
        x=MARGIN, y=y - 12, size=12,
        checked=checked,
        borderColor=colors.HexColor("#555555"),
        fillColor=CREAM,
    )
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN + 16, y - 3, label)
    return y - 18


def sig_line(c, y, label, name, w):
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(MARGIN, y, label)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(MARGIN, y - 18, MARGIN + INNER, y - 18)
    c.setFillColor(RED)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(MARGIN + 4, y - 15, "Sign in person before Passport Acceptance Agent")
    return y - 30


# ── Main builder ───────────────────────────────────────────────────────────────

def build(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle("DS-11 U.S. Passport Application – KASSEM, NOAH MOHAMAD")
    c.setAuthor("U.S. Department of State (pre-filled)")
    c.setSubject("Application for U.S. Passport")

    # ── PAGE 1 ─────────────────────────────────────────────────────────────────
    draw_header(c, W, H)
    y = H - 60

    # ── IMPORTANT NOTICE ──────────────────────────────────────────────────────
    y = notice_box(c, y,
        "IMPORTANT: DS-11 is required (not DS-82) because passport No. 673827855 "
        "was issued when the applicant was age 5 (under 16). DS-82 requires the "
        "passport to have been issued at age 16 or older — a hard U.S. State Dept. "
        "rule. Fields pre-filled from passport scan are shown in blue. "
        "Blank fields must be completed by the applicant before submission.",
        W)

    # ── 1. APPLICANT INFORMATION ───────────────────────────────────────────────
    y = section_bar(c, y, "1.  APPLICANT INFORMATION", W)
    y = field_row(c, y, "Last Name / Surname:", "last_name", PASSPORT["last_name"])
    y = field_row(c, y, "First Name:", "first_name", PASSPORT["first_name"])
    y = field_row(c, y, "Middle Name:", "middle_name", PASSPORT["middle_name"])
    y = two_field_row(c, y,
        "Date of Birth (MM/DD/YYYY):", "dob", PASSPORT["dob"],
        "Sex:", "sex", PASSPORT["sex"],
        w_label1=160, w_field1=120, w_label2=30, w_field2=80)
    y = field_row(c, y, "Place of Birth (City & Country):", "place_of_birth",
                  PASSPORT["place_of_birth"])
    y = field_row(c, y, "Social Security Number:", "ssn", "",
                  note="⚠ Required — not on passport")

    y -= 4
    # ── 2. PHYSICAL DESCRIPTION ───────────────────────────────────────────────
    y = section_bar(c, y, "2.  PHYSICAL DESCRIPTION", W)
    y = two_field_row(c, y,
        "Height (ft / in):", "height", "",
        "Hair Color:", "hair_color", "",
        w_label1=100, w_field1=100, w_label2=75, w_field2=120)
    y = field_row(c, y, "Eye Color:", "eye_color", "")

    y -= 4
    # ── 3. CONTACT INFORMATION ────────────────────────────────────────────────
    y = section_bar(c, y, "3.  CONTACT INFORMATION", W)
    y = field_row(c, y, "Home / Mailing Address:", "address", "")
    y = two_field_row(c, y,
        "City:", "city", "",
        "State:", "state", "",
        w_label1=30, w_field1=160, w_label2=35, w_field2=50)
    y = two_field_row(c, y,
        "ZIP Code:", "zip", "",
        "Primary Phone:", "phone", "",
        w_label1=65, w_field1=80, w_label2=90, w_field2=130)
    y = field_row(c, y, "Email Address:", "email", "")

    y -= 4
    # ── 4. EMERGENCY CONTACT ──────────────────────────────────────────────────
    y = section_bar(c, y, "4.  IN-CASE-OF-EMERGENCY CONTACT", W)
    y = two_field_row(c, y,
        "Contact Full Name:", "emergency_name", "",
        "Relationship:", "emergency_relation", "",
        w_label1=115, w_field1=140, w_label2=80, w_field2=100)
    y = field_row(c, y, "Emergency Phone:", "emergency_phone", "")

    y -= 4
    # ── 5. MOST RECENTLY ISSUED PASSPORT ──────────────────────────────────────
    y = section_bar(c, y, "5.  MOST RECENTLY ISSUED U.S. PASSPORT / CARD", W)
    y = field_row(c, y, "Passport Number:", "prev_passport_no", PASSPORT["passport_no"])
    y = two_field_row(c, y,
        "Issue Date (MM/DD/YYYY):", "prev_issue_date", PASSPORT["issue_date"],
        "Expiration Date:", "prev_exp_date", PASSPORT["exp_date"],
        w_label1=155, w_field1=110, w_label2=90, w_field2=90)
    y = field_row(c, y, "Issuing Authority:", "prev_issue_auth", PASSPORT["issue_auth"])
    y = notice_box(c, y,
        "Passport No. 673827855 expires 05/23/2026. The original passport must be "
        "submitted with this DS-11 application. Since it was issued to a minor under "
        "age 16, DS-82 (mail renewal) is NOT permitted — travel.state.gov.",
        W)

    y -= 4
    # ── 6. TRAVEL PLANS ───────────────────────────────────────────────────────
    y = section_bar(c, y, "6.  TRAVEL PLANS (if known)", W)
    y = two_field_row(c, y,
        "Departure Date (MM/DD/YYYY):", "travel_date", "",
        "Destination Countries:", "travel_dest", "",
        w_label1=170, w_field1=100, w_label2=120, w_field2=70)

    y -= 4
    # ── 7. PASSPORT TYPE REQUESTED ────────────────────────────────────────────
    y = section_bar(c, y, "7.  PASSPORT TYPE REQUESTED", W)
    y = checkbox_row(c, y, "book", "Passport Book  (standard 28-page or large 52-page)", True)
    y = checkbox_row(c, y, "card", "Passport Card  (land/sea travel: Canada, Mexico, Caribbean, Bermuda)", False)

    draw_footer(c, W, 1)
    c.showPage()

    # ── PAGE 2 ─────────────────────────────────────────────────────────────────
    draw_header(c, W, H)
    y = H - 60

    # ── 8. PARENTAL CONSENT (MINOR) ───────────────────────────────────────────
    y = section_bar(c, y,
        "8.  PARENTAL / GUARDIAN CONSENT  "
        "(REQUIRED — applicant NOAH MOHAMAD KASSEM is under age 16)", W)
    y = notice_box(c, y,
        "Both parents/guardians must appear in person at the acceptance facility, OR "
        "one parent appears and provides a completed notarized DS-3053 (Statement of "
        "Consent) from the absent parent. If only one parent has legal custody, bring "
        "documentary evidence (court order, death certificate, etc.).",
        W)
    y -= 6
    y = field_row(c, y, "Parent / Guardian 1 — Full Name:", "parent1_name", "")
    y = field_row(c, y, "Parent / Guardian 1 — Relationship:", "parent1_relation", "")
    y = field_row(c, y, "Parent / Guardian 1 — Phone:", "parent1_phone", "")
    y = sig_line(c, y, "Parent / Guardian 1 Signature:", "sig_parent1", W)
    y -= 8
    y = field_row(c, y, "Parent / Guardian 2 — Full Name:", "parent2_name", "")
    y = field_row(c, y, "Parent / Guardian 2 — Relationship:", "parent2_relation", "")
    y = field_row(c, y, "Parent / Guardian 2 — Phone:", "parent2_phone", "")
    y = sig_line(c, y, "Parent / Guardian 2 Signature:", "sig_parent2", W)

    y -= 10
    # ── 9. APPLICANT SIGNATURE ────────────────────────────────────────────────
    y = section_bar(c, y, "9.  APPLICANT / PARENT SIGNATURE AND DATE", W)
    y = notice_box(c, y,
        "DO NOT SIGN until instructed by the Passport Acceptance Agent. "
        "Signing before the agent voids this application.",
        W, bg=colors.HexColor("#FFE4E4"))
    y -= 6
    y = sig_line(c, y, "Applicant or Parent Signature:", "applicant_sig", W)
    y = field_row(c, y, "Date of Application (MM/DD/YYYY):", "app_date",
                  PASSPORT["app_date"])

    y -= 10
    # ── 10. FEES ──────────────────────────────────────────────────────────────
    y = section_bar(c, y, "10.  FEES  (verify current amounts at travel.state.gov)", W)
    fees = [
        ("Passport Book — minor under 16",       "$135.00", "Paid to U.S. Dept. of State"),
        ("Execution fee",                          "$35.00",  "Paid to acceptance facility"),
        ("Passport Card — optional (minor)",       "$15.00",  "If card also requested"),
        ("Expedite fee — optional",                "$60.00",  "Faster processing"),
        ("1-2 day return delivery — optional",     "$19.53",  "Priority return shipping"),
    ]
    col_w = [210, 70, 200]
    row_h = 14
    # header row
    c.setFillColor(NAVY)
    c.rect(MARGIN, y - row_h, INNER, row_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    for i, (hdr, cx) in enumerate(zip(["Item", "Fee", "Notes"],
                                       [MARGIN + 4, MARGIN + col_w[0] + 4,
                                        MARGIN + col_w[0] + col_w[1] + 4])):
        c.drawString(cx, y - row_h + 3, hdr)
    y -= row_h
    for idx, (item, fee, note) in enumerate(fees):
        bg = colors.HexColor("#EEF2FF") if idx % 2 == 0 else colors.white
        c.setFillColor(bg)
        c.rect(MARGIN, y - row_h, INNER, row_h, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN + 4, y - row_h + 3, item)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NAVY)
        c.drawString(MARGIN + col_w[0] + 4, y - row_h + 3, fee)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#444444"))
        c.drawString(MARGIN + col_w[0] + col_w[1] + 4, y - row_h + 3, note)
        y -= row_h

    y -= 10
    # ── MRZ REFERENCE ─────────────────────────────────────────────────────────
    y = section_bar(c, y, "REFERENCE — Machine-Readable Zone from current passport", W)
    c.setFillColor(colors.HexColor("#111111"))
    c.rect(MARGIN, y - 44, INNER, 44, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#00FF00"))
    c.setFont("Courier-Bold", 10)
    c.drawString(MARGIN + 10, y - 16, "P<USAKASSEM<<NOAH<MOHAMAD<<<<<<<<<<<<<<<<<<<<<")
    c.drawString(MARGIN + 10, y - 30, "6738278551USA1601220M2605236718725846<406404")
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN + 10, y - 42,
        "Type=P  Country=USA  Surname=KASSEM  Given=NOAH MOHAMAD  "
        "No=673827855  DOB=16-01-22  Sex=M  Expiry=26-05-23")

    draw_footer(c, W, 2)
    c.save()
    print(f"✓ Editable PDF saved → {output_path}")


build(OUTPUT)
