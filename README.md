# 悟空云展网下载器

这是一个云展网（yunzhan365.com）电子书下载工具，支持一键导出为 PDF，并进行基础数据分析。

![](https://asiaassets.gokuscraper.com/images/2026/05/29/94b08118491a0019.webp)

## 核心优势

- 免登录免配置，输入链接即可下载
- 自动抓取所有页面并合成为 PDF
- 下载过程实时显示进度日志
- 支持 CLI 命令行和 Web 界面两种方式

---

## 在线使用

[https://yunzhan.streamlit.app/](https://yunzhan.streamlit.app/)

## 功能概览

### 0PDF下载

- 输入云展网书籍链接
- 自动解析页面配置，通过 Node.js 解码加密信息
- 页面实时显示下载进度日志
- 下载完成后提供 PDF 下载
- 下载结束后自动清理临时图片目录

### 1数据分析

- 支持两种输入来源：
  1. 最近一次下载的 PDF（自动缓存）
  2. 上传 PDF 文件
- 统计指标：总页数、文件名、文件大小

---

## 运行方式

### 方式一：直接启动 Streamlit

```bash
streamlit run streamlit_app.py
```

### 方式二：命令行下载

```bash
python download_yunzhan_pdf.py https://book.yunzhan365.com/xxxxxx
```

默认地址：<http://localhost:8501>

---

## 环境要求

- Python 3.10+
- Node.js（用于解码）
- Pillow（图片处理）

安装依赖：

```bash
pip install streamlit pillow
```

---

## 目录与关键文件

- `streamlit_app.py`：主界面与业务逻辑
- `download_yunzhan_pdf.py`：命令行下载入口
- `utils.py`：核心工具函数库（解析、解码、下载、合成 PDF）
- `i18n.py`：国际化模块
- `locales/`：语言包（中文/英文）
- `framework_settings.json`：页面输入配置缓存
- `pages/0_PDF_Download.py`：PDF 下载页面
- `pages/1_Data_Analysis.py`：数据分析页面

---

## 使用说明

1. 打开页面后进入 `PDF下载`
2. 填入云展网书籍链接，点击"开始执行任务"
3. 等待下载完成，点击下载 PDF
4. 切换到 `数据分析`
   - 可直接点"开始分析"（自动用最近下载的 PDF）
   - 或上传 PDF 再分析

---

## 公众号和交流群

![交流群](https://asiaassets.gokuscraper.com/%E6%82%9F%E7%A9%BA%E7%88%AC%E8%99%AB%E5%85%AC%E4%BC%97%E5%8F%B7.jpg)

## 官方网站

https://gokuscraper.com

在线体验工具，或了解更多数据分析能力。

如有定制化数据分析或工具需求，欢迎交流。

---

## 常见问题

### 1) 提示找不到 Node.js

应用需要 Node.js 来解码云展网的加密书籍配置。请确保已安装 Node.js（>= 16）并添加到系统 PATH。

### 2) 下载的 PDF 无法打开

请确认链接有效且书籍可公开访问。部分加密或需要登录的书籍可能无法下载。

### 3) 为什么分析结果只有页数

当前分析功能主要统计 PDF 的基本信息（页数、文件大小、文件名），后续版本会扩展更多分析维度。

---

## 备注

本工具基于云展网公开数据结构进行解析和下载，重点是"简单可用、可视化、可下载、可分析"。

## 免责声明

本项目为数据分析与可视化工具，仅处理公开数据用于研究分析。

本项目与云展网平台无关联或授权关系。

禁止用于任何违法或侵犯他人权益的用途，使用者需自行承担全部责任。
