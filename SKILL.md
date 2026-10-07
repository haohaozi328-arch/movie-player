---
name: movie-player
description: |
  查询无水印资源网（wsyzy.cc / api.wsyzy.net）的影视资源，并通过解析播放器在浏览器中打开 m3u8 播放地址。
  Trigger keywords: 电影, 电视剧, 综艺, 动漫, 短剧, 资源网, wsyzy, 在线看, 播放, 看点什么, 想看.
---

# vip影视动漫查询播放 (wsyzy)

当用户说想看什么电影/剧/综艺/动漫，或给出影视名字、想在线播放时，使用本 skill。

## 默认源（最高优先级）

**默认源：<https://wsyzy.cc/>（采集接口 `https://api.wsyzy.net/api.php/provide/vod/`），优先级最高。**

- 搜索时**先查 wsyzy.cc（api.wsyzy.net）**；只有它没有结果时，才自动按顺序回退到其余备用源。
- 播放解析统一使用 `https://wsyzy.vip/m3u8/?url=`（旧 `wsyzy.top` 已屏蔽）。
- 单独指定备用源：`--src N或域名`（`python scripts/wsyzy.py sources` 查看编号）。

## 优先站点（先让用户确认）

部分作品配置了**优先播放页**，命中时**先用浏览器打开该页面让用户确认**，确认没有要看的再走采集站。

| 作品 | 优先播放页 |
|------|-----------|
| 凡人修仙传 | <https://www.4kvms.org/play/cgzq7f67f> |

流程：

1. 用户确认作品后，先查优先站点：
   ```bash
   python scripts/wsyzy.py prefer "凡人修仙传"
   ```
   命中则自动打开该播放页，并提示"先看看有没有你要的"。
2. 询问用户：这个页面里有没有你要看的？
   - **有** → 停在该页面，不再走采集站。
   - **没有** → 使用采集站解析播放：
     ```bash
     python scripts/wsyzy.py play <vod_id> [集] --force
     ```
     （默认源 wsyzy.cc 优先，无结果才回退备用源）
3. `play <vod_id>` 命中优先站点时也会**自动先打开优先页**，只有加 `--force` 才直接用采集站，避免播错或不必要的跳转。

新增优先站点：在 `scripts/wsyzy.py` 的 `PREFERRED` 字典中加一条即可。

## 接口事实（已实测）

| 用途 | 地址 | 状态 |
|------|------|------|
| 采集接口 JSON | `https://api.wsyzy.net/api.php/provide/vod/?ac=list` | 可用，返回 Apple CMS 列表 |
| 采集接口 XML | `https://api.wsyzy.net/api.php/provide/vod/from/wsym3u8/at/xml` | 可用（无搜索） |
| 详情（含播放地址） | `https://api.wsyzy.net/api.php/provide/vod/?ac=detail&ids=<vod_id>` | 可用 |
| 搜索 `?ac=list&wd=` | `https://api.wsyzy.net/api.php/...` | ❌ 大多数源返回"暂不支持搜索"，脚本自动回退为本地过滤 |
| 站内搜索 | `https://wsyzy.cc/index.php/vod/search.html?wd=<关键词>` | 有验证码拦截 |
| 播放页 | `https://wsyzy.cc/index.php/vod/detail/id/<vod_id>/p/1/nid/1/from/wsym3u8.html` | 可获取真实 m3u8 |
| 接口事实表见 | [available-sources.md](available-sources.md) | 20 个精选采集源，含免责声明 |
| 新解析播放（可用） | `https://wsyzy.vip/m3u8/?url=<m3u8地址>` | 当前有效 |
| 旧解析播放 | `https://wsyzy.top/m3u8/?url=<m3u8地址>` | 被屏蔽不可用，仅作备用 |

## 工作流

1. **查看源**：`python scripts/wsyzy.py sources` 列出全部采集站（`[0]` 为默认源 wsyzy.cc，优先级最高；其余为备用）。
2. **搜索**：先问用户想看什么。
   ```bash
   python scripts/wsyzy.py search "<关键词>" [--src N或域名]
   ```
   不加 `--src` 时自动"默认源优先、无结果再回退备用源"。展示候选（vod_id、名称、类型、备注）让用户挑。
   关键词为**短名/简称**时必须先与用户确认，见下一节。
