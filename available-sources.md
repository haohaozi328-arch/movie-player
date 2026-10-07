# 可用采集源清单（20 个精选）

> 更新：2026-10-07，从 38 个实测源中人工精选保留 20 个
> 来源：wsyzy 技能 GitHub 仓库 https://github.com/haohaozi328-arch/movie-player
> （无需每次拉取；仅当搜索/播放失败、源大面积不可用，或用户要求更新时再获取最新清单）

> ⚠️ **声明**：以上所有链接均来源于网络，仅供学习研究使用。
> 请勿相信采集站页面中出现的任何广告、付费引导、会员开通等信息，
> 本 skill 不对任何第三方内容负责，请支持正版。

## 源列表

> `[0]` 为**默认源（最高优先级）**：站点 <https://wsyzy.cc/>，采集接口 api.wsyzy.net。
> 搜索时先查该源，无结果才按顺序回退到下列备用源。

| # | 采集接口 | 角色 |
|---|---------|------|
| 0 | https://api.wsyzy.net/api.php/provide/vod/ | ⭐ 默认源（站点 wsyzy.cc） |
| 1 | http://hongniuzy2.com/api.php/provide/vod/ | 备用 |
| 2 | https://360zy.com/api.php/provide/vod/ | 备用 |
| 3 | https://api.apibdzy.com/api.php/provide/vod | 备用 |
| 4 | https://api.guangsuapi.com/api.php/provide/vod/ | 备用 |
| 5 | https://api.maoyanapi.top/api.php/provide/vod | 备用 |
| 6 | https://api.niuniuzy.me/api.php/provide/vod/ | 备用 |
| 7 | https://api.wujinapi.me/api.php/provide/vod/ | 备用 |
| 8 | https://bfzyapi.com/api.php/provide/vod/ | 备用 |
| 9 | https://cj.yayazy.net/api.php/provide/vod/ | 备用 |
| 10 | https://dbzy.tv/api.php/provide/vod/ | 备用 |
| 11 | https://ffzy5.tv/api.php/provide/vod/ | 备用 |
| 12 | https://haohuazy.com/api.php/provide/vod/ | 备用 |
| 13 | https://huyazy.net/api.php/provide/vod/ | 备用 |
| 14 | https://jszyapi.com/api.php/provide/vod/ | 备用 |
| 15 | https://m3u8.apiyhzy.com/api.php/provide/vod | 备用 |
| 16 | https://mtzy5.com/api.php/provide/vod/ | 备用 |
| 17 | https://subocj.com/api.php/provide/vod/ | 备用 |
| 18 | https://tyyszyapi.com/api.php/provide/vod/ | 备用 |
| 19 | https://www.mdzyapi.com/api.php/provide/vod/ | 备用 |

## 更新方式

1. 打开本技能的 GitHub 仓库页面，获取最新的采集源列表。
2. 将新列表中 URL 填入 `scripts/available_sources.json`（保持默认源在数组第 1 位）。
3. 运行 `python scripts/wsyzy.py sources` 校验编号是否正确。

## 使用

```bash
python scripts/wsyzy.py search "关键词"          # 默认源优先，自动回退备用源
python scripts/wsyzy.py search "关键词" --src 8  # 指定备用源
python scripts/wsyzy.py play <vod_id> 第01集
```
