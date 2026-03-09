# FetchPlaylist

**FetchPlaylist** 是一个高效、简洁的歌单导出工具，能够将你喜爱的网易云音乐和 QQ 音乐歌单导出为 CSV 格式，方便备份与管理。

## 功能特点

* **多平台支持**：同时支持网易云音乐与 QQ 音乐。
* **导出格式**：统一导出为 CSV 文件，兼容 Excel 与主流数据分析工具。
* **本地化 API**：集成本地 API 服务，确保数据抓取的稳定性与隐私安全。
* **一键运行**：针对 Windows 用户优化，支持直接双击 `.bat` 文件运行，无需频繁操作命令行。

## 环境要求

在使用前，请确保你的系统已安装以下环境：

| 环境 | 版本要求 | 用途 |
| --- | --- | --- |
| Python | 3.8+ | 运行数据导出脚本 |
| Node.js | 18+ | 运行音乐 API 服务 |
| Git | 2.0+ | 用于下载及更新 API 模块 |

## 下载项目

你可以通过以下两种方式获取本项目：

1. **使用 Git 克隆**：
```bash
git clone https://github.com/ferielda/FetchPlaylist.git

```


2. **下载 ZIP 包**：
点击 GitHub 页面右上角的 `<> Code` 按钮，选择 `Download ZIP`，解压到本地即可。

## 安装步骤

1. **安装 Python 依赖**：
在终端或 CMD 中进入项目根目录，运行：
```bash
pip install -r bin/requirements.txt

```


2. **配置 API 环境**：
* **网易云**：本项目采用 `npx` 自动拉取 API，无需手动部署。
* **QQ 音乐**：首次使用时，请进入 `bin/QQMusicApi` 目录执行 `npm install` 以安装必要的依赖。



## 使用方法

### 1. 导出网易云歌单

1. 启动 API 服务（双击运行启动脚本）。
2. 打开 `playlist_link_netease.txt`，将歌单链接粘贴进去（程序会自动获取链接中最后一个有效 ID）。
3. 双击运行 `导出歌单_网易云.bat`，生成的 CSV 文件将保存在当前目录下。

### 2. 导出 QQ 音乐歌单

1. 启动 QQ 音乐 API 服务。
2. 打开 `playlist_link_qq.txt`，粘贴歌单链接。
3. 双击运行 `导出歌单_QQ.bat` 即可导出。

> **提示**：若文本文件中包含多个链接，程序默认提取最后一行链接进行处理。

## 项目结构

```text
FetchPlaylist/
├── bin/
│   ├── QQMusicApi/       # QQ 音乐核心 API
│   └── requirements.txt  # Python 依赖清单
├── 导出歌单_网易云.bat    # Windows 运行入口
├── 导出歌单_QQ.bat       # Windows 运行入口
├── playlist_link_netease.txt # 歌单链接配置
├── playlist_link_qq.txt      # 歌单链接配置
└── README.md

```

## 常见问题 (FAQ)

* **Q: 程序闪退怎么办？**
A: 请检查是否安装了 Node.js 18+，并确认 `bin/` 目录下的相关 API 服务是否已成功启动。
* **Q: 导出后没有 CSV 文件？**
A: 请检查链接格式是否正确，并查看黑框（命令行）中是否有报错提示。
* **Q: Linux 或 macOS 用户如何使用？**
A: 由于 `.bat` 文件仅限 Windows，请直接在终端执行 Python 命令：`python export_netease.py`。

## 致谢与许可证

* 本项目使用了 [NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi) 和 [QQMusicApi](https://github.com/jsososo/QQMusicApi) 等开源组件。
* 本工具仅供个人学习与研究使用，请勿用于商业用途或大规模抓取数据。

---
