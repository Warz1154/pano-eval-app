import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
# Folder containing the final PNGs
DEFAULT_IMAGE_DIR = str(Path(__file__).parent / "images")


# Where evaluations are stored (local CSV file)
EVAL_CSV_PATH = Path("evaluations.csv")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def get_image_files(image_dir: Path):
    exts = (".png", ".jpg", ".jpeg")
    return sorted([p for p in image_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in exts])


def init_session_state():
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "image_dir" not in st.session_state:
        st.session_state.image_dir = DEFAULT_IMAGE_DIR


def save_evaluation(record: dict):
    df = pd.DataFrame([record])
    header = not EVAL_CSV_PATH.exists()
    df.to_csv(EVAL_CSV_PATH, mode="a", header=header, index=False)


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="Panoramic Image Evaluation", layout="wide")
    init_session_state()

    st.title("🦷 Panoramic Image Evaluation Tool")
    st.write(
        "This app allows dental professionals to evaluate **synthetic panoramic images** "
        "generated from CBCT and stores the evaluations locally in `evaluations.csv`."
    )

    # ---------------- SIDEBAR ----------------
    st.sidebar.header("Settings")

    img_dir_input = st.sidebar.text_input(
        "Image directory",
        value=st.session_state.image_dir,
        help="Path to the folder containing the PNG panoramas.",
    )

    image_dir = Path(img_dir_input)
    st.session_state.image_dir = img_dir_input

    if not image_dir.is_dir():
        st.error(f"Directory not found: {image_dir}")
        st.stop()

    image_files = get_image_files(image_dir)
    if not image_files:
        st.error(f"No PNG/JPG images found in: {image_dir}")
        st.stop()

    # Make sure index is in range
    st.session_state.current_index = max(
        0, min(st.session_state.current_index, len(image_files) - 1)
    )

    col_prev, col_info, col_next = st.sidebar.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅ Previous", use_container_width=True):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1

    with col_next:
        if st.button("Next ➡", use_container_width=True):
            if st.session_state.current_index < len(image_files) - 1:
                st.session_state.current_index += 1

    with col_info:
        st.write(
            f"Image {st.session_state.current_index + 1} / {len(image_files)}"
        )

    # Dropdown to jump to a specific image
    selected_name = st.sidebar.selectbox(
        "Jump to image",
        options=[p.name for p in image_files],
        index=st.session_state.current_index,
    )
    st.session_state.current_index = [p.name for p in image_files].index(
        selected_name
    )
    current_image = image_files[st.session_state.current_index]

    st.sidebar.markdown("---")
    st.sidebar.write("Evaluations are stored in:")
    st.sidebar.code(str(EVAL_CSV_PATH), language="bash")

    # ---------------- MAIN LAYOUT ----------------
    st.subheader(f"Current Image: `{current_image.name}`")

    # Show image
    st.image(str(current_image), use_container_width=True)

    st.markdown("---")

    # ------------- SECTION 1: Respondent info -------------
    st.header("Section 1 – Respondent Information (Optional)")

    col1, col2 = st.columns(2)
    with col1:
        resp_name = st.text_input("Full Name")
        clinic = st.text_input("Clinic / Hospital")

    with col2:
        specialization = st.selectbox(
            "Specialization",
            [
                "",
                "General Dentist",
                "Oral Radiologist",
                "Oral Surgeon",
                "Orthodontist",
                "Other",
            ],
        )
        years_exp = st.selectbox(
            "Years of Experience",
            ["", "<5", "5–10", "10–20", ">20"],
        )

    avg_cases = st.selectbox(
        "Average number of panoramic cases per week",
        ["", "<10", "10–30", "30–50", ">50"],
    )

    # ------------- Likert helper -------------
    def likert(label, key):
        return st.radio(
            label,
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: f"{x}",
            horizontal=True,
            key=key,
        )

    st.markdown("---")
    st.header("Section 2 – Image Quality Assessment")
    st.write("Rate 1 (Strongly Disagree) to 5 (Strongly Agree).")

    q1 = likert(
        "1. The synthetic panoramic image appears realistic and similar to a true panoramic X-ray.",
        "q1",
    )
    q2 = likert(
        "2. The anatomical structures (teeth, jaw, condyles, sinus) are clearly visible.",
        "q2",
    )
    q3 = likert(
        "3. The contrast and brightness are clinically adequate.",
        "q3",
    )
    q4 = likert(
        "4. The image resolution is sufficient for diagnostic purposes.",
        "q4",
    )
    q5 = likert(
        "5. There are no major artifacts or distortions that affect interpretation.",
        "q5",
    )

    st.markdown("---")
    st.header("Section 3 – Diagnostic Reliability")

    q6 = likert(
        "6. The synthetic image preserves key diagnostic landmarks.",
        "q6",
    )
    q7 = likert(
        "7. I would feel confident using this image to identify caries, bone levels, or lesions.",
        "q7",
    )
    q8 = likert(
        "8. The synthetic panoramic provides sufficient information for treatment planning.",
        "q8",
    )
    q9 = likert(
        "9. I can easily identify anatomical symmetry and dental arch shape.",
        "q9",
    )
    q10 = likert(
        "10. The synthetic image aligns spatially with real panoramic anatomy.",
        "q10",
    )

    st.markdown("---")
    st.header("Section 4 – Comparative Evaluation")

    comp_quality = st.radio(
        "1. Overall quality of the synthetic panoramic compared to a real panoramic image:",
        options=[
            "Much Worse",
            "Slightly Worse",
            "Similar",
            "Slightly Better",
            "Much Better",
        ],
        horizontal=True,
        key="comp_quality",
    )

    aspects_better = st.multiselect(
        "2. Which aspects performed better in the synthetic panoramic? (Select all that apply)",
        options=[
            "Sharpness",
            "Contrast",
            "Coverage",
            "Consistency",
            "Artifact Reduction",
            "None",
        ],
        key="aspects_better",
    )

    aspects_improve = st.text_area(
        "3. Which aspects need improvement?",
        key="aspects_improve",
    )

    st.markdown("---")
    st.header("Section 5 – Usability and Clinical Value")

    q11 = likert(
        "11. The synthetic panoramic can reduce the need for additional exposures.",
        "q11",
    )
    q12 = likert(
        "12. The workflow to generate and view the image is efficient.",
        "q12",
    )
    q13 = likert(
        "13. I would consider integrating such a system into my daily practice.",
        "q13",
    )
    q14 = likert(
        "14. The system could be beneficial when panoramic equipment is unavailable.",
        "q14",
    )

    st.markdown("---")
    st.header("Section 6 – Open Feedback")

    strengths = st.text_area(
        "1. What are the strengths of the synthetic panoramic images?",
        key="strengths",
    )
    limitations = st.text_area(
        "2. What are the limitations or concerns you observed?",
        key="limitations",
    )
    recommendations = st.text_area(
        "3. Any recommendations for improvement?",
        key="recommendations",
    )

    willing_future = st.radio(
        "4. Would you be willing to participate in future studies or clinical trials of this technology?",
        options=["Yes", "No"],
        horizontal=True,
        key="willing_future",
    )

    st.markdown("---")

    # ---------------- SUBMIT ----------------
    if st.button("✅ Submit evaluation for this image"):
        record = {
            "timestamp": datetime.now().isoformat(),
            "image_filename": current_image.name,
            # Respondent info
            "name": resp_name,
            "clinic": clinic,
            "specialization": specialization,
            "years_experience": years_exp,
            "avg_pano_cases_per_week": avg_cases,
            # Likert questions
            "q1_realistic": q1,
            "q2_anatomy_visible": q2,
            "q3_contrast_brightness": q3,
            "q4_resolution": q4,
            "q5_artifacts": q5,
            "q6_landmarks": q6,
            "q7_confidence_diagnosis": q7,
            "q8_treatment_planning": q8,
            "q9_symmetry_arch": q9,
            "q10_alignment": q10,
            "q11_reduces_exposures": q11,
            "q12_workflow_efficient": q12,
            "q13_integrate_practice": q13,
            "q14_beneficial_no_pano": q14,
            # Comparative
            "comparative_quality": comp_quality,
            "aspects_better": "; ".join(aspects_better),
            "aspects_need_improvement": aspects_improve,
            # Open feedback
            "strengths": strengths,
            "limitations": limitations,
            "recommendations": recommendations,
            "willing_future_studies": willing_future,
        }

        save_evaluation(record)
        st.success(
            f"Evaluation saved for **{current_image.name}** "
            f"to `{EVAL_CSV_PATH}`."
        )


if __name__ == "__main__":
    main()
