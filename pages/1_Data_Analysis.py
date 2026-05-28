import os
import streamlit as st

from i18n import _
from utils import analyze_pdf, init_state

init_state()

st.subheader(_("page_analysis_title"))
st.caption(_("page_analysis_desc"))

last_pdf = st.session_state.get("last_pdf_path", "")
last_count = st.session_state.get("last_page_count", 0)
last_title = st.session_state.get("last_book_title", "")
last_name = st.session_state.get("last_result_name", "")

if last_pdf and os.path.exists(last_pdf):
    size_mb = os.path.getsize(last_pdf) / (1024 * 1024)
    st.info(
        f"**{_('info_cache')}**\n\n"
        f"- {_('col_title')}: {last_title}\n"
        f"- {_('col_pages')}: {last_count} {_('unit_page')}\n"
        f"- {_('col_file')}: {last_name}\n"
        f"- {_('col_size')}: {size_mb:.2f} MB"
    )

uploaded_file = st.file_uploader(_("file_uploader_label"), type=["pdf"])

if st.button(_("btn_analyze"), type="primary", use_container_width=True):
    target_path = ""

    if uploaded_file is not None:
        temp_path = f"_uploaded_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        target_path = temp_path
        source = f"上传文件：{uploaded_file.name}"
    elif last_pdf and os.path.exists(last_pdf):
        target_path = last_pdf
        source = f"上次下载：{last_name}"
    else:
        st.warning(_("warn_no_data"))
        st.stop()

    result = analyze_pdf(target_path)

    if "error" in result:
        st.error(result["error"])
    else:
        size_mb = result["file_size"] / (1024 * 1024)
        st.success(_("success_analysis"))

        col1, col2, col3 = st.columns(3)
        col1.metric(_("col_pages"), f'{result["pages"]} {_("unit_page")}')
        col2.metric(_("col_file"), result["file_name"])
        col3.metric(_("col_size"), f"{size_mb:.2f} MB")

    if uploaded_file is not None and os.path.exists(temp_path):
        os.remove(temp_path)
