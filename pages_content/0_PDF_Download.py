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
    disabled=True,
)

save_settings(st.session_state["target_input"])

st.button(_("btn_run"), type="primary", use_container_width=True, disabled=True)
st.caption("本功能已暂停，如需使用请 clone 代码本地部署")
