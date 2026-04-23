from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Documentation", layout="wide")

ROOT_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT_DIR / "docs"

DOC_FILES = {
    "README": ROOT_DIR / "README.md",
    "Project Report": DOCS_DIR / "PROJECT_REPORT.md",
    "Function Reference": DOCS_DIR / "FUNCTION_REFERENCE.md",
    "Requirements Audit": DOCS_DIR / "REQUIREMENTS_AUDIT.md",
    "Roadmap": DOCS_DIR / "ROADMAP.md",
}


@st.cache_data(show_spinner=False)
def read_text_file(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return f"# Missing File\n\nThe file `{file_path}` was not found."
    return file_path.read_text(encoding="utf-8")


def render_doc(label: str, path: Path):
    st.subheader(label)
    st.caption(str(path.relative_to(ROOT_DIR)))

    content = read_text_file(str(path))
    st.markdown(content)

    with st.expander("Raw Source"):
        st.code(content, language="markdown")


st.title("Project Documentation")
st.markdown(
    """
This page makes the submission documents readable from inside the dashboard.

Use it for project onboarding, requirements review, implementation reference, and roadmap planning.
"""
)

doc_tabs = st.tabs(list(DOC_FILES.keys()))

for tab, (label, path) in zip(doc_tabs, DOC_FILES.items()):
    with tab:
        render_doc(label, path)
