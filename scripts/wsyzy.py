#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资源站查询与播放助手（多源）

用法:
  python wsyzy.py sources                        列出可用采集接口
  python wsyzy.py search <关键词> [--src N|名称]  搜索（默认源优先，无结果自动回退备用源）
  python wsyzy.py detail <vod_id> [--src N]     查看详情与剧集
  python wsyzy.py speed <vod_id|关键词> [集号] [--src N|all] [--top N]
                                                 实测各候选播放地址速度，挑最快的一个
  python wsyzy.py prefer <片名>                   命中优先站点则打开指定播放页，请用户确认
  python wsyzy.py play <m3u8地址>                  新解析播放并打开浏览器
  python wsyzy.py play <vod_id> [集号|集名] [--src N] [--force]
                                                 按 ID 播放指定集；命中优先站点时会先打开优先页，
                                                 用户确认没有要看的再加 --force 改用采集站

注意:
  1. 用户常把完整片名说成简称（如「凡人」→《凡人修仙传》）。
     search 命中多条候选时会输出 [提示]；请先把候选列表交用户确认，
     得到确认的序号/完整片名后再 detail / play，不要直接播放第一条。
  2. 速度由 speed 命令实测决定：并发上限 2，只对比少量候选，
     挑最快的一个播放；不要同时打开很多个视频/标签页。
  3. 《凡人修仙传》等已配置优先站点的作品：先打开优先播放页让用户确认，
     用户说没有要看的，再用默认采集源/备用源（--force）。
"""
import sys, json, time, urllib.request, urllib.parse, re, webbrowser
from concurrent.futures import ThreadPoolExecutor

PARSER = "https://wsyzy.vip/m3u8/?url="  # 新解析播放;旧的 wsyzy.top 已不可用

# 默认源（最高优先级）：https://wsyzy.cc/  →  采集接口 api.wsyzy.net
SITE = "https://wsyzy.cc/"
DEFAULT_API = "https://api.wsyzy.net/api.php/provide/vod/"

# 可用采集接口（20 个精选；[0] 为默认优先源，其余为备用）
SOURCES = [
    DEFAULT_API,
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
]
DEFAULT_SRC = 0  # wsyzy.cc / api.wsyzy.net 优先级最高
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": SITE}

# 优先站点：命中这些作品时，先打开指定播放页让用户确认有没有想看的；
# 用户确认没有（或该页不可用）时，再回退到采集站。
PREFERRED = {
    "凡人修仙传": "https://www.4kvms.org/play/cgzq7f67f",
}


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
    """解析 vod_play_url。
    多播放组用 $$$ 分隔（组名见 vod_play_from），组内用 # 分隔剧集，格式：剧集名$m3u8地址。"""
    froms = [g for g in (vod.get("vod_play_from") or "").split("$$$") if g]
    out = []
    for gi, grp in enumerate((vod.get("vod_play_url") or "").split("$$$")):
        gname = froms[gi] if gi < len(froms) else f"线路{gi + 1}"
        for seg in grp.split("#"):
            seg = seg.strip()
            if not seg:
                continue
            if "$" in seg:
                name, url = seg.split("$", 1)
            else:
                name, url = "", seg
            url = url.strip()
            if not url.startswith("http"):
                continue
            out.append({"group": gname, "name": name, "url": url})
    return out


def measure(url, timeout=8, sample=262144):
    """实测一个 m3u8 的可用性与速度。
    返回 dict(ok, latency_ms, kbps, note)：先取播放列表，再 Range 拉首个分片估算带宽。"""
    res = {"url": url, "ok": False, "latency_ms": None, "kbps": None, "note": ""}
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
        res["latency_ms"] = int((time.time() - t0) * 1000)
    except Exception as e:
        res["note"] = f"播放列表不可达: {str(e)[:40]}"
        return res
    text = body.decode("utf-8", "ignore")
    if "#EXTM3U" not in text:
        res["note"] = "非 HLS 播放列表"
        return res
    res["ok"] = True
    # 找首个分片地址（跳过 #EXT-X-STREAM-INF 的下一行也按行处理）
    seg = ""
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            seg = line
            break
    if not seg:
        res["note"] = "无分片（可能为纯音频或加密列表）"
        return res
    seg_url = urllib.parse.urljoin(url, seg)
    try:
        t1 = time.time()
        req = urllib.request.Request(seg_url, headers={**HEADERS, "Range": f"bytes=0-{sample - 1}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(sample)
        dt = max(time.time() - t1, 0.001)
        res["kbps"] = int(len(data) * 8 / dt / 1000)
    except Exception as e:
        res["note"] = f"分片拉取失败: {str(e)[:40]}"
    return res


def speed_test(cands, top=3, workers=2):
    """并发实测候选地址（并发上限默认 2，避免同时拉起太多视频流），返回按速度排序的结果。"""
    if not cands:
        return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda c: {**measure(c["url"]), "cand": c}, cands))
    ok = [r for r in results if r["ok"]]
    ok.sort(key=lambda r: (r["kbps"] is None, -(r["kbps"] or 0), r["latency_ms"] or 0))
    bad = [r for r in results if not r["ok"]]
    return (ok + bad)[:top] if top else (ok + bad)