3. **详情/剧集**：
   ```bash
   python scripts/wsyzy.py detail <vod_id> [--src N]
   ```
4. **播放**：
   ```bash
   python scripts/wsyzy.py speed <vod_id> <集号>        # 先实测速度，挑最快的一条
   python scripts/wsyzy.py play <vod_id> <集号或集名> [--src N] [--force]
   ```
   或直接给 m3u8：
   ```bash
   python scripts/wsyzy.py play "https://v13.wsyzym3u8.com/.../index.m3u8"
   ```
   脚本会用 `https://wsyzy.vip/m3u8/?url=` 包装后 `webbrowser.open()` 打开系统浏览器播放。
   **同时最多测 2 个候选、只打开 1 个播放页**，不要同时打开很多个视频。

## 播放速度自判（AI 自行比较，不要多开）

不猜"哪个源快"，直接用 `speed` 实测后挑最快的一条：

```bash
python scripts/wsyzy.py speed <vod_id> <集号>            # 在默认源内比较线路
python scripts/wsyzy.py speed <关键词> --all --top 3     # 跨采集站比较同一集
```

- 实测内容：播放列表可达性 + 首分片下载速度（KB/s）与延迟（ms）。
- **并发上限 2**：一次最多同时拉 2 路，避免同时播放很多个视频把带宽/内存打满。
- 输出按速度排序，并给出 `[推荐]` + `[解析播放]` 链接；**只打开这一个链接**。
- 推荐链接慢或打不开时，再换下一个候选，或 `--src` 换源重测。



用户经常把完整剧名说成简称，例如把**《凡人修仙传》说成「凡人」**、把《斗罗大陆》说成「斗罗」、
把《盗墓笔记》说成「盗墓」等。这类输入**不能直接 detail / play**，否则极易播错片子。

> 注意：《凡人修仙传》除简称确认外，还要走上面的**优先站点**流程（先打开 4kvms 播放页确认）。

**规则**：

1. 拿到片名后**第一步永远是 search**，不要凭猜测直接取第一条结果播放。
2. 命中以下任一情况，**必须先把候选列给用户并等待确认**：
   - 关键词是简称/前缀（短于片名，如「凡人」「斗罗」）
   - 关键词汉字数 < 4，或明显是某部作品名的一部分
   - 搜索结果 ≥ 2 条
3. 确认话术示例：

   ```
   你说的「凡人」可能指这几部，请确认是哪一个：
   1. 凡人修仙传（国产动漫 | 更新第120集）
   2. 凡人修仙传之仙界篇（国产动漫 | 更新第40集）
   3. 凡人修仙传（真人剧 | 完结）
   回复序号即可，或直接给出完整片名。
   ```

4. 只有用户确认后（或候选唯一且名称与用户所说完全一致时）才继续 detail 与 play。
5. 搜索无结果时：换 `--src` 重试，或请用户提供更完整的片名，**不要猜片**。
6. 任何情况下都不要在未经确认时把简称直接当成某部作品的唯一结果去播放。

脚本支持一次列出多条候选，便于确认：

```bash
python scripts/wsyzy.py search "凡人" --src wsyzy   # 列出全部候选，由用户挑选
```

## 注意

- 脚本输出中文可能出现控制台乱码，不影响数据与 URL，可保存为 UTF-8 文件再读。
- `wsyzy.top` 解析播放已被屏蔽，默认使用 `wsyzy.vip`。
- 本 skill 仅供个人学习研究，请自行遵守版权法规，支持正版。
- **所有链接均来源于网络，请勿相信采集站页面中出现的任何广告、付费引导、会员开通信息。** 采集链接更新地址（备用）：https://github.com/haohaozi328-arch/movie-player —— **无需每次使用前拉取最新清单**，由 AI 自行判断：仅当搜索/播放失败、源大面积不可用、或用户主动要求更新时，才去该地址取最新采集源。
- 如需 Node 版，可用 `scripts/wsyzy.mjs`。
- **简称/短名（如「凡人」→《凡人修仙传》）必须先 search 并把候选交用户确认，确认前不得 detail/play。**
