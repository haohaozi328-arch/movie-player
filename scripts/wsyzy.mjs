#!/usr/bin/env node
/* 无水印资源网 (wsyzy) 查询与播放助手
 * 用法:
 *   node wsyzy.mjs search <关键词> [pg]      在站内搜索(解析首页分类列表后本地过滤，失败时用 ddapi 镜像搜索)
 *   node wsyzy.mjs detail <vod_id>          获取视频详情与播放地址
 *   node wsyzy.mjs play <m3u8地址>           用 https://wsyzy.vip/m3u8/?url= 打开浏览器播放
 *   node wsyzy.mjs play <vod_id> <集号>       直接按 id 播放指定集
 */
import { exec } from 'node:child_process';

const API = 'https://api.wsyzy.net/api.php/provide/vod';
const SITE = 'https://wsyzy.cc';
const PARSER = 'https://wsyzy.vip/m3u8/?url=';

const headers = { 'User-Agent': 'Mozilla/5.0', Referer: SITE + '/' };

async function get(url) {
  const r = await fetch(url, { headers });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.text();
}

async function apiList(page = 1) {
  const txt = await get(`${API}/?ac=list&pg=${page}`);
  return JSON.parse(txt);
}

async function apiDetail(id) {
  const txt = await get(`${API}/?ac=detail&ids=${encodeURIComponent(id)}`);
  return JSON.parse(txt);
}

function parsePlayUrls(vod) {
  // vod_play_url: "第01集$https://...index.m3u8#第02集$https://...index.m3u8"
  return (vod.vod_play_url || '')
    .split('#')
    .filter(Boolean)
    .map((seg) => {
      const i = seg.indexOf('$');
      return i >= 0 ? { name: seg.slice(0, i), url: seg.slice(i + 1) } : { name: '', url: seg };
    });
}

async function search(keyword, pg = 1) {
  // 优先:POST 站内搜索(若站点放行);回退:遍历分类列表做本地过滤
  try {
    const html = await get(`${SITE}/index.php/vod/search.html?wd=${encodeURIComponent(keyword)}`);
    if (!html.includes('安全验证')) {
      const items = [...html.matchAll(/detail\/id\/(\d+)\.html[^>]*>([^<]*)/g)].map((m) => ({
        vod_id: +m[1],
        vod_name: m[2].trim(),
      }));
      if (items.length) return items;
    }
  } catch {}
  const out = [];
  for (let p = +pg; p < +pg + 5 && out.length < 20; p++) {
    const j = await apiList(p);
    for (const it of j.list || []) {
      if (it.vod_name.includes(keyword)) out.push({ vod_id: it.vod_id, vod_name: it.vod_name, type_name: it.type_name, vod_remarks: it.vod_remarks });
    }
  }
  return out;
}

async function main() {
  const [cmd, a, b] = process.argv.slice(2);
  switch (cmd) {
    case 'search': {
      const kw = a;
      if (!kw) return console.error('需要关键词');
      const list = await search(kw, b || 1);
      console.log(JSON.stringify(list.slice(0, 30), null, 2));
      break;
    }
    case 'detail': {
      const j = await apiDetail(a);
      const v = j.list?.[0];
      if (!v) return console.error('未找到');
      console.log(JSON.stringify({
        vod_id: v.vod_id, vod_name: v.vod_name, type_name: v.type_name,
        vod_remarks: v.vod_remarks, episodes: parsePlayUrls(v).map((e) => e.name),
      }, null, 2));
      break;
    }
    case 'play': {
      let m3u8;
      if (/^\d+$/.test(a)) {
        const j = await apiDetail(a);
        const eps = parsePlayUrls(j.list?.[0] || {});
        const ep = eps.find((e) => e.name === b) || eps[+b - 1] || eps[0];
        if (!ep) return console.error('无可用播放地址');
        m3u8 = ep.url;
        console.log(`播放: ${j.list[0].vod_name} ${ep.name}`);
      } else {
        m3u8 = a;
      }
      const url = PARSER + encodeURIComponent(m3u8);
      // 新解析播放;仍可用时可替换为 https://wsyzy.top/m3u8/?url=
      console.log(url);
      exec(`start "" "${url}"`);
      break;
    }
    default:
      console.log('用法: node wsyzy.mjs search <关键词> [pg] | detail <id> | play <m3u8|id> [集]');
  }
}

main().catch((e) => { console.error(e.message); process.exit(1); });
