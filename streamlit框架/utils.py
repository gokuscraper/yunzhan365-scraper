import base64
import json
import mimetypes
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from i18n import _

# --- UI 工具函数 ---

SETTINGS_FILE = "framework_settings.json"


def resolve_asset_path(file_name: str) -> str:
    APP_DIR = Path(__file__).resolve().parent
    candidates = [APP_DIR / file_name, Path.cwd() / file_name]
    for p in candidates:
        if p.exists():
            return str(p)
    return file_name


def image_to_data_uri(path: str) -> str:
    try:
        file_path = Path(path)
        if not file_path.exists():
            return ""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "image/png"
        data = file_path.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return ""


def load_settings() -> dict[str, Any]:
    if not os.path.exists(SETTINGS_FILE):
        return {"target_input": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"target_input": ""}


def save_settings(target_input: str) -> None:
    data = {
        "target_input": target_input,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_state():
    _clean_stale_lock()
    settings = load_settings()
    defaults = {
        "lang": "zh",
        "target_input": settings.get("target_input", ""),
        "last_result_text": "",
        "last_result_name": "",
        "last_file_path": "",
        "last_result_count": 0,
        "last_result_title": "",
        "env_ready": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# --- 互斥锁（防止多人并发导致 OOM） ---

LOCK_FILE = Path.cwd() / ".run_lock"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _clean_stale_lock():
    if not LOCK_FILE.exists():
        return
    try:
        data = json.loads(LOCK_FILE.read_text())
        pid = data.get("pid")
        if pid is None or pid == os.getpid() or not _pid_alive(pid):
            LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        LOCK_FILE.unlink(missing_ok=True)


def _acquire_lock() -> bool:
    _clean_stale_lock()
    if LOCK_FILE.exists():
        try:
            data = json.loads(LOCK_FILE.read_text())
            elapsed = time.time() - data["time"]
            if elapsed < 300:
                return False
        except Exception:
            pass
        LOCK_FILE.unlink(missing_ok=True)
    LOCK_FILE.write_text(json.dumps({"time": time.time(), "pid": os.getpid()}))
    return True


def _release_lock():
    try:
        if LOCK_FILE.exists():
            data = json.loads(LOCK_FILE.read_text())
            if data.get("pid") == os.getpid():
                LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        LOCK_FILE.unlink(missing_ok=True)


# --- 业务管道（框架占位，填充你的采集逻辑） ---


def run_pipeline(
    url: str,
    status_holder,
    log_placeholder,
    progress_bar,
) -> tuple[int, str, str, int]:
    if not _acquire_lock():
        status_holder.error("当前有其他任务正在执行，请稍后再试")
        return -2, "BUSY", "", 0
    try:
        # TODO: 在这里实现你的采集管道
        # 示例用法：
        #   status_holder.info("开始采集...")
        #   log_placeholder.code("[INFO] 采集进度...", language="bash")
        #   progress_bar.progress(0.5)
        #   st.session_state["last_result_title"] = title
        #   st.session_state["last_file_path"] = str(output_path)
        #   st.session_state["last_result_count"] = count
        #   status_holder.success("采集完成")
        #   return 0, "SUCCESS", str(output_path), count
        status_holder.info(_("info_parsing"))
        return -1, "TODO", "", 0
    finally:
        _release_lock()


def analyze_result(file_path: str) -> dict:
    # TODO: 在这里实现你的分析逻辑
    # 示例：
    #   return {"pages": n, "file_size": size, "file_name": name}
    return {"error": "TODO"}
