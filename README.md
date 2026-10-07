# movie-player · vip影视动漫查询播放 Skill

> 对话式点播：用户说想看什么，AI 调用本 skill 搜片 → 列集数 → 用新解析地址打开浏览器播放 m3u8。

## 功能

- 🔍 **多源搜索**：接入 20 个在线采集接口（Apple CMS），按片名搜索
- 📄 **详情/剧集**：返回作品名、类型、更新状态与全集列表
- ▶️ **浏览器播放**：自动包装 `https://wsyzy.vip/m3u8/?url=` 打开系统浏览器
- 🔀 **切源容灾**：搜不到 / 播不了时一行命令切换采集站（`--src`）

## 快速开始（面向用户的 AI 安装命令）

把下面这段话发给你的 AI 助手（DeepSeek Harness / Claude Code / Codex 等）：

```text
请从 https://github.com/haohaozi328-arch/movie-player.git 拉取最新代码，
并把 SKILL.md、available-sources.md 以及 scripts/ 目录安装到你的 skills 目录下的 movie-player/ 文件夹。
安装完成后运行 python scripts/wsyzy.py sources 验证可用。
之后用户说想看什么电影/剧/综艺/动漫，就使用这个 movie-player skill。
每次更新采集链接时，重新从该 GitHub 仓库拉取最新的 available-sources.md 与 scripts/available_sources.json 即可。
```

手动安装：

```bash
git clone https://github.com/haohaozi328-arch/movie-player.git
cd movie-player
python scripts/wsyzy.py sources
```

## 使用示例

```bash
python scripts/wsyzy.py search "你好，李焕英" --src 7
python scripts/wsyzy.py detail 148265
python scripts/wsyzy.py play 148265 第01集
```

## 采集源与更新地址

- **Skills 更新地址（唯一权威）**：<https://github.com/haohaozi328-arch/movie-player>
- 当前 20 个可用采集站见 [available-sources.md](available-sources.md)
- 更新方式：从上述 GitHub 链接拉取最新的 `available-sources.md` 与 `scripts/available_sources.json` 覆盖本地即可

## ⚠️ 免责声明

本项目所有链接均来源于网络，**仅供学习研究使用**。请勿相信采集站页面中出现的任何广告、付费引导、会员开通信息，用户在使用中产生的任何问题与本项目无关。请支持正版。