def search_one(keyword, src, page=1, pages=5):
    """在单个源内搜索：先 wd 直搜，失败则本地过滤"""
    # 1) wd 参数直搜
    try:
        txt = get(f"{norm(SOURCES[src])}?ac=list&wd={urllib.parse.quote(keyword)}")
        if txt.strip().startswith("{"):
            lst = json.loads(txt).get("list") or []
            if lst:
                for it in lst:
                    it.setdefault("src", src)
                return lst
    except Exception:
        pass
    # 2) 本地过滤回退
    hits = []
    for p in range(page, page + pages):
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


def search(keyword, src=None, page=1):
    """搜索。默认源（wsyzy.cc / api.wsyzy.net）优先级最高；
    未显式指定 --src 时，默认源无结果会自动按顺序回退到其余备用源。"""
    if src is not None:
        return search_one(keyword, src, page), src
    hits = search_one(keyword, DEFAULT_SRC, page, pages=5)
    if hits:
        return hits, DEFAULT_SRC
    for i in range(len(SOURCES)):
        if i == DEFAULT_SRC:
            continue
        try:
            hits = search_one(keyword, i, page, pages=2)
        except Exception:
            continue
        if hits:
            return hits, i
    return [], DEFAULT_SRC


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


def play(src, target, ep=None, force=False):
    if target.endswith(".m3u8") or target.startswith("http"):
        m3u8, label = target, target
    else:
        j = api_detail(src, target)
        lst = j.get("list") or []
        if not lst:
            print("未找到该视频"); return
        v = lst[0]
        # 命中优先站点：先打开优先播放页让用户确认，确认没有再用采集站（--force）
        purl = match_preferred(v.get("vod_name"))
        if purl and not force:
            print(f"[优先站点] 《{v['vod_name']}》优先打开：{purl}")
            print("[请确认] 先看这个页面有没有你要的；若没有，请加 --force 改用采集站解析播放。")
            webbrowser.open(purl)
            return
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


def pick_eps(eps, ep):
    """选出要测速的剧集：指定集名/集号优先，未指定则取第一集。"""
    if not eps:
        return []
    if not ep:
        return eps[:1]
    m = [e for e in eps if e["name"] == ep or ep in e["name"]]
    if m:
        return m[:1]
    if str(ep).isdigit():
        i = int(ep) - 1
        if 0 <= i < len(eps):
            return [eps[i]]
    return []


def match_preferred(name):
    """返回优先站点 URL（若该片名命中 PREFERRED），否则 None。"""
    if not name:
        return None
    for k, url in PREFERRED.items():
        if k in name or name in k:
            return url
    return None


def prefer(name, open_browser=True):
    """优先站点流程：命中则打开指定播放页，请用户确认；未命中则提示走采集站。"""
    url = match_preferred(name)
    if not url:
        print(f"[优先站点] 「{name}」没有配置优先播放页，直接使用默认源（wsyzy.cc）与其他采集站。")
        return False
    print(f"[优先站点] 「{name}」命中优先播放页：{url}")
    print("[请确认] 先在这个页面看看有没有你要看的；确认没有再回到采集站（wsyzy.cc 默认源优先，其余备用）。")
    if open_browser:
        webbrowser.open(url)
    return True


