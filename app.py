import streamlit as st
from streamlit_gps_location import gps_location_button
from datetime import date
from fpdf import FPDF
import tempfile
import os
from PIL import Image
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Field Report", layout="centered")

st.title("🔬 Field Discovery Reporter")
st.markdown("Document your scientific discovery in the field.")

# ── 1. User Information ───────────────────────────────────────────────────────
st.header("1. Researcher Information")
researcher_name = st.text_input("Researcher name", placeholder="e.g. Ana García")
discovery_title = st.text_input("Title of discovery", placeholder="e.g. Rare orchid species")
notes = st.text_area("Description / Observations", placeholder="Describe what you observed...")

# ── 2. GPS Location ───────────────────────────────────────────────────────────
st.header("2. GPS Location")
location_data = gps_location_button(buttonText="📍 Get my location")

lat, lon = None, None
if location_data is not None:
    lat = location_data.get("latitude")
    lon = location_data.get("longitude")
    if lat is not None and lon is not None:
        st.success(f"Location captured: Lat {lat:.5f}, Lon {lon:.5f}")
        import pandas as pd
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
    else:
        st.info("Press the button above to capture your GPS coordinates.")
else:
    st.info("Press the button above to capture your GPS coordinates.")

# ── 3. Visual Evidence ────────────────────────────────────────────────────────
st.header("3. Visual Evidence")
photo = st.camera_input("Take a photo as evidence")
if photo is None:
    photo = st.file_uploader("Or upload an image", type=["jpg", "jpeg", "png"])

if photo:
    st.image(photo, caption="Evidence photo", use_column_width=True)

# ── 4. PDF Report Generation ──────────────────────────────────────────────────
st.header("4. Generate Report")

def generate_pdf(name, title, description, lat, lon, photo_bytes):
    pdf = FPDF()
    pdf.add_page()

    # Header banner
    pdf.set_fill_color(34, 110, 50)
    pdf.rect(0, 0, 210, 25, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_y(8)
    pdf.cell(0, 10, "FIELD REPORT", align="C")

    # Reset colour
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)

    # Meta row
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 7, f"Researcher: {name}")
    pdf.cell(0, 7, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True)

    coords_text = (
        f"Coordinates: Lat {lat:.5f}, Lon {lon:.5f}"
        if lat is not None and lon is not None
        else "Coordinates: not captured"
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, coords_text, ln=True)

    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(6)

    # Finding
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Finding: {title}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Observations:", ln=True)
    pdf.multi_cell(0, 6, description if description else "—")
    pdf.ln(4)

    # Photo
    if photo_bytes:
        try:
            img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                img.save(tmp.name, format="JPEG")
                img_w = min(img.width, 120)
                img_h = int(img.height * img_w / img.width)
                pdf.image(tmp.name, x=10, w=img_w, h=img_h)
            os.unlink(tmp.name)
        except Exception as e:
            pdf.cell(0, 7, f"[Photo could not be embedded: {e}]", ln=True)

    # Page number
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"Page {pdf.page_no()}", align="C")

    return pdf.output()


if st.button("📄 Generate PDF Report"):
    errors = []
    if not researcher_name.strip():
        errors.append("• Researcher name is required.")
    if not discovery_title.strip():
        errors.append("• Discovery title is required.")
    if not notes.strip():
        errors.append("• Description / observations are required.")
    if lat is None or lon is None:
        errors.append("• GPS location must be captured.")
    if photo is None:
        errors.append("• A photo is required.")

    if errors:
        st.error("Please complete all required fields:\n" + "\n".join(errors))
    else:
        try:
            photo_bytes = photo.read() if photo else None
            pdf_bytes = generate_pdf(
                researcher_name, discovery_title, notes, lat, lon, photo_bytes
            )
            st.success("✅ Report generated successfully!")
            st.download_button(
                label="⬇️ Download PDF Report",
                data=bytes(pdf_bytes),
                file_name=f"field_report_{date.today()}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"An error occurred while generating the report: {e}")