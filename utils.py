import base64
import gzip
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import streamlit as st
from PIL import Image

from i18n import _

# --- 云展网下载核心 (原 download_yunzhan_pdf.py) ---

DESTRING_URL = "https://book.yunzhan365.com/resourceFiles/html5_templates/js/deString.js"
USER_AGENT = "Mozilla/5.0"

def fetch_text(url: str, referer: str | None = None) -> str:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        data = response.read()
        if data.startswith(b"\x1f\x8b"):
            data = gzip.decompress(data)
        return data.decode("utf-8", errors="replace")

def fetch_bytes(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    with urlopen(request, timeout=60) as response:
        return response.read()

def normalize_book_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    if url.endswith("/"):
        return urljoin(url, "mobile/index.html")
    if "/mobile/" not in url and not url.endswith("index.html"):
        return urljoin(url + "/", "mobile/index.html")
    return url

def load_html_config(book_url: str) -> tuple[dict, str | None]:
    html = fetch_text(book_url)
    title_match = re.search(r"<title>\s*(.*?)\s*</title>", html, re.S | re.I)
    html_title = title_match.group(1).strip() if title_match else None
    match = re.search(r'<script[^>]+src=["\']([^"\']*javascript/config\.js[^"\']*)', html)
    if not match:
        raise RuntimeError("没有在页面中找到 javascript/config.js")
    config_url = urljoin(book_url, match.group(1))
    config_js = fetch_text(config_url, referer=book_url)
    match = re.search(r"var\s+htmlConfig\s*=\s*(\{.*\})\s*;\s*$", config_js, re.S)
    if not match:
        raise RuntimeError("config.js 中没有找到 htmlConfig")
    return json.loads(match.group(1)), html_title

def patch_destring_js(source: str) -> str:
    source = source.replace("\r\n", "\n")
    needle = "read_ = (filename, binary) => {\n"
    patch = (
        "read_ = (filename, binary) => {\n"
        "  if (isDataURI(filename)) {\n"
        "    var data = Buffer.from(filename.slice(dataURIPrefix.length), 'base64');\n"
        "    return binary ? data : data.toString('utf8');\n"
        "  }\n"
    )
    if patch in source:
        return source
    if needle not in source:
        raise RuntimeError("无法补丁 deString.js")
    return source.replace(needle, patch, 1)

def decode_configs(html_config: dict) -> tuple[dict, list[dict]]:
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        raise RuntimeError("需要本机安装 Node.js，用来执行云展网的配置解码脚本")
    encrypted = {
        "bookConfig": html_config["bookConfig"],
        "fliphtml5_pages": html_config["fliphtml5_pages"],
    }
    with tempfile.TemporaryDirectory(prefix="yunzhan_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        (temp_dir / "encrypted.json").write_text(json.dumps(encrypted), encoding="utf-8")
        destring_js = patch_destring_js(fetch_text(DESTRING_URL))
        (temp_dir / "deString.js").write_text(destring_js, encoding="utf-8")
        (temp_dir / "decode.js").write_text(
            r"""
const fs = require("fs");
const encrypted = JSON.parse(fs.readFileSync("encrypted.json", "utf8"));
const Module = require("./deString.js");

function toCString(str) {
  const bytes = new TextEncoder().encode(str + "\0");
  const ptr = Module._malloc(bytes.length);
  Module.HEAPU8.set(bytes, ptr);
  return ptr;
}

function fromCString(ptr) {
  const bytes = [];
  for (let i = ptr; Module.HEAPU8[i] !== 0; i++) bytes.push(Module.HEAPU8[i]);
  return new TextDecoder("utf8").decode(new Uint8Array(bytes));
}

function deString(value) {
  const input = toCString(value);
  const output = Module._DeString(input);
  const decoded = fromCString(output);
  Module._free(input);
  if (Module._FreeMemory) Module._FreeMemory(output);
  return decoded;
}

function run() {
  const decoded = {
    bookConfig: deString(encrypted.bookConfig),
    pages: deString(encrypted.fliphtml5_pages),
  };
  fs.writeFileSync("decoded.json", JSON.stringify(decoded), "utf8");
}

if (Module.isReady) run();
else Module.onRuntimeInitialized = run;
""",
            encoding="utf-8",
        )
        subprocess.run(
            [node, "decode.js"],
            cwd=temp_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        decoded = json.loads((temp_dir / "decoded.json").read_text(encoding="utf-8"))
    book_config, _ = json.JSONDecoder().raw_decode(decoded["bookConfig"])
    pages, _ = json.JSONDecoder().raw_decode(decoded["pages"])
    return book_config, pages

def safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "yunzhan_book"

def page_urls(book_url: str, book_config: dict, pages: list[dict]) -> list[str]:
    paths = book_config.get("largePath") or book_config.get("normalPath") or ["../files/large/"]
    large_path = paths[0] if isinstance(paths, list) else paths
    root_url = book_url.split("/mobile/", 1)[0] + "/"
    base_url = urljoin(book_url if str(large_path).startswith(("../", "/", "http")) else root_url, large_path)
    urls = []
    for page in pages:
        name = page.get("n")
        if isinstance(name, list) and name:
            urls.append(urljoin(base_url, name[0]))
            continue
        if isinstance(name, str) and name and name != "none":
            urls.append(urljoin(base_url, name))
            continue
        page_path = page.get("p")
        if isinstance(page_path, str) and page_path and page_path != "none":
            urls.append(urljoin(book_url, page_path))
            continue
        thumb_path = page.get("t")
        if isinstance(thumb_path, str) and thumb_path and thumb_path != "none":
            urls.append(urljoin(book_url, thumb_path))
    return urls

def download_pages(
    urls: list[str],
    pages_dir: Path,
    referer: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[Path]:
    pages_dir.mkdir(parents=True, exist_ok=True)
    page_paths = []
    for index, url in enumerate(urls, start=1):
        suffix = Path(url.split("?", 1)[0]).suffix or ".webp"
        page_path = pages_dir / f"{index:03d}{suffix}"
        page_paths.append(page_path)
        if page_path.exists() and page_path.stat().st_size > 0:
            if progress_callback:
                progress_callback(index, len(urls), f"[skip] 第 {index:03d} 页 (已存在)")
            continue
        page_path.write_bytes(fetch_bytes(url, referer=referer))
        if progress_callback:
            progress_callback(index, len(urls), f"[download] 第 {index:03d}/{len(urls)} 页")
    return page_paths

def build_pdf(page_paths: list[Path], output: Path) -> None:
    images: list[Image.Image] = []
    try:
        for page_path in page_paths:
            with Image.open(page_path) as image:
                images.append(image.convert("RGB"))
        if not images:
            raise RuntimeError("没有可用于合成 PDF 的页面")
        images[0].save(output, "PDF", save_all=True, append_images=images[1:], resolution=100.0)
    finally:
        for image in images:
            image.close()

# --- UI 工具函数 (原 streamlit_app.py) ---

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
    settings = load_settings()
    defaults = {
        "lang": "zh",
        "target_input": settings.get("target_input", ""),
        "last_result_text": "",
        "last_result_name": "",
        "last_pdf_path": "",
        "last_page_count": 0,
        "last_book_title": "",
        "env_ready": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- 下载完整流程（供 UI 页面调用） ---

def run_download_pipeline(
    url: str,
    status_holder,
    log_placeholder,
    progress_bar,
) -> tuple[int, str, str, int]:
    try:
        book_url = normalize_book_url(url)
        status_holder.info(_("info_parsing"))
        log_placeholder.code("[INFO] 正在解析页面配置...\n", language="bash")
        html_config, html_title = load_html_config(book_url)

        status_holder.info(_("info_decoding"))
        log_placeholder.code("[INFO] 页面解析完成\n[INFO] 正在解码书籍配置 (Node.js)...\n", language="bash")
        book_config, pages = decode_configs(html_config)

        title = (
            html_title
            or html_config.get("meta", {}).get("title")
            or book_config.get("bookTitle")
            or book_config.get("Title")
            or "yunzhan_book"
        )
        stem = safe_name(title)
        output = Path(f"{stem}.pdf")
        pages_dir = Path(f"{stem}_pages")
        urls = page_urls(book_url, book_config, pages)

        current_log = f"[INFO] 页面解析完成\n[INFO] 解码完成\n[INFO] 找到 {len(urls)} 页\n"
        log_placeholder.code(current_log, language="bash")

        status_holder.info(_("info_downloading").format(total=len(urls)))
        progress_bar.progress(0)

        def on_progress(index, total, msg):
            nonlocal current_log
            current_log += msg + "\n"
            log_placeholder.code(current_log, language="bash")
            progress_bar.progress(index / total)

        page_paths = download_pages(urls, pages_dir, book_url, progress_callback=on_progress)

        status_holder.info(_("info_building_pdf"))
        current_log += "[INFO] 正在生成 PDF...\n"
        log_placeholder.code(current_log, language="bash")
        build_pdf(page_paths, output)

        shutil.rmtree(pages_dir, ignore_errors=True)

        st.session_state["last_pdf_path"] = str(output.resolve())
        st.session_state["last_page_count"] = len(page_paths)
        st.session_state["last_book_title"] = title
        st.session_state["last_result_name"] = output.name
        st.session_state["last_result_text"] = f"书籍: {title}\n页数: {len(page_paths)} 页\n文件: {output.name}"

        current_log += "[SUCCESS] PDF 生成完成！\n"
        log_placeholder.code(current_log, language="bash")
        status_holder.success(_("success_exec"))

        return 0, "SUCCESS", str(output.resolve()), len(page_paths)

    except Exception as e:
        status_holder.error(f"执行失败: {e}")
        return -1, str(e), "", 0

# --- 分析函数 ---

def analyze_pdf(pdf_path: str) -> dict:
    path = Path(pdf_path)
    if not path.exists():
        return {"error": "文件不存在"}
    try:
        from PIL import Image
        with Image.open(pdf_path) as pdf:
            pages = getattr(pdf, "n_frames", 1)
        file_size = path.stat().st_size
        return {
            "pages": pages,
            "file_size": file_size,
            "file_name": path.name,
        }
    except Exception as e:
        return {"error": str(e)}
