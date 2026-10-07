---
name: movie-player
description: |
  查询无水印资源网（wsyzy.cc / api.wsyzy.net）的影视资源，并通过解析播放器在浏览器中打开 m3u8 播放地址。
  Trigger keywords: 电影, 电视剧, 综艺, 动漫, 短剧, 资源网, wsyzy, 在线看, 播放, 看点什么, 想看.
---

# vip影视动漫查询播放 (wsyzy)

当用户说想看什么电影/剧/综艺/动漫，或给出影视名字、想在线播放时，使用本 skill。

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

1. **查看源**：`python scripts/wsyzy.py sources` 列出 20 个精选采集站（默认源 wsyzy）。
2. **搜索**：先问用户想看什么。
   ```bash
   python scripts/wsyzy.py search "<关键词>" [--src N或域名]
   ```
   展示候选（vod_id、名称、类型、备注）让用户挑；搜不到换 `--src` 切源再试。
3. **详情/剧集**：
   ```bash
   python scripts/wsyzy.py detail <vod_id> [--src N]
   ```
4. **播放**：
   ```bash
   python scripts/wsyzy.py play <vod_id> <集号或集名> [--src N]
   ```
   或直接给 m3u8：
   ```bash
   python scripts/wsyzy.py play "https://v13.wsyzym3u8.com/.../index.m3u8"
   ```
   脚本会用 `https://wsyzy.vip/m3u8/?url=` 包装后 `webbrowser.open()` 打开系统浏览器播放。

## 注意

- 脚本输出中文可能出现控制台乱码，不影响数据与 URL，可保存为 UTF-8 文件再读。
- `wsyzy.top` 解析播放已被屏蔽，默认使用 `wsyzy.vip`。
- 本 skill 仅供个人学习研究，请自行遵守版权法规，支持正版。
- **所有链接均来源于网络，请勿相信采集站页面中出现的任何广告、付费引导、会员开通信息。** 最新链接清单请以本 skill 的 GitHub 仓库为准。
- 如需 Node 版，可用 `scripts/wsyzy.mjs`。
