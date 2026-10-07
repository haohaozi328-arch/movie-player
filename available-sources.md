# 可用采集源清单（20 个精选）

> 更新：2026-10-07，从 38 个实测源中人工精选保留 20 个
> 来源：wsyzy 技能 GitHub 仓库 https://github.com/haohaozi328-arch/movie-player
> （无需每次拉取；仅当搜索/播放失败、源大面积不可用，或用户要求更新时再获取最新清单）

> ⚠️ **声明**：以上所有链接均来源于网络，仅供学习研究使用。
> 请勿相信采集站页面中出现的任何广告、付费引导、会员开通等信息，
> 本 skill 不对任何第三方内容负责，请支持正版。

## 源列表

| # | 采集接口 |
|---|---------|
| 0 | http://hongniuzy2.com/api.php/provide/vod/ |
| 1 | https://360zy.com/api.php/provide/vod/ |
| 2 | https://api.apibdzy.com/api.php/provide/vod |
| 3 | https://api.guangsuapi.com/api.php/provide/vod/ |
| 4 | https://api.maoyanapi.top/api.php/provide/vod |
| 5 | https://api.niuniuzy.me/api.php/provide/vod/ |
| 6 | https://api.wujinapi.me/api.php/provide/vod/ |
| 7 | https://bfzyapi.com/api.php/provide/vod/ |
| 8 | https://cj.yayazy.net/api.php/provide/vod/ |
| 9 | https://dbzy.tv/api.php/provide/vod/ |
| 10 | https://ffzy5.tv/api.php/provide/vod/ |
| 11 | https://haohuazy.com/api.php/provide/vod/ |
| 12 | https://huyazy.net/api.php/provide/vod/ |
| 13 | https://jszyapi.com/api.php/provide/vod/ |
| 14 | https://m3u8.apiyhzy.com/api.php/provide/vod |
| 15 | https://mtzy5.com/api.php/provide/vod/ |
| 16 | https://subocj.com/api.php/provide/vod/ |
| 17 | https://tyyszyapi.com/api.php/provide/vod/ |
| 18 | https://www.mdzyapi.com/api.php/provide/vod/ |
| 19 | https://api.wsyzy.net/api.php/provide/vod/ （默认源） |

## 更新方式

1. 打开本技能的 GitHub 仓库页面，获取最新的采集源列表。
2. 将新列表中 URL 填入 `scripts/available_sources.json`。
3. 运行 `python scripts/wsyzy.py sources` 校验编号是否正确。

## 使用

```bash
python scripts/wsyzy.py search "关键词" --src 7
python scripts/wsyzy.py play <vod_id> 第01集 --src wsyzy
```
