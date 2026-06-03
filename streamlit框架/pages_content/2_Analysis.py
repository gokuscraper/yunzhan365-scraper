import os
import streamlit as st

from i18n import _
from utils import analyze_result, init_state

init_state()

st.subheader(_("page_analysis_title"))
st.caption(_("page_analysis_desc"))

last_file = st.session_state.get("last_file_path", "")
last_count = st.session_state.get("last_result_count", 0)
last_title = st.session_state.get("last_result_title", "")
last_name = st.session_state.get("last_result_name", "")

if last_file and os.path.exists(last_file):
    size_mb = os.path.getsize(last_file) / (1024 * 1024)
    st.info(
        f"**{_('info_cache')}**\n\n"
        f"- {_('col_title')}: {last_title}\n"
        f"- {_('col_count')}: {last_count} {_('unit')}\n"
        f"- {_('col_file')}: {last_name}\n"
        f"- {_('col_size')}: {size_mb:.2f} MB"
    )

uploaded_file = st.file_uploader(_("file_uploader_label"))

if st.button(_("btn_analyze"), type="primary", use_container_width=True):
    target_path = ""

    if uploaded_file is not None:
        temp_path = f"_uploaded_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        target_path = temp_path
    elif last_file and os.path.exists(last_file):
        target_path = last_file
    else:
        st.warning(_("warn_no_data"))
        st.stop()

    result = analyze_result(target_path)

    if "error" in result:
        st.error(result["error"])
    else:
        st.success(_("success_analysis"))
        cols = st.columns(len(result))
        for i, (key, value) in enumerate(result.items()):
            cols[i].metric(key, str(value))

    if uploaded_file is not None and os.path.exists(temp_path):
        os.remove(temp_path)
