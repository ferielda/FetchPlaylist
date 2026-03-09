# 网易云 / QQ 音乐歌单导出

从网易云音乐或 QQ 音乐个人歌单抓取全部歌曲信息（歌名、歌手、专辑、时长等），导出为 CSV。

## 文件夹说明

- **根目录**：只保留常用入口与链接文件  
  - `playlist_link_qq.txt`：QQ 音乐歌单链接（粘贴后运行「导出歌单_QQ.bat」）  
  - `playlist_link_netease.txt`：网易云歌单链接（粘贴后运行「导出歌单_网易云.bat」）  
  - `导出歌单_QQ.bat` / `导出歌单_网易云.bat`：导出对应平台歌单  
  - `启动QQ音乐API.bat` / `启动网易云API.bat`：启动本地 API 服务（导出前需先运行）  
  - `README.md`：本说明  
- **bin/**：脚本与依赖  
  - `qq_playlist_scraper.py`、`netease_playlist_scraper.py`：抓取脚本  
  - `export_playlist_qq.bat`、`export_playlist_netease.bat`：导出逻辑（由根目录 bat 调用）  
  - `QQMusicApi/`：QQ 音乐本地 API 项目  
  - `requirements.txt`：Python 依赖（`pip install -r bin/requirements.txt`）

## 快速使用

1. **网易云**：把歌单链接写入 `playlist_link_netease.txt` → 先双击 `启动网易云API.bat`，再双击 `导出歌单_网易云.bat`。  
2. **QQ 音乐**：把歌单链接写入 `playlist_link_qq.txt` → 先双击 `启动QQ音乐API.bat`，再双击 `导出歌单_QQ.bat`。  
3. 导出的 CSV 在根目录，文件名为「创建者的歌单信息.csv」。

---

# 网易云音乐歌单抓取（脚本说明）

从网易云音乐个人歌单页面抓取全部歌曲信息（歌名、歌手、专辑、时长等）。

## 方式一：使用本地 API 代理（推荐，避免 20001）

官方直连常被风控返回 20001，建议用 [NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi) 在本地起一个代理。**无需 git clone**，用 npx 即可。

### 1. 安装 Node.js 并启动本地 API

- 若未安装，请先安装 [Node.js](https://nodejs.org/)（建议 18+）。
- 在任意目录打开终端，执行：

```bash
npx NeteaseCloudMusicApi@latest
```

首次运行会自动下载依赖，看到类似 `server running @ http://localhost:3000` 即表示已启动，**保持该窗口不关闭**。

### 2. 指定本地 API 并运行脚本

**另开一个终端**，在项目目录下执行（脚本在 `bin` 目录）：

**Windows CMD：**
```cmd
set NETEASE_API_BASE=http://127.0.0.1:3000
python bin\netease_playlist_scraper.py 931794508
```

**Windows PowerShell：**
```powershell
$env:NETEASE_API_BASE="http://127.0.0.1:3000"
python bin\netease_playlist_scraper.py 931794508
```

**Linux / macOS：**
```bash
export NETEASE_API_BASE=http://127.0.0.1:3000
python bin/netease_playlist_scraper.py 931794508
```

之后每次抓取前，只要先启动 NeteaseCloudMusicApi，再设置 `NETEASE_API_BASE` 并运行脚本即可。

---

## 方式二：直连官方（需有效 Cookie，易被 20001）

在浏览器登录 [网易云音乐](https://music.163.com)，F12 → Network → 任选请求 → Request Headers 里复制整段 **Cookie**，然后：

```cmd
set NETEASE_COOKIE=你复制的Cookie
python bin\netease_playlist_scraper.py 歌单ID或链接
```

Cookie 过期或风控时可能仍返回 20001，此时建议改用方式一。

---

## 安装依赖与常用命令

```bash
pip install -r bin/requirements.txt
```

```bash
# 只打印到控制台
python bin\netease_playlist_scraper.py 931794508

# 保存为 JSON
python bin\netease_playlist_scraper.py 931794508 -o 歌单.json

# 同时导出 CSV
python bin\netease_playlist_scraper.py 931794508 -o 歌单.json -t 歌曲.csv
```

## 环境变量说明

| 变量 | 说明 |
|------|------|
| `NETEASE_API_BASE` | 设为 `http://127.0.0.1:3000` 时使用本地 NeteaseCloudMusicApi，避免直连 20001 |
| `NETEASE_COOKIE` | 可选，覆盖脚本内默认 Cookie（直连时用） |
