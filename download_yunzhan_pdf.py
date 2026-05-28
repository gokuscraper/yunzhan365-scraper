import argparse
import shutil
from pathlib import Path

from utils import (
    normalize_book_url,
    load_html_config,
    decode_configs,
    safe_name,
    page_urls,
    download_pages,
    build_pdf,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a yunzhan365 book as PDF.")
    parser.add_argument("url", nargs="?", help="云展网书籍链接")
    parser.add_argument("-o", "--output", help="输出 PDF 文件名")
    parser.add_argument("--keep-pages", action="store_true", help="保留下载的页面图片")
    args = parser.parse_args()

    book_url = normalize_book_url(args.url or input("请输入云展网链接: "))
    print(f"[page] {book_url}")

    html_config, html_title = load_html_config(book_url)
    book_config, pages = decode_configs(html_config)

    title = (
        html_title
        or html_config.get("meta", {}).get("title")
        or book_config.get("bookTitle")
        or book_config.get("Title")
        or "yunzhan_book"
    )
    stem = safe_name(title)
    output = Path(args.output or f"{stem}.pdf")
    pages_dir = Path(f"{stem}_pages")

    urls = page_urls(book_url, book_config, pages)
    print(f"[info] {stem}, {len(urls)} pages")
    page_paths = download_pages(urls, pages_dir, book_url)

    print(f"[pdf] {output}")
    build_pdf(page_paths, output)

    if not args.keep_pages:
        shutil.rmtree(pages_dir, ignore_errors=True)

    print("[done]")


if __name__ == "__main__":
    main()
