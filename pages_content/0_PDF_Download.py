import streamlit as st

from i18n import _
from utils import (
    init_state,
    save_settings,
    run_download_pipeline,
)

init_state()

st.subheader(_("page_exec_title"))
st.caption(_("page_exec_desc"))

st.session_state["target_input"] = st.text_input(
    _("input_label"),
    value=st.session_state["target_input"],
    placeholder=_("input_placeholder"),
)

save_settings(st.session_state["target_input"])

if st.button(_("btn_run"), type="primary", use_container_width=True):
    url = st.session_state["target_input"].strip()

    if not url:
        st.warning(_("warn_empty"))
    else:
        status_holder = st.empty()
        log_placeholder = st.empty()
        progress_bar = st.progress(0)

        code, msg, pdf_path, page_count = run_download_pipeline(
            url, status_holder, log_placeholder, progress_bar
        )

        if code == 0:
            st.markdown(
                """
                <style>
                div[data-testid="stDownloadButton"] button {
                    background-color: #FFD54F !important;
                    color: #111827 !important;
                    border: 1px solid #E0A800 !important;
                    font-weight: 700 !important;
                }
                div[data-testid="stDownloadButton"] button:hover {
                    background-color: #FFCA28 !important;
                    color: #111827 !important;
                    border: 1px solid #D89C00 !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    _("btn_download"),
                    data=f,
                    file_name=st.session_state["last_result_name"],
                    mime="application/pdf",
                    use_container_width=True,
                )