def collect_candidates(target, ep, src, all_sources=False, max_cands=6):
    """收集"同一部剧"的多个候选播放地址（用于测速对比）。
    target: vod_id 或 关键词；ep: 集号/集名；src: 源编号或 None（默认源优先）；
    all_sources: True 时对比全部源里同名作品的同一集。"""
    cands = []
    if str(target).isdigit():
        srcs = range(len(SOURCES)) if all_sources else [src if src is not None else DEFAULT_SRC]
        name_ref = None
        for i in srcs:
            try:
                j = api_detail(i, target)
            except Exception:
                continue
            v = (j.get("list") or [None])[0]
            if not v:
                continue
            name_ref = name_ref or v.get("vod_name")
            for e in pick_eps(parse_play_urls(v), ep):
                cands.append({"src": i, "label": f"{v['vod_name']} {e['name']} [{e['group']}]", "url": e["url"]})
            if len(cands) >= max_cands:
                break
        return cands
    # 关键词：先搜索定位作品，再按需在其他源里找同名作品
    hits, used = search(target, None if all_sources else src)
    if not hits:
        return []
    name = hits[0].get("vod_name") or target
    srcs = range(len(SOURCES)) if all_sources else [used]
    for i in srcs:
        try:
            found = search_one(name, i, pages=2)
        except Exception:
            found = []
        if not found:
            continue
        vid = found[0].get("vod_id")
        try:
            v = (api_detail(i, vid).get("list") or [None])[0]
        except Exception:
            v = None
        if not v:
            continue
        for e in pick_eps(parse_play_urls(v), ep):
            cands.append({"src": i, "label": f"{v['vod_name']} {e['name']} [{e['group']}]", "url": e["url"]})
        if len(cands) >= max_cands:
            break
    return cands[:max_cands]


def speed(src, target, ep=None, all_sources=False, top=3):
    cands = collect_candidates(target, ep, src, all_sources=all_sources, max_cands=6 if all_sources else 4)
    if not cands:
        print("[提示] 没有可测速的候选地址；请确认片名/集号，或换 --src 重试。", file=sys.stderr)
        return
    print(f"[测速] 共 {len(cands)} 个候选，并发上限 2（避免同时拉起过多视频流）…", file=sys.stderr)
    ranked = speed_test(cands, top=top, workers=2)
    print(f"{'排名':<4}{'速度KB/s':>10}{'延迟ms':>9}  {'源':<4}候选")
    best = None
    for n, r in enumerate(ranked, 1):
        c = r["cand"]
        kb = f"{r['kbps'] // 8}" if r["kbps"] else "-"
        lat = r["latency_ms"] if r["latency_ms"] is not None else "-"
        flag = "OK  " if r["ok"] else "FAIL"
        print(f"{n:<4}{kb:>10}{str(lat):>9}  [{c['src']}] {flag} {c['label']} {r['note']}")
        if best is None and r["ok"]:
            best = r
    if best:
        url = PARSER + urllib.parse.quote(best["cand"]["url"], safe="")
        print(f"\n[推荐] 最快可用：{best['cand']['label']}")
        print(f"[解析播放] {url}")
        print("[说明] 只打开这一个链接播放，不要同时开多个视频。", file=sys.stderr)
    else:
        print("\n[提示] 所有候选测速均失败，建议换 --src 或换一部作品。", file=sys.stderr)


def parse_flags(args):
    src, all_flag, top, force = None, False, 3, False
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--src" and i + 1 < len(args):
            src = args[i + 1]; i += 2
        elif a == "--all":
            all_flag = True; i += 1
        elif a == "--force":
            force = True; i += 1
        elif a == "--top" and i + 1 < len(args):
            try:
                top = int(args[i + 1])
            except Exception:
                top = 3
            i += 2
        else:
            rest.append(a); i += 1
    return src, rest, all_flag, top, force


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    cmd, rest = args[0], args[1:]
    src_flag, rest, all_flag, top, force = parse_flags(rest)
    src = resolve_src(src_flag) if src_flag is not None else None
    if cmd == "sources":
        for i, u in enumerate(SOURCES):
            tag = "  (默认源，最高优先级 wsyzy.cc)" if i == DEFAULT_SRC else ""
            print(f"[{i}] {u}{tag}")
    elif cmd == "search" and rest:
        kw = rest[0]
        hits, used = search(kw, src)
        hits = hits[:30]
        print(f"[源] 使用 [{used}] {SOURCES[used]}" + ("（默认优先源）" if used == DEFAULT_SRC else "（备用源）"),
              file=sys.stderr)
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
        detail(src if src is not None else DEFAULT_SRC, rest[0])
    elif cmd == "speed" and rest:
        speed(src, rest[0], rest[1] if len(rest) > 1 else None,
              all_sources=all_flag or src_flag == "all", top=top)
    elif cmd in ("prefer", "preferred") and rest:
        prefer(rest[0], open_browser=not force)
    elif cmd == "play" and rest:
        play(src if src is not None else DEFAULT_SRC, rest[0],
             rest[1] if len(rest) > 1 else None, force=force)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
