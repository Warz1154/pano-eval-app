import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import io

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
# Default image directory (for Streamlit Cloud: an "images" folder in the repo)
DEFAULT_IMAGE_DIR = str(Path(__file__).parent / "images")

# Where evaluations are stored (local CSV file relative to app.py)
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
    if "last_image_name" not in st.session_state:
        st.session_state.last_image_name = None


# keys we want to RESET when changing image
ANSWER_KEYS = [
    # Likert questions
    "q1", "q2", "q3", "q4", "q5",
    "q6", "q7", "q8", "q9", "q10",
    "q11", "q12", "q13", "q14",
    # comparative & open
    "comp_quality", "aspects_better", "aspects_improve",
    "strengths", "limitations", "recommendations", "willing_future",
]


def reset_answers():
    for k in ANSWER_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def save_evaluation(record: dict):
    df = pd.DataFrame([record])
    header = not EVAL_CSV_PATH.exists()
    df.to_csv(EVAL_CSV_PATH, mode="a", header=header, index=False)


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="Panoramic Image Evaluation Tool",
                       layout="wide")

    init_session_state()

    # ---------------- SIDEBAR: SETTINGS & NAV ----------------
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        img_dir_input = st.text_input(
            "Image directory",
            value=st.session_state.image_dir,
            help="Folder containing the panoramic PNG/JPG images.",
        )
        image_dir = Path(img_dir_input)
        st.session_state.image_dir = img_dir_input

        if not image_dir.is_dir():
            st.error(f"Directory not found: {image_dir}")
            st.stop()

        image_files = get_image_files(image_dir)
        if not image_files:
            st.error(f"No images found in: {image_dir}")
            st.stop()

        # keep index in range
        st.session_state.current_index = max(
            0, min(st.session_state.current_index, len(image_files) - 1)
        )

        # Previous / next buttons
        col_prev, col_count, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅ Prev", use_container_width=True):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1
        with col_next:
            if st.button("Next ➡", use_container_width=True):
                if st.session_state.current_index < len(image_files) - 1:
                    st.session_state.current_index += 1
        with col_count:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"Image {st.session_state.current_index + 1} / {len(image_files)}"
                f"</div>",
                unsafe_allow_html=True,
            )

        # dropdown to jump to specific image
        names = [p.name for p in image_files]
        selected_name = st.selectbox(
            "Jump to image",
            options=names,
            index=st.session_state.current_index,
        )
        st.session_state.current_index = names.index(selected_name)

        current_image = image_files[st.session_state.current_index]

        st.markdown("---")
        st.markdown("**Evaluations are stored in:**")
        st.code(str(EVAL_CSV_PATH), language="bash")

        # download button for evaluations csv if it exists
        if EVAL_CSV_PATH.exists():
            df_existing = pd.read_csv(EVAL_CSV_PATH)
            csv_buf = io.StringIO()
            df_existing.to_csv(csv_buf, index=False)
            st.download_button(
                "⬇️ Download all evaluations (CSV)",
                data=csv_buf.getvalue(),
                file_name="evaluations.csv",
                mime="text/csv",
            )

    # ---------------- MAIN AREA ----------------
    # reset answers if image changed
    if st.session_state.last_image_name != current_image.name:
        reset_answers()
        st.session_state.last_image_name = current_image.name

    st.markdown(
        "<h1 style='margin-bottom:0;'>🦷 Panoramic Image Evaluation Tool</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:0.95rem;color:#cccccc;'>"
        "Evaluate synthetic panoramic images generated from CBCT. "
        "Your ratings and comments are stored securely in <code>evaluations.csv</code> "
        "on the server."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Current image header + display
    st.markdown(
        f"### Current Image: "
        f"<code>{current_image.name}</code>",
        unsafe_allow_html=True,
    )
    st.image(str(current_image), use_container_width=True)

    st.markdown("---")

    # ------------- SECTION 1: Respondent info -------------
    st.subheader("Section 1 – Respondent Information (Optional)")

    col1, col2 = st.columns(2)
    with col1:
        resp_name = st.text_input("Full Name", key="resp_name")
        clinic = st.text_input("Clinic / Hospital", key="clinic")
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
            key="specialization",
        )
        years_exp = st.selectbox(
            "Years of Experience",
            ["", "<5", "5–10", "10–20", ">20"],
            key="years_exp",
        )

    avg_cases = st.selectbox(
        "Average number of panoramic cases per week",
        ["", "<10", "10–30", "30–50", ">50"],
        key="avg_cases",
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

    # ---------- Section 2 ----------
    st.markdown("---")
    st.subheader("Section 2 – Image Quality Assessment")
    st.caption("Rate 1 (Strongly Disagree) to 5 (Strongly Agree).")

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

    # ---------- Section 3 ----------
    st.markdown("---")
    st.subheader("Section 3 – Diagnostic Reliability")

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

    # ---------- Section 4 ----------
    st.markdown("---")
    st.subheader("Section 4 – Comparative Evaluation")

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

    # ---------- Section 5 ----------
    st.markdown("---")
    st.subheader("Section 5 – Usability and Clinical Value")

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

    # ---------- Section 6 ----------
    st.markdown("---")
    st.subheader("Section 6 – Open Feedback")

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
    if st.button("✅ Submit evaluation for this image", type="primary"):
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

        # after submission, clear answers for next image / repeat rating
        reset_answers()


if __name__ == "__main__":
    main()
