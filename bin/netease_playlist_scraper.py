#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐个人歌单抓取脚本
从歌单页面抓取所有歌曲信息（歌名、歌手、专辑、时长等）
"""

import json
import os
import re
import time
import requests
from urllib.parse import urlparse, parse_qs


def _sanitize_creator_for_filename(creator: str, max_len: int = 80) -> str:
    """将创建者名称整理为合法文件名（去掉 Windows 非法字符）。"""
    s = (creator or "").strip()
    for c in '\\/:*?"<>|':
        s = s.replace(c, "_")
    s = s.strip(" .") or "未命名"
    return s[:max_len] if len(s) > max_len else s


def _resolve_csv_path(csv_arg: str, creator: str, script_dir: str) -> str:
    """若 -t 传入的是目录，则输出路径为 目录/创建者的歌单信息.csv。"""
    if not csv_arg:
        return ""
    # Windows 批处理传 "%OUTDIR%" 时若路径以 \ 结尾，闭合引号会变成路径一部分，需去掉
    csv_arg = csv_arg.strip().rstrip('"').rstrip("/\\").strip() or csv_arg.strip()
    if not csv_arg:
        return ""
    p = csv_arg.rstrip("/\\")
    if not p:
        return ""
    is_dir = csv_arg.rstrip("/\\") != csv_arg or (os.path.exists(csv_arg) and os.path.isdir(csv_arg))
    if is_dir:
        base_dir = csv_arg.rstrip("/\\")
        if not base_dir:
            base_dir = script_dir
        name = _sanitize_creator_for_filename(creator) + "的歌单信息.csv"
        return os.path.join(base_dir, name)
    return csv_arg


# 默认 Cookie（可能已过期）；可通过环境变量 NETEASE_COOKIE 覆盖为最新复制的 Cookie
DEFAULT_COOKIE = "_iuqxldmzr_=32; _ntes_nnid=0588459b00ee982b4cc6dae837ab090d,1773036660269; _ntes_nuid=0588459b00ee982b4cc6dae837ab090d; Hm_lvt_1483fb4774c02a30ffa6f0e2945e9b70=1773036660; HMACCOUNT=6F484AFF2700AF37; NMTID=00OKd-He31vlKTX905IiZaZyBKbnWMAAAGc0Thlmw; WEVNSM=1.0.0; WNMCID=skvulw.1773036661404.01.0; WM_NI=DmU53szej4fcvGLgl8PXj69pPKHDrRy7HWq%2F5bky9yJrU3jezeOJ0NgkZlQsJLoIjmNoRAYK0k0WI4%2FWBbhBthg4tUE2KbvRmD8s5%2F92mVhpp0pRpZwkIFGG8lpkgWmjRTc%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6ee91c6489c8ca7b8bc33868a8ea6c84a868a9fadd634899798b8f74fb1ad8589b12af0fea7c3b92a88b39bd6b279babba6d5e569b6998488ef349488a6d7bc7c949588a5f15abbe988b8f425f7bea59abc738aae9bd4e96fbabb81abb346a5b5968dd4798a94a1aae9678eb19ea2dc41f4b500b8cc40ed898e83eb4ab8b8a9d5f75f87ee8583f55aaf9cf894b825fbeea3b7eb7cb4f0c0b3f352b5b587a7c64dfcb4c08ce65dafb69eb5e237e2a3; WM_TID=2nl9t%2FxrN01BAFRQQVbD5PYGH5R4of1y; sDeviceId=YD-Og3gg%2BQddZxFQkEBQVfW4eZGWpEs%2BWiF; ntes_utid=tid._.%252FbTn0IX0mmdFVkUVURbCofZHG8B9%252FRyc._.0; __snaker__id=Syf6XMHtA6f0gX29; gdxidpyhxdE=%5C16Glqgp3zyha52%2BaIIrInQ73XCBWcM8hC4CCsIuWy3Xx48GiCaxbOQ4B9xwxX%2FyKyGzDqAlh%2F8mlD7uyWI8OTuRDzG62C7yQ506iwfXn1Tb54nNVBym5Y86c5%2BMwi9md8uwN9fYa%5CHl2U0mWrrizEIdYz6qfGmIeoK3Cy2Du%2BNGgNLk%3A1773038459996; JSESSIONID-WYYY=K%2BslHokGWcKEzvW%2Faf12PbBkYSG%2BGHZbVOS4rNSf%2FeibYYagep0OKW%2BrpeCT6SAclvMFnUzGR2eyE7VEKlRJhKFgpIBTNG4cRoKJCI11D07%2FONeJ2h4DXJug%2BNnFxadkZ6OM1ce4oec6AczK%5CEIKlU2U%5CRNjq0zqtsf3%5CWwbKM8wnAMu%3A1773040201172; Hm_lpvt_1483fb4774c02a30ffa6f0e2945e9b70=1773038714"

def _get_cookie() -> str:
    """优先使用环境变量 NETEASE_COOKIE，否则使用脚本内 DEFAULT_COOKIE。"""
    return (os.environ.get("NETEASE_COOKIE") or DEFAULT_COOKIE).strip()


def _get_base_url() -> str:
    """优先使用环境变量 NETEASE_API_BASE（如本地 NeteaseCloudMusicApi），否则官方域名。"""
    return (os.environ.get("NETEASE_API_BASE") or "https://music.163.com").rstrip("/")


def _is_local_api() -> bool:
    base = _get_base_url().lower()
    return "127.0.0.1" in base or "localhost" in base


def _api_path(subpath: str) -> str:
    """官方接口带 /api 前缀，本地 NeteaseCloudMusicApi 不带。"""
    if _is_local_api():
        return f"/{subpath.lstrip('/')}"
    return f"/api/{subpath.lstrip('/')}"


# 请求头：网易云会校验 Referer/Origin；Cookie 可从环境变量 NETEASE_COOKIE 覆盖
def _build_headers() -> dict:
    h = {
        "Referer": "https://music.163.com/",
        "Origin": "https://music.163.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    cookie = _get_cookie()
    if cookie:
        h["Cookie"] = cookie
    return h


# 单次 song/detail 请求的 id 数量上限，避免 URL 过长
SONG_DETAIL_BATCH = 100


def extract_playlist_id(url_or_id: str) -> str:
    """
    从歌单链接或直接传入的 ID 中提取歌单 ID。
    支持格式：
    - https://music.163.com/playlist?id=123456
    - https://music.163.com/#/playlist?id=123456&userid=xxx&creatorId=xxx（仅用 id 参数，其余忽略）
    - 123456
    """
    s = url_or_id.strip().lstrip("\ufeff")  # 去掉 BOM
    if s.isdigit():
        return s
    parsed = urlparse(s)
    # 处理 # 在 path 里的情况
    path = parsed.path or parsed.fragment or ""
    if "?" in path:
        path, query = path.split("?", 1)
    else:
        query = parsed.query
    params = parse_qs(query)
    pid = params.get("id", [None])[0]
    if pid and str(pid).isdigit():
        return str(pid)
    # 兜底：从整段字符串里匹配 id=数字
    m = re.search(r"[?&]id=(\d+)", s)
    if m:
        return m.group(1)
    raise ValueError(f"无法从输入中解析歌单 ID: {url_or_id}")


def fetch_playlist_detail(playlist_id: str) -> dict:
    """请求歌单详情接口，返回原始 JSON。"""
    base = _get_base_url()
    url = f"{base}{_api_path('playlist/detail')}"
    params = {"id": playlist_id}
    headers = _build_headers()
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    code = data.get("code")
    if code != 200:
        msg = data.get("msg") or data.get("message") or str(data)
        if code == 20001:
            raise RuntimeError(
                "歌单接口返回 20001（请求被限制）。\n"
                "方案一：先打开 https://music.163.com 登录，F12 → Network → 复制 Cookie，执行 set NETEASE_COOKIE=你复制的Cookie 再运行。\n"
                "方案二（推荐）：使用本地 API 代理。安装 Node.js 后，在终端执行： npx NeteaseCloudMusicApi@latest\n"
                "  另开终端执行： set NETEASE_API_BASE=http://127.0.0.1:3000  再运行本脚本。"
            )
        raise RuntimeError(f"歌单接口返回错误: code={code}, msg={msg}")
    return data


def fetch_song_details(song_ids: list[int]) -> list[dict]:
    """根据歌曲 ID 列表请求歌曲详情，返回歌曲信息列表。"""
    if not song_ids:
        return []
    headers = _build_headers()
    all_songs = []
    for i in range(0, len(song_ids), SONG_DETAIL_BATCH):
        batch = song_ids[i : i + SONG_DETAIL_BATCH]
        ids_str = ",".join(str(x) for x in batch)
        url = f"{_get_base_url()}{_api_path('song/detail')}"
        params = {"ids": f"[{ids_str}]"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"歌曲详情接口返回错误: {data.get('message', data)}")
        songs = data.get("songs") or []
        all_songs.extend(songs)
        time.sleep(0.2)  # 适当限速，避免请求过快
    return all_songs


def parse_track(raw: dict) -> dict:
    """将接口返回的单曲对象解析为统一的歌曲信息字典。"""
    name = raw.get("name", "")
    sid = raw.get("id", 0)
    # 歌手 ar: [ { id, name } ]
    ar = raw.get("ar") or []
    artists = ", ".join(a.get("name", "") for a in ar if a.get("name"))
    # 专辑 al: { id, name, picUrl }
    al = raw.get("al") or {}
    album = al.get("name", "")
    album_id = al.get("id", 0)
    # 时长 dt，单位毫秒
    dt_ms = raw.get("dt", 0) or 0
    duration_sec = dt_ms // 1000
    duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
    return {
        "id": sid,
        "name": name,
        "artists": artists,
        "album": album,
        "album_id": album_id,
        "duration_ms": dt_ms,
        "duration": duration_str,
    }


def get_playlist_songs(playlist_id: str) -> tuple[dict, list[dict]]:
    """
    获取歌单基本信息与全部歌曲列表。
    返回 (歌单信息, 歌曲信息列表)。
    """
    data = fetch_playlist_detail(playlist_id)
    playlist = data.get("playlist") or {}
    track_ids = [t["id"] for t in (playlist.get("trackIds") or [])]
    tracks_from_playlist = playlist.get("tracks") or []

    # 若 trackIds 数量大于当前 tracks 数量，说明未返回完整列表，用 song/detail 补全
    have_ids = {t.get("id") for t in tracks_from_playlist if t.get("id")}
    if len(track_ids) > len(tracks_from_playlist):
        need_ids = [i for i in track_ids if i not in have_ids]
        if need_ids:
            extra_songs = fetch_song_details(need_ids)
            for s in extra_songs:
                if s.get("id") not in have_ids:
                    tracks_from_playlist.append(s)
                    have_ids.add(s.get("id"))

    # 按 trackIds 顺序排列
    id_to_track = {t.get("id"): t for t in tracks_from_playlist if t.get("id")}
    ordered_tracks = []
    for tid in track_ids:
        if tid in id_to_track:
            ordered_tracks.append(id_to_track[tid])

    playlist_info = {
        "id": playlist.get("id"),
        "name": playlist.get("name"),
        "description": playlist.get("description"),
        "track_count": playlist.get("trackCount", 0),
        "creator": (playlist.get("creator") or {}).get("nickname", ""),
    }
    song_list = [parse_track(t) for t in ordered_tracks]
    return playlist_info, song_list


def main():
    import argparse

    parser = argparse.ArgumentParser(description="抓取网易云音乐歌单中的全部歌曲信息")
    parser.add_argument(
        "playlist",
        type=str,
        help="歌单链接、歌单 ID，或存有链接的文本文件路径（如 歌单链接.txt）",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出 JSON 文件路径；不指定则只打印到控制台",
    )
    parser.add_argument(
        "-t", "--csv",
        type=str,
        default=None,
        help="同时导出为 CSV 文件路径（仅歌曲列表）",
    )
    args = parser.parse_args()

    # 若传入的是文件路径，则从文件第一行读取歌单链接（utf-8-sig 自动去掉 BOM）
    playlist_input = args.playlist.strip().lstrip("\ufeff")
    link_file = playlist_input
    if not os.path.isabs(link_file) and not os.path.isfile(link_file):
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir and os.path.isfile(os.path.join(_dir, link_file)):
            link_file = os.path.join(_dir, link_file)
    if os.path.isfile(link_file):
        with open(link_file, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip().lstrip("\ufeff")
                if not line:
                    continue
                if not line.startswith("#"):
                    if "music.163.com" in line:
                        playlist_input = line
                    continue
                # 注释行：只认含 music.163.com 的链接；取最后一个匹配，避免用模板里的示例
                m = re.search(r"https?://[^\s\)\]\"\']*music\.163\.com[^\s\)\]\"\']*", line)
                if m:
                    playlist_input = m.group(0).rstrip(".,;:")
        if playlist_input == link_file or (not playlist_input.strip()):
            raise ValueError("歌单链接.txt 中未找到有效链接，请粘贴网易云歌单完整链接（如 https://music.163.com/#/playlist?id=xxx）")

    playlist_id = extract_playlist_id(playlist_input)
    print(f"歌单 ID: {playlist_id}")
    print("正在获取歌单与歌曲信息...")

    playlist_info, songs = get_playlist_songs(playlist_id)
    print(f"\n歌单: {playlist_info['name']}")
    print(f"创建者: {playlist_info['creator']}")
    print(f"歌曲数量: {len(songs)}")

    result = {"playlist": playlist_info, "songs": songs}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"已保存 JSON: {args.output}")

    if args.csv and songs:
        import csv
        script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
        csv_arg = (args.csv or "").strip().rstrip('"').rstrip("/\\")
        csv_path = _resolve_csv_path(csv_arg, playlist_info.get("creator", ""), script_dir)
        if not csv_path:
            csv_path = csv_arg
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "artists", "album", "duration"])
            w.writeheader()
            w.writerows([{k: s.get(k, "") for k in ["id", "name", "artists", "album", "duration"]} for s in songs])
        print(f"已保存 CSV: {csv_path}")
        try:
            marker = os.path.join(os.path.dirname(csv_path), "last_export_path.txt")
            with open(marker, "w", encoding="utf-8") as m:
                m.write(csv_path)
        except Exception:
            pass

    if not args.output and not args.csv:
        print("\n--- 歌曲列表 ---")
        for i, s in enumerate(songs, 1):
            print(f"{i}. {s['name']} - {s['artists']} | {s['album']} | {s['duration']}")

    return result


if __name__ == "__main__":
    main()
