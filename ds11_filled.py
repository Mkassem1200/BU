"""Generate a filled DS-11 U.S. Passport Application form from passport data."""

from fpdf import FPDF
from datetime import date

# ── Passport data extracted from the uploaded image ──────────────────────────
DATA = {
    "last_name": "KASSEM",
    "first_name": "NOAH",
    "middle_name": "MOHAMAD",
    "dob_month": "01",
    "dob_day": "22",
    "dob_year": "2016",
    "place_of_birth": "United Arab Emirates",
    "sex": "Male",
    "ssn": "___-__-____",               # not on passport
    "height_ft": "__",
    "height_in": "__",
    "hair_color": "________",
    "eye_color": "________",
    "home_address": "________________________________",
    "city": "________________",
    "state": "__",
    "zip": "_____",
    "phone": "(____)___-____",
    "email": "____________________",
    "emergency_contact": "________________",
    "emergency_phone": "(____)___-____",
    "emergency_relation": "________________",
    # Most-recent passport
    "prev_passport_no": "673827855",
    "prev_issue_date": "05/24/2021",
    "prev_exp_date": "05/23/2026",
    "prev_issue_auth": "United States Department of State",
    "travel_date": "__/__/____",
    "travel_destination": "________________",
    "application_date": date.today().strftime("%m/%d/%Y"),
}


class DS11PDF(FPDF):
    TITLE_COLOR = (0, 0, 128)
    HEADER_BG = (0, 0, 128)
    SECTION_BG = (200, 210, 230)
    FIELD_BG = (255, 255, 240)
    NOTE_COLOR = (180, 0, 0)

    def header(self):
        # Red bar
        self.set_fill_color(180, 0, 0)
        self.rect(0, 0, 210, 8, "F")
        # Blue header
        self.set_fill_color(*self.HEADER_BG)
        self.rect(0, 8, 210, 22, "F")
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 11)
        self.cell(0, 8, "U.S. DEPARTMENT OF STATE", ln=True)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(10, 19)
        self.cell(0, 6, "DS-11  Application for a U.S. Passport", ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            8,
            "DS-11  10-2023  |  Generated from passport data  |  Page "
            + str(self.page_no()),
            align="C",
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def section_title(self, title: str):
        self.set_fill_color(*self.SECTION_BG)
        self.set_text_color(*self.TITLE_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, f"  {title}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def labeled_field(self, label: str, value: str, w_label=55, w_value=125, note=""):
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80, 80, 80)
        self.cell(w_label, 4, label, ln=False)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 120)
        self.set_fill_color(*self.FIELD_BG)
        self.cell(w_value, 5, f"  {value}", border=1, fill=True, ln=False)
        if note:
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*self.NOTE_COLOR)
            self.cell(0, 5, f"  {note}", ln=False)
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def two_fields(self, label1, val1, label2, val2, w1=55, v1=55, w2=40, v2=40):
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80, 80, 80)
        self.cell(w1, 4, label1, ln=False)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 120)
        self.set_fill_color(*self.FIELD_BG)
        self.cell(v1, 5, f"  {val1}", border=1, fill=True, ln=False)
        self.cell(5, 5, "", ln=False)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80, 80, 80)
        self.cell(w2, 4, label2, ln=False)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 120)
        self.cell(v2, 5, f"  {val2}", border=1, fill=True, ln=False)
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def checkbox(self, label: str, checked: bool):
        self.set_fill_color(*self.FIELD_BG)
        box_val = "X" if checked else " "
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 120)
        self.cell(8, 5, box_val, border=1, fill=True, ln=False)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"  {label}", ln=True)
        self.ln(1)

    def note_box(self, text: str):
        self.set_fill_color(255, 240, 200)
        self.set_draw_color(*self.NOTE_COLOR)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*self.NOTE_COLOR)
        self.multi_cell(0, 4, text, border=1, fill=True)
        self.set_draw_color(0, 0, 0)
        self.set_text_color(0, 0, 0)
        self.ln(2)


