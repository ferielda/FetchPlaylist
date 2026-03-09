#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ 音乐歌单抓取脚本
从歌单链接抓取全部歌曲信息并导出 CSV（与网易云脚本用法一致）
"""

import csv
import json
import os
import re
import requests


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
    # 传入的是目录：以路径分隔符结尾，或路径为已存在的目录
    is_dir = csv_arg.rstrip("/\\") != csv_arg or (os.path.exists(csv_arg) and os.path.isdir(csv_arg))
    if is_dir:
        base_dir = csv_arg.rstrip("/\\")
        if not base_dir:
            base_dir = script_dir
        name = _sanitize_creator_for_filename(creator) + "的歌单信息.csv"
        return os.path.join(base_dir, name)
    return csv_arg

# 默认使用公共 API；可设置环境变量 QQ_API_BASE=http://localhost:3300 使用本地 QQMusicApi
QQ_API_BASE = (os.environ.get("QQ_API_BASE") or "https://api.qq.jsososo.com").rstrip("/")


def extract_playlist_id(url_or_id: str) -> str:
    """
    从 QQ 音乐歌单链接或纯 ID 中提取歌单 ID。
    支持格式：
    - https://y.qq.com/n/yqq/playlist/7177076625.html
    - https://y.qq.com/musicmac/v6/playlist/detail.html?id=7177076625
    - https://i.y.qq.com/n2/m/share/details/taoge.html?id=7177076625
    - 7177076625
    """
    s = url_or_id.strip().lstrip("\ufeff")
    if s.isdigit():
        return s
    # 路径形式: .../playlist/数字 或 .../playlist/数字.html 或 .../playlist/数字?...
    m = re.search(r"/playlist/(\d+)(?:\.html|\?|/|$)", s)
    if m:
        return m.group(1)
    # 查询参数 id=数字
    m = re.search(r"[?&]id=(\d+)", s)
    if m:
        return m.group(1)
    raise ValueError(f"无法从输入中解析 QQ 歌单 ID: {url_or_id}")


def fetch_playlist(playlist_id: str) -> dict:
    """请求 QQ 音乐歌单详情接口。jsososo/QQMusicApi 歌单详情路由为 /songlist（非 /playlist）。"""
    url = f"{QQ_API_BASE.rstrip('/')}/songlist"
    params = {"id": playlist_id}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
    except requests.exceptions.SSLError:
        # 公共接口有时 SSL 握手异常，重试时跳过证书校验（仅用于读取歌单）
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
    resp.raise_for_status()
    data = resp.json()
    # 不同接口：result=100 或 code=0/200 为成功；有 data/songlist 也视为成功
    if data.get("code") not in (None, 0, 200) and data.get("result") not in (None, 100):
        if not (data.get("data") or data.get("songlist")):
            raise RuntimeError(f"QQ 歌单接口返回错误: {data}")
    return data


def parse_song(item: dict) -> dict:
    """将 API 返回的单曲项解析为统一字段。"""
    # 常见字段：songname / name, singer(数组或字符串), album, interval(秒)
    name = item.get("songname") or item.get("name") or item.get("title") or ""
    sid = item.get("songid") or item.get("song_id") or item.get("id") or 0
    singer = item.get("singer")
    if isinstance(singer, list):
        artists = " / ".join(s.get("name", s.get("title", "")) for s in singer if s)
    else:
        artists = str(singer) if singer else ""
    album = ""
    al = item.get("album") or item.get("albumname")
    if isinstance(al, dict):
        album = al.get("name") or al.get("title") or ""
    elif al:
        album = str(al)
    interval = item.get("interval") or item.get("song_time") or 0
    if isinstance(interval, (int, float)):
        sec = int(interval)
    else:
        # 如 "3:45" 或 "3分45秒"
        sec = 0
        if isinstance(interval, str):
            parts = re.findall(r"\d+", interval)
            if len(parts) >= 2:
                sec = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 1:
                sec = int(parts[0])
    duration = f"{sec // 60}:{sec % 60:02d}" if sec else "0:00"
    return {
        "id": sid,
        "name": name,
        "artists": artists,
        "album": album,
        "duration": duration,
    }


def get_playlist_songs(playlist_id: str) -> tuple[dict, list[dict]]:
    """获取歌单信息与歌曲列表。"""
    raw = fetch_playlist(playlist_id)
    # 兼容多种返回结构：data / detail / 顶层
    data = raw.get("data") or raw.get("detail") or raw
    songlist = (
        data.get("songlist")
        or data.get("songList")
        or data.get("song_list")
        or raw.get("songlist")
        or raw.get("songList")
        or []
    )
    # 歌单信息
    playlist_info = {
        "id": playlist_id,
        "name": data.get("dissname") or data.get("title") or data.get("name") or "",
        "description": data.get("desc") or "",
        "track_count": data.get("songnum") or len(songlist),
        "creator": data.get("nick_name") or data.get("nickname") or data.get("creator", {}).get("name", ""),
    }
    songs = [parse_song(s) for s in songlist if s]
    return playlist_info, songs


def main():
    import argparse

    parser = argparse.ArgumentParser(description="抓取 QQ 音乐歌单并导出")
    parser.add_argument("playlist", type=str, help="歌单链接、ID 或存有链接的文本文件路径")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出 JSON 路径")
    parser.add_argument("-t", "--csv", type=str, default=None, help="输出 CSV 路径")
    args = parser.parse_args()

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
                    if "y.qq.com" in line:
                        playlist_input = line
                    continue
                # 注释行：只认含 y.qq.com 的链接；取最后一个匹配，避免用模板里的示例 ID
                urls = re.findall(r"https?://\S+", line)
                for u in urls:
                    u = u.rstrip(".,;:)")
                    if "y.qq.com" in u:
                        playlist_input = u
        if playlist_input == link_file or (not playlist_input.strip()):
            raise ValueError("歌单链接.txt 中未找到有效链接，请粘贴 QQ 音乐歌单完整链接（如 https://y.qq.com/n/yqq/playlist/xxx.html）")

    playlist_id = extract_playlist_id(playlist_input)
    print(f"QQ 歌单 ID: {playlist_id}")
    print("正在获取歌单与歌曲信息...")

    playlist_info, songs = get_playlist_songs(playlist_id)
    print(f"\n歌单: {playlist_info['name']}")
    print(f"创建者: {playlist_info['creator']}")
    print(f"歌曲数量: {len(songs)}")

    result = {"playlist": playlist_info, "songs": songs}
    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"已保存 JSON: {args.output}")

    if args.csv and songs:
        csv_arg = (args.csv or "").strip().rstrip('"').rstrip("/\\")
        csv_path = _resolve_csv_path(csv_arg, playlist_info.get("creator", ""), script_dir)
        if not csv_path:
            csv_path = csv_arg
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "artists", "album", "duration"])
            w.writeheader()
            w.writerows([{k: s.get(k, "") for k in ["id", "name", "artists", "album", "duration"]} for s in songs])
        print(f"已保存 CSV: {csv_path}")
        # 供批处理打开该文件
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
