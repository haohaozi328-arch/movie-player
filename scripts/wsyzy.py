#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资源站查询与播放助手（多源）

用法:
  python wsyzy.py sources                        列出可用采集接口
  python wsyzy.py search <关键词> [--src N|名称]  搜索（优先 wd 参数，失败回退本地过滤）
  python wsyzy.py detail <vod_id> [--src N]     查看详情与剧集
  python wsyzy.py play <m3u8地址>                  新解析播放并打开浏览器
  python wsyzy.py play <vod_id> [集号|集名] [--src N]  按 ID 播放指定集

注意:
  用户常把完整片名说成简称（如「凡人」→《凡人修仙传》）。
  search 命中多条候选时会输出 [提示]；请先把候选列表交用户确认，
  得到确认的序号/完整片名后再 detail / play，不要直接播放第一条。
"""
import sys, json, urllib.request, urllib.parse, re, webbrowser

PARSER = "https://wsyzy.vip/m3u8/?url="  # 新解析播放;旧的 wsyzy.top 已不可用

# 可用采集接口（20 个精选）
SOURCES = [
    "http://hongniuzy2.com/api.php/provide/vod/",
    "https://360zy.com/api.php/provide/vod/",
    "https://api.apibdzy.com/api.php/provide/vod",
    "https://api.guangsuapi.com/api.php/provide/vod/",
    "https://api.maoyanapi.top/api.php/provide/vod",
    "https://api.niuniuzy.me/api.php/provide/vod/",
    "https://api.wujinapi.me/api.php/provide/vod/",
    "https://bfzyapi.com/api.php/provide/vod/",
    "https://cj.yayazy.net/api.php/provide/vod/",
    "https://dbzy.tv/api.php/provide/vod/",
    "https://ffzy5.tv/api.php/provide/vod/",
    "https://haohuazy.com/api.php/provide/vod/",
    "https://huyazy.net/api.php/provide/vod/",
    "https://jszyapi.com/api.php/provide/vod/",
    "https://m3u8.apiyhzy.com/api.php/provide/vod",
    "https://mtzy5.com/api.php/provide/vod/",
    "https://subocj.com/api.php/provide/vod/",
    "https://tyyszyapi.com/api.php/provide/vod/",
    "https://www.mdzyapi.com/api.php/provide/vod/",
    "https://api.wsyzy.net/api.php/provide/vod/",
]
DEFAULT_SRC = len(SOURCES) - 1  # wsyzy
HEADERS = {"User-Agent": "Mozilla/5.0"}


def norm(u: str) -> str:
    return u if u.endswith("/") else u + "/"


def resolve_src(s):
    if s is None:
        return DEFAULT_SRC
    if str(s).isdigit():
        i = int(s)
        return i if 0 <= i < len(SOURCES) else DEFAULT_SRC
    for i, u in enumerate(SOURCES):
        if s in u:
            return i
    return DEFAULT_SRC


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read().decode("utf-8", "ignore")


def api_list(src, page=1):
    return json.loads(get(f"{norm(SOURCES[src])}?ac=list&pg={page}"))


def api_detail(src, vod_id):
    return json.loads(get(f"{norm(SOURCES[src])}?ac=detail&ids={urllib.parse.quote(str(vod_id))}"))


def parse_play_urls(vod: dict):
    out = []
    for seg in (vod.get("vod_play_url") or "").split("#"):
        if not seg:
            continue
        if "$" in seg:
            name, url = seg.split("$", 1)
            out.append({"name": name, "url": url})
        else:
            out.append({"name": "", "url": seg})
    return out


def search(keyword, src, page=1):
    # 1) wd 参数直搜
    try:
        txt = get(f"{norm(SOURCES[src])}?ac=list&wd={urllib.parse.quote(keyword)}")
        if txt.strip().startswith("{"):
            lst = json.loads(txt).get("list") or []
            if lst:
                return lst
    except Exception:
        pass
    # 2) 本地过滤回退
    hits = []
    for p in range(page, page + 5):
        try:
            j = api_list(src, p)
        except Exception:
            continue
        for it in j.get("list", []):
            if keyword in it.get("vod_name", ""):
                hits.append({"vod_id": it["vod_id"], "vod_name": it["vod_name"],
                             "type_name": it.get("type_name"), "vod_remarks": it.get("vod_remarks"),
                             "src": src})
        if len(hits) >= 20:
            break
    return hits


def detail(src, vod_id):
    j = api_detail(src, vod_id)
    lst = j.get("list") or []
    if not lst:
        print("未找到")
        return
    v = lst[0]
    eps = parse_play_urls(v)
    print(json.dumps({"vod_id": v["vod_id"], "vod_name": v["vod_name"],
                      "type_name": v.get("type_name"), "vod_remarks": v.get("vod_remarks"),
                      "episode_count": len(eps), "episodes": [e["name"] for e in eps]},
                     ensure_ascii=False, indent=2))


def play(src, target, ep=None):
    if target.endswith(".m3u8") or target.startswith("http"):
        m3u8, label = target, target
    else:
        j = api_detail(src, target)
        lst = j.get("list") or []
        if not lst:
            print("未找到该视频"); return
        v = lst[0]
        eps = parse_play_urls(v)
        if not eps:
            print("无可用播放地址"); return
        if ep:
            pick = next((e for e in eps if e["name"] == ep or ep in e["name"]), None)
            if not pick and str(ep).isdigit():
                pick = eps[int(ep) - 1] if 1 <= int(ep) <= len(eps) else None
            pick = pick or eps[0]
            m3u8, label = pick["url"], f"{v['vod_name']} {pick['name']}"
        else:
            m3u8, label = eps[0]["url"], f"{v['vod_name']} {eps[0]['name']}"
    url = PARSER + urllib.parse.quote(m3u8, safe="")
    print(f"播放: {label}\n{url}")
    webbrowser.open(url)


def parse_flags(args):
    src = None
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--src" and i + 1 < len(args):
            src = args[i + 1]; i += 2
        else:
            rest.append(args[i]); i += 1
    return src, rest


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    cmd, rest = args[0], args[1:]
    src_flag, rest = parse_flags(rest)
    src = resolve_src(src_flag)
    if cmd == "sources":
        for i, u in enumerate(SOURCES):
            print(f"[{i}] {u}" + ("  (默认)" if i == DEFAULT_SRC else ""))
    elif cmd == "search" and rest:
        kw = rest[0]
        hits = search(kw, src)[:30]
        # 短名/简称/多候选 → 必须先与用户确认，避免播错片
        if len(hits) > 1:
            print(f"[提示] 关键词「{kw}」命中 {len(hits)} 条候选，属于简称/歧义输入；"
                  f"请先把候选列表给用户确认，得到序号或完整片名后再执行 detail/play。", file=sys.stderr)
        elif len(hits) == 1:
            print(f"[提示] 唯一候选：《{hits[0].get('vod_name')}》。"
                  f"若「{kw}」是简称（如「凡人」→《凡人修仙传》），仍需与用户确认后再播放。", file=sys.stderr)
        else:
            print(f"[提示] 未找到「{kw}」；请换 --src 重试，或请用户给出更完整的片名，不要猜片。", file=sys.stderr)
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    elif cmd == "detail" and rest:
        detail(src, rest[0])
    elif cmd == "play" and rest:
        play(src, rest[0], rest[1] if len(rest) > 1 else None)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