def build_pdf(data: dict, output_path: str):
    pdf = DS11PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── IMPORTANT NOTICE ────────────────────────────────────────────────────
    pdf.note_box(
        "IMPORTANT: DS-11 is used for first-time passport applicants and those whose "
        "most-recent passport was issued before age 16, was lost/stolen, or is damaged. "
        "Fields marked with blanks could not be determined from the passport scan alone "
        "and must be completed by the applicant."
    )

    # ── 1. APPLICANT INFORMATION ─────────────────────────────────────────────
    pdf.section_title("1.  APPLICANT INFORMATION")
    pdf.labeled_field("Last Name / Surname:", data["last_name"])
    pdf.labeled_field("First Name:", data["first_name"])
    pdf.labeled_field("Middle Name:", data["middle_name"])
    pdf.two_fields(
        "Date of Birth (MM/DD/YYYY):",
        f"{data['dob_month']}/{data['dob_day']}/{data['dob_year']}",
        "Sex:",
        data["sex"],
        w1=65, v1=55, w2=15, v2=25,
    )
    pdf.labeled_field("Place of Birth (City & Country):", data["place_of_birth"])
    pdf.labeled_field("Social Security Number:", data["ssn"], note="Required — not on passport")

    # ── 2. PHYSICAL DESCRIPTION ──────────────────────────────────────────────
    pdf.section_title("2.  PHYSICAL DESCRIPTION")
    pdf.two_fields(
        "Height (ft / in):", f"{data['height_ft']}' {data['height_in']}\"",
        "Hair Color:", data["hair_color"],
        w1=45, v1=35, w2=30, v2=40,
    )
    pdf.labeled_field("Eye Color:", data["eye_color"])

    # ── 3. CONTACT INFORMATION ───────────────────────────────────────────────
    pdf.section_title("3.  CONTACT INFORMATION")
    pdf.labeled_field("Home Address:", data["home_address"])
    pdf.two_fields(
        "City:", data["city"],
        "State:", data["state"],
        w1=15, v1=70, w2=15, v2=20,
    )
    pdf.labeled_field("ZIP Code:", data["zip"])
    pdf.labeled_field("Phone Number:", data["phone"])
    pdf.labeled_field("Email Address:", data["email"])

    # ── 4. EMERGENCY CONTACT ─────────────────────────────────────────────────
    pdf.section_title("4.  EMERGENCY CONTACT")
    pdf.labeled_field("Contact Name:", data["emergency_contact"])
    pdf.labeled_field("Relationship:", data["emergency_relation"])
    pdf.labeled_field("Phone:", data["emergency_phone"])

    # ── 5. MOST RECENTLY ISSUED PASSPORT ────────────────────────────────────
    pdf.section_title("5.  MOST RECENTLY ISSUED U.S. PASSPORT")
    pdf.labeled_field("Passport Number:", data["prev_passport_no"])
    pdf.two_fields(
        "Issue Date (MM/DD/YYYY):", data["prev_issue_date"],
        "Expiration Date:", data["prev_exp_date"],
        w1=60, v1=45, w2=35, v2=40,
    )
    pdf.labeled_field("Issuing Authority:", data["prev_issue_auth"])

    pdf.note_box(
        "This passport (No. 673827855) expires 05/23/2026. "
        "As of the application date the passport is expiring within 6 months. "
        "A new passport book/card must be submitted with this application."
    )

    # ── 6. TRAVEL PLANS ──────────────────────────────────────────────────────
    pdf.section_title("6.  TRAVEL PLANS  (complete if known)")
    pdf.labeled_field("Departure Date:", data["travel_date"])
    pdf.labeled_field("Destination Country/Countries:", data["travel_destination"])

    # ── 7. PASSPORT TYPE REQUESTED ───────────────────────────────────────────
    pdf.section_title("7.  PASSPORT REQUESTED")
    pdf.checkbox("Passport Book  (standard 28-page or 52-page)", checked=True)
    pdf.checkbox("Passport Card", checked=False)

    # ── 8. PARENTAL CONSENT (applicant is a minor — DOB 2016) ────────────────
    pdf.section_title(
        "8.  PARENTAL / GUARDIAN CONSENT  "
        "(required — applicant is under age 16 as of application date)"
    )
    pdf.note_box(
        "Both parents/guardians must appear in person, OR one parent must appear "
        "with a notarized Statement of Consent (DS-3053) from the absent parent. "
        "Evidence of sole authority is required if only one parent has legal custody."
    )
    pdf.labeled_field("Parent / Guardian 1 Name:", "________________________________")
    pdf.labeled_field("Parent / Guardian 1 Signature:", "(sign in person before agent)")
    pdf.labeled_field("Parent / Guardian 2 Name:", "________________________________")
    pdf.labeled_field("Parent / Guardian 2 Signature:", "(sign in person before agent)")

    # ── 9. APPLICANT SIGNATURE ───────────────────────────────────────────────
    pdf.section_title("9.  APPLICANT SIGNATURE AND DATE")
    pdf.note_box(
        "Do NOT sign until instructed by the Passport Acceptance Agent. "
        "Signing before the agent voids this application."
    )
    pdf.labeled_field("Applicant / Parent Signature:", "(sign in person before agent)")
    pdf.labeled_field("Date of Application:", data["application_date"])

    # ── 10. FEES ─────────────────────────────────────────────────────────────
    pdf.section_title("10.  FEES  (as of 2024 — verify current amounts at travel.state.gov)")
    rows = [
        ("Passport Book (under 16):", "$135.00 application fee"),
        ("Execution Fee:", "$35.00 (paid to acceptance facility)"),
        ("Passport Card (optional, under 16):", "$15.00"),
        ("Expedite Fee (optional):", "$60.00 additional"),
    ]
    for lbl, val in rows:
        pdf.labeled_field(lbl, val)

    pdf.output(output_path)
    print(f"PDF saved → {output_path}")


if __name__ == "__main__":
    build_pdf(DATA, "/home/user/BU/DS-11_KASSEM_NOAH_MOHAMAD.pdf")
