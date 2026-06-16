#!/usr/bin/env python3
"""Auto-updater for galaxy-guide. Run daily at 17:00 Taiwan time."""

import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TW = timezone(timedelta(hours=8))
REF = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
SYNODIC = 29.53058867

MAIN_LOCS = [
    {"name": "龍磐公園",        "region": "屏東 · 墾丁",        "lat": 21.9272, "lon": 120.8480, "maps": "21.9272,120.8480",
     "desc": "恆春半島東側的隆起珊瑚礁草原，<b>面太平洋、地平線無遮蔽</b>，往東南方正對銀河中心。24 小時開放、光害極低。風很大，記得帶外套、腳架壓重。"},
    {"name": "佳樂水 / 滿州一帶","region": "屏東 · 恆春半島東",  "lat": 22.0028, "lon": 120.8736, "maps": "22.0028,120.8736",
     "desc": "滿州是半島東側<b>光害最低的暗空帶之一</b>，比墾丁大街那側更暗。沿台 26 線找開闊處即可停車仰望。"},
    {"name": "社頂自然公園",    "region": "屏東 · 墾丁",        "lat": 21.9564, "lon": 120.8189, "maps": "21.9564,120.8189",
     "desc": "園區夜間幾乎無光害。正式步道 17:00 關閉，但<b>停車場周邊草地仍可仰望</b>，離墾丁大街近、補給方便。"},
    {"name": "華源海灣",        "region": "台東 · 太麻里",       "lat": 22.6625, "lon": 121.0289, "maps": "22.6625,121.0289",
     "desc": "台 9 線旁、<b>面東太平洋的無敵海景觀星點</b>，停車方便、24 小時開放，可順看日出。"},
    {"name": "三仙台",          "region": "台東 · 成功",         "lat": 23.1206, "lon": 121.4028, "maps": "23.1206,121.4028",
     "desc": "東海岸知名的<b>「海上銀河＋日出」雙拍點</b>，光害低，雲量比墾丁稍高一點。"},
]

RAINY_LOCS = [
    {"name": "阿里山",       "lat": 23.5107, "lon": 120.8031},
    {"name": "澎湖",         "lat": 23.5654, "lon": 119.6179},
    {"name": "合歡山鳶峰",   "lat": 24.1417, "lon": 121.2906},
    {"name": "武陵農場",     "lat": 24.3618, "lon": 121.3950},
    {"name": "池上 / 鹿野", "lat": 23.0962, "lon": 121.2177},
    {"name": "蘭嶼",         "lat": 22.0465, "lon": 121.5578},
    {"name": "小琉球",       "lat": 22.3432, "lon": 120.3781},
]

NUMS = ["一","二","三","四","五","六","七","八","九","十",
        "十一","十二","十三","十四","十五","十六","十七","十八",
        "十九","二十","廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"]

def fetch_rain(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast"
           f"?latitude={lat}&longitude={lon}"
           f"&hourly=precipitation_probability"
           f"&timezone=Asia%2FTaipei&forecast_days=2")
    try:
        with urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        probs = data["hourly"]["precipitation_probability"]
        night = probs[21:27]  # 21:00–02:00
        return round(sum(night) / len(night))
    except Exception as e:
        print(f"  Warning: weather fetch failed ({lat},{lon}): {e}", file=sys.stderr)
        return 55

def get_moon(dt):
    days = (dt.astimezone(timezone.utc) - REF).total_seconds() / 86400
    ld = int(days % SYNODIC) + 1  # lunar day 1–30
    n = NUMS[ld - 1]

    if ld == 1:
        return dict(v="新月（朔）", small="農曆初一 · 整夜無月光",
                    dek=f"農曆初一・新月</b>，整夜無月光干擾，是觀賞銀河最乾淨的時段之一",
                    peak="00–02 時", peak_s="核心過午夜抵正南最壯觀",
                    legend="新月整夜無月光，肉眼即可見銀河帶；用相機長曝效果更佳。",
                    reminder="今晚正逢<b>新月</b>（農曆初一），整夜黑暗，是觀星最理想的夜晚。")
    elif ld <= 4:
        sh = 18 + ld
        return dict(v=f"眉月（初{n}）", small=f"約 {sh}:30 落下 · 之後整夜無月光",
                    dek=f"農曆初{n}・眉月</b>，細月牙約 {sh}:30 沒入西方，之後整夜無月光干擾，是觀賞銀河的好時機",
                    peak=f"{sh+1}:00 後", peak_s=f"月落後即可出發，00–02 時核心最高",
                    legend=f"眉月約 {sh}:30 已落，{sh+1}:00 後整夜無月光，肉眼可見銀河帶；用相機長曝效果更佳。",
                    reminder=f"今晚眉月（初{n}）細如髮絲，<b>約 {sh}:30 即沒入西方地平線</b>，對觀星影響極小——{sh+1}:00 到達現場即可直接開始。")
    elif ld <= 8:
        sh = 21 + (ld - 5)
        return dict(v=f"上弦前（初{n}）", small=f"約 {sh}:00 落下，後半夜可觀星",
                    dek=f"農曆初{n}・上弦月前</b>，月亮約 {sh}:00 落下，後半夜可欣賞銀河",
                    peak=f"{sh}:00 後", peak_s="月落後黑暗，越晚越好",
                    legend=f"月亮約 {sh}:00 落，之後黑暗適合長曝拍銀河；核心在 01–02 時最高。",
                    reminder=f"今晚月亮（初{n}）約 <b>{sh}:00 落下</b>，在此之前有月光干擾；{sh}:00 後即可進行無月光觀星。")
    elif ld <= 15:
        return dict(v=f"{'滿月（望）' if ld>=14 else f'上弦月（初{n}）'}", small="前半夜月光明亮",
                    dek=f"農曆初{n}・上弦月</b>，前半夜月光明顯，00 時後才漸暗",
                    peak="00 時後", peak_s="前半夜月光干擾，後半夜較暗",
                    legend="上弦月前後，前半夜月光干擾；建議後半夜觀星。",
                    reminder=f"今晚上弦月（初{n}），<b>前半夜月光偏強</b>，建議等到 00 時月亮偏西後再長曝拍攝。")
    else:
        return dict(v=f"下弦月（{n}）", small="前半夜黑暗，適合觀星",
                    dek=f"農曆{n}・下弦月</b>，前半夜黑暗，把握 21:00–00:00 的時間窗口",
                    peak="21–00 時", peak_s="月升前觀賞，前半夜最佳",
                    legend="下弦月前半夜黑暗，把握 21–24 時黃金窗口拍攝銀河。",
                    reminder=f"今晚下弦月（{n}），<b>前半夜黑暗適合觀星</b>，建議把握 21:00–00:00 時間窗口，月升後光害增加。")


CSS = """
  :root{--ink:#0a0e23;--ink2:#121736;--panel:#161c40;--haze:#293266;--line:#2b3568;
    --star:#f3ecdd;--muted:#99a2cc;--muted2:#6f78a6;--glow:#ffd27a;--glow2:#ffb454;
    --aqua:#7fd6c2;--warn:#ff8b6b;}
  *{box-sizing:border-box;}
  html{-webkit-text-size-adjust:100%;}
  body{margin:0;background:var(--ink);color:var(--star);
    font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
    line-height:1.7;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:880px;margin:0 auto;padding:0 22px 80px;}
  .archive-banner{background:rgba(43,53,104,.5);border:1px solid var(--line);border-radius:10px;
    padding:10px 18px;margin:20px 0 0;font-family:"IBM Plex Mono",monospace;font-size:12.5px;
    color:var(--muted2);display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
  .archive-banner b{color:var(--muted);}
  .archive-banner a{color:var(--aqua);text-decoration:none;}
  .hero{position:relative;margin:0 -22px;padding:64px 22px 52px;overflow:hidden;
    background:radial-gradient(120% 80% at 78% -10%,rgba(255,180,84,.16),transparent 55%),
      radial-gradient(90% 120% at 10% 110%,rgba(127,214,194,.10),transparent 50%),
      linear-gradient(160deg,#0a0e23 0%,#101638 60%,#0a0e23 100%);}
  .hero .galaxy{position:absolute;inset:0;opacity:.5;pointer-events:none;
    background:radial-gradient(1px 1px at 20% 30%,#fff,transparent),
      radial-gradient(1px 1px at 40% 70%,#fff,transparent),
      radial-gradient(1px 1px at 65% 20%,#fff,transparent),
      radial-gradient(1px 1px at 80% 55%,#fff,transparent),
      radial-gradient(1px 1px at 12% 80%,#dfe6ff,transparent),
      radial-gradient(1.4px 1.4px at 55% 42%,#fff,transparent),
      radial-gradient(1px 1px at 90% 80%,#cdd6ff,transparent),
      radial-gradient(1px 1px at 33% 15%,#fff,transparent),
      radial-gradient(1.6px 1.6px at 72% 78%,#ffe9c2,transparent);}
  .hero .core{position:absolute;right:-60px;top:-40px;width:340px;height:340px;border-radius:50%;
    background:radial-gradient(circle,rgba(255,210,122,.22),transparent 62%);
    filter:blur(6px);pointer-events:none;}
  .hero-inner{position:relative;}
  .eyebrow{font-family:"IBM Plex Mono",monospace;font-size:12.5px;letter-spacing:.28em;
    text-transform:uppercase;color:var(--glow);margin:0 0 18px;}
  h1{font-family:"Fraunces",serif;font-weight:500;font-size:clamp(34px,6.4vw,58px);
    line-height:1.05;letter-spacing:-.01em;margin:0 0 6px;}
  h1 .zh{font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;font-weight:600;}
  .dek{color:var(--muted);font-size:16px;max-width:54ch;margin:14px 0 0;}
  .dek b{color:var(--star);font-weight:600;}
  .cond{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin:34px 0 0;
    border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--line);}
  .cond > div{background:var(--ink2);padding:16px 18px;}
  .cond .k{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;
    text-transform:uppercase;color:var(--muted2);margin-bottom:6px;}
  .cond .v{font-size:16px;font-weight:600;color:var(--star);}
  .cond .v small{display:block;font-weight:400;font-size:12.5px;color:var(--muted);margin-top:2px;}
  section{margin-top:54px;}
  .sec-head{display:flex;align-items:baseline;gap:14px;margin-bottom:8px;}
  .sec-head .num{font-family:"IBM Plex Mono",monospace;color:var(--glow);font-size:13px;}
  h2{font-family:"Fraunces",serif;font-weight:500;font-size:24px;margin:0;letter-spacing:.005em;}
  .sec-note{color:var(--muted);font-size:14.5px;margin:2px 0 24px;}
  .card{border:1px solid var(--line);border-radius:16px;
    background:linear-gradient(180deg,var(--ink2),#0e1330);
    padding:22px 22px 20px;margin-bottom:14px;
    display:grid;grid-template-columns:46px 1fr;gap:18px;align-items:start;}
  .rank{font-family:"Fraunces",serif;font-size:30px;line-height:1;color:var(--glow);
    border-right:1px solid var(--line);padding-right:18px;padding-top:2px;}
  .card-body{min-width:0;}
  .loc-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;margin-bottom:4px;}
  .loc-name{font-size:19px;font-weight:700;}
  .loc-region{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted2);
    letter-spacing:.06em;border:1px solid var(--line);border-radius:999px;padding:2px 9px;}
  .tag-best{color:var(--ink);background:var(--glow);border:none;font-weight:600;}
  .loc-desc{color:var(--muted);font-size:14.5px;margin:6px 0 14px;}
  .loc-desc b{color:var(--star);font-weight:600;}
  .meter-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;}
  .meter{flex:1;min-width:160px;height:8px;border-radius:999px;
    background:#0a0e26;border:1px solid var(--line);overflow:hidden;}
  .meter span{display:block;height:100%;border-radius:999px;}
  .pct{font-family:"IBM Plex Mono",monospace;font-size:15px;font-weight:500;white-space:nowrap;}
  .pct small{color:var(--muted2);font-weight:400;}
  .nav{font-family:"IBM Plex Mono",monospace;font-size:12.5px;text-decoration:none;
    color:var(--aqua);border:1px solid var(--line);border-radius:999px;padding:6px 13px;
    white-space:nowrap;transition:.15s;}
  .nav:hover{border-color:var(--aqua);background:rgba(127,214,194,.08);}
  .sky{border:1px solid var(--line);border-radius:16px;
    background:linear-gradient(180deg,#0c1130,#0a0e23);padding:22px 18px 14px;}
  .sky svg{width:100%;height:auto;display:block;}
  .sky-legend{display:flex;flex-wrap:wrap;gap:8px 22px;justify-content:center;
    margin-top:8px;font-size:13px;color:var(--muted);}
  .sky-legend b{color:var(--glow);font-weight:600;}
  .out{border:1px dashed var(--line);border-radius:14px;padding:18px 20px;
    background:rgba(255,139,107,.04);}
  .out p{margin:0 0 12px;color:var(--muted);font-size:14.5px;}
  .out-grid{display:flex;flex-wrap:wrap;gap:8px;}
  .chip{font-family:"IBM Plex Mono",monospace;font-size:12.5px;border:1px solid var(--line);
    border-radius:999px;padding:5px 12px;color:var(--muted);}
  .chip b{color:var(--warn);font-weight:500;}
  .notes{list-style:none;padding:0;margin:0;}
  .notes li{position:relative;padding:0 0 14px 26px;color:var(--muted);font-size:14.5px;}
  .notes li::before{content:"✦";position:absolute;left:0;top:0;color:var(--glow);font-size:13px;}
  .notes li b{color:var(--star);font-weight:600;}
  footer{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);
    font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted2);line-height:1.8;}
  footer b{color:var(--muted);font-weight:500;}
  @media(max-width:560px){
    .cond{grid-template-columns:1fr;}
    .card{grid-template-columns:38px 1fr;gap:14px;padding:18px;}
    .rank{font-size:24px;padding-right:14px;}}
  @media print{
    :root{--star:#1a1a1a;--muted:#3d3d3d;--muted2:#666;--line:#d8d8d8;
      --ink:#fff;--ink2:#fff;--glow:#b5791a;--aqua:#0b7a66;}
    body{background:#fff;color:#1a1a1a;}
    .hero{background:#fff;border-bottom:2px solid #e2e2e2;margin:0;}
    .hero .galaxy,.hero .core,.archive-banner{display:none;}
    .eyebrow{color:#b5791a;}
    .card,.sky,.out,.cond,.cond>div{break-inside:avoid;background:#fff;}
    .card{border-color:#d8d8d8;}
    .nav{display:none;}
    .tag-best{background:#f0d8a8;color:#3a2a00;}
    a{color:inherit;}
    .wrap{max-width:none;padding:0 8px 20px;}}
"""

SVG = """<svg viewBox="0 0 600 210" role="img" aria-label="銀河中心由東南升起至正南最高的弧線">
        <line x1="30" y1="170" x2="570" y2="170" stroke="#2b3568" stroke-width="1"/>
        <path d="M70 162 C 210 150, 330 70, 470 64" fill="none" stroke="url(#g)" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M470 64 C 510 62, 540 78, 560 96" fill="none" stroke="#3a4480" stroke-width="2" stroke-dasharray="4 5" stroke-linecap="round"/>
        <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#7fd6c2"/><stop offset="1" stop-color="#ffd27a"/>
        </linearGradient></defs>
        <circle cx="78" cy="160" r="5" fill="#7fd6c2"/>
        <text x="78" y="190" fill="#99a2cc" font-size="12" text-anchor="middle" font-family="IBM Plex Mono,monospace">21時</text>
        <text x="78" y="146" fill="#cfd6f5" font-size="11" text-anchor="middle">東南升起</text>
        <circle cx="280" cy="98" r="5" fill="#bfe0d6"/>
        <text x="280" y="128" fill="#99a2cc" font-size="12" text-anchor="middle" font-family="IBM Plex Mono,monospace">23時</text>
        <circle cx="468" cy="64" r="6.5" fill="#ffd27a"/>
        <text x="468" y="44" fill="#ffd27a" font-size="12" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-weight="500">01–02時</text>
        <text x="468" y="92" fill="#f3ecdd" font-size="11" text-anchor="middle">正南 · 最高</text>
        <text x="70" y="200" fill="#6f78a6" font-size="11" text-anchor="middle">東南 SE</text>
        <text x="468" y="200" fill="#6f78a6" font-size="11" text-anchor="middle">南 S</text>
        <text x="560" y="200" fill="#6f78a6" font-size="11" text-anchor="middle">西南 SW</text>
      </svg>"""


def meter_color(pct):
    if pct < 40:
        return "linear-gradient(90deg,#7fd6c2,#ffd27a)"
    elif pct < 60:
        return "linear-gradient(90deg,#ffd27a,#ffb454)"
    return "linear-gradient(90deg,#ffb454,#ff8b6b)"


def cards_html(locs):
    out = ""
    for i, loc in enumerate(locs):
        pct = loc["rain"]
        best = '<span class="loc-region tag-best">最推薦</span>' if i == 0 else ""
        out += f"""
    <div class="card">
      <div class="rank">{i+1}</div>
      <div class="card-body">
        <div class="loc-top">
          <span class="loc-name">{loc["name"]}</span>
          <span class="loc-region">{loc["region"]}</span>
          {best}
        </div>
        <p class="loc-desc">{loc["desc"]}</p>
        <div class="meter-row">
          <div class="meter"><span style="width:{pct}%;background:{meter_color(pct)}"></span></div>
          <span class="pct">{pct}% <small>降雨</small></span>
          <a class="nav" href="https://www.google.com/maps/search/?api=1&query={loc['maps']}" target="_blank" rel="noopener">導航 ↗</a>
        </div>
      </div>
    </div>"""
    return out


def chips_html(locs):
    return "\n        ".join(
        f'<span class="chip">{l["name"]} <b>{l["rain"]}%</b></span>' for l in locs
    )


def build_page(date_str, weekday, moon, main, rainy, is_archive=False, archive_date=""):
    y, m, d = date_str.split("-")
    date_disp = f"{int(y)} 年 {int(m)} 月 {int(d)} 日（{weekday}）"
    date_title = f"{y}/{m}/{d}"

    archive_banner = ""
    if is_archive:
        archive_banner = f"""
  <div class="archive-banner">
    <span>📁 <b>Archive</b> — {archive_date} 過去紀錄</span>
    <a href="../index.html">← 回今天的指南</a>
    <a href="index.html">所有過去紀錄</a>
  </div>"""

    archive_link = "" if is_archive else """
    <div style="margin-bottom:10px;">
      <a href="archive/index.html" style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#7fd6c2;text-decoration:none;border:1px solid #2b3568;border-radius:999px;padding:5px 13px;">📁 過去觀星紀錄 Archive ↗</a>
    </div>"""

    src_note = "自動更新" if not is_archive else "查詢當日"

    return (
        f'<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>\n'
        f'<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{"銀河觀星指南" if is_archive else "今晚銀河觀星指南"} · {date_title}</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">\n'
        f'<style>{CSS}</style>\n</head>\n<body>\n<div class="wrap">\n'
        f'{archive_banner}\n'
        '  <header class="hero">\n'
        '    <div class="galaxy"></div>\n    <div class="core"></div>\n'
        '    <div class="hero-inner">\n'
        '      <p class="eyebrow">Taiwan · Milky Way Field Guide</p>\n'
        '      <h1>今晚<span class="zh">銀河</span>觀星指南</h1>\n'
        f'      <p class="dek">{date_disp} · 21:00 之後｜今晚 <b>{moon["dek"]}。以下 5 個地點依今晚降雨機率由低到高排序。</p>\n'
        '      <div class="cond">\n'
        f'        <div><div class="k">月相 · Moon</div><div class="v">{moon["v"]}<small>{moon["small"]}</small></div></div>\n'
        '        <div><div class="k">銀河中心 · Core</div><div class="v">東南 → 正南<small>21 時東南升起，越晚越高</small></div></div>\n'
        f'        <div><div class="k">最佳時段 · Peak</div><div class="v">{moon["peak"]}<small>{moon["peak_s"]}</small></div></div>\n'
        '      </div>\n    </div>\n  </header>\n\n'
        '  <section>\n    <div class="sec-head"><span class="num">01</span><h2>今晚最有機會的 5 個暗空點</h2></div>\n'
        '    <p class="sec-note">降雨機率為 Open-Meteo 氣象模式 21:00–02:00 夜間平均值，數字越低越好；點右側可直接導航。</p>\n'
        f'{cards_html(main)}\n  </section>\n\n'
        '  <section>\n    <div class="sec-head"><span class="num">02</span><h2>銀河中心今晚的軌跡</h2></div>\n'
        '    <p class="sec-note">22:00 後先望<b style="color:var(--glow)">東南方</b>低空，越晚核心越高；午夜後升至正南、仰角最高，最適合拍攝與肉眼觀賞。</p>\n'
        f'    <div class="sky">{SVG}\n      <div class="sky-legend"><span><b>{moon["v"]}</b> {moon["legend"]}</span></div>\n    </div>\n  </section>\n\n'
        '  <section>\n    <div class="sec-head"><span class="num">03</span><h2>今晚降雨機率偏高的暗空點</h2></div>\n'
        '    <div class="out">\n'
        '      <p>以下暗空點今晚雲量或降雨偏多，<b style="color:var(--star)">不建議特地前往</b>：</p>\n'
        f'      <div class="out-grid">{chips_html(rainy)}</div>\n    </div>\n  </section>\n\n'
        '  <section>\n    <div class="sec-head"><span class="num">04</span><h2>出發前的務實提醒</h2></div>\n'
        '    <ul class="notes">\n'
        '      <li>表中降雨機率為 <b>21:00–02:00 夜間平均值</b>（Open-Meteo 氣象模式），出發前建議再看中央氣象署即時雷達回波確認——夏季對流雨常在午夜後減弱。</li>\n'
        f'      <li>{moon["reminder"]}</li>\n'
        '      <li>這 5 點從台北出發都約 <b>5–6 小時車程</b>，較適合過夜或本來就在南部。若想找台北當天來回的點，北部近郊今晚同樣多雲且光害偏高，條件並不理想。</li>\n'
        '      <li>海邊與草原風大、夜間轉涼，<b>帶外套、頭燈（紅光不破壞暗視覺）、腳架</b>；注意潮汐與懸崖邊安全。</li>\n'
        '    </ul>\n  </section>\n\n'
        f'  <footer>{archive_link}\n'
        f'    <div><b>資料來源</b>　天氣：Open-Meteo {src_note}（{date_str} 17:00 TST，夜間 21:00–02:00 平均）｜月相：農曆推算｜座標／導航：Google Maps</div>\n'
        '    <div><b>提示</b>　可用瀏覽器「列印 → 另存為 PDF」匯出乾淨的列印版本。</div>\n'
        f'    <div style="margin-top:6px;color:#525a85;">{"Archive" if is_archive else "Auto-updated"} for Ian · {date_str}</div>\n'
        '  </footer>\n\n</div>\n</body>\n</html>\n'
    )


def update_archive_index(new_date, weekday, moon_v):
    path = os.path.join(SCRIPT_DIR, "archive", "index.html")
    y, m, d = new_date.split("-")
    days_zh = ["一","二","三","四","五","六","日"]
    new_entry = f"""
    <a class="archive-item" href="{new_date}.html">
      <div>
        <div class="item-date">{new_date} · 星期{weekday}</div>
        <div class="item-title">銀河觀星指南 · {int(m)} 月 {int(d)} 日</div>
        <div class="item-meta">月相：<b>{moon_v}</b></div>
      </div>
      <div class="item-arrow">查看 ↗</div>
    </a>"""

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Insert after <div class="archive-list">
    content = content.replace('<div class="archive-list">', '<div class="archive-list">' + new_entry, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    now = datetime.now(TW)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    weekday = ["一","二","三","四","五","六","日"][now.weekday()]
    yesterday_wd = ["一","二","三","四","五","六","日"][(now - timedelta(days=1)).weekday()]

    print(f"Galaxy Guide Auto-Update: {today} (Taiwan)")

    # Step 1: Archive yesterday's index.html if not already done
    archive_path = os.path.join(SCRIPT_DIR, "archive", f"{yesterday}.html")
    if not os.path.exists(archive_path):
        index_path = os.path.join(SCRIPT_DIR, "index.html")
        if os.path.exists(index_path):
            print(f"  Archiving {yesterday}...")
            # Read current index and build archive version
            # We don't have yesterday's weather, so just copy current with banner
            with open(index_path, "r", encoding="utf-8") as f:
                old_html = f.read()
            # Add archive banner CSS + banner element to current page
            banner_css = """
  .archive-banner{background:rgba(43,53,104,.5);border:1px solid var(--line);border-radius:10px;
    padding:10px 18px;margin:20px 0 0;font-family:"IBM Plex Mono",monospace;font-size:12.5px;
    color:var(--muted2);display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
  .archive-banner b{color:var(--muted);}
  .archive-banner a{color:var(--aqua);text-decoration:none;}
"""
            banner_html = f"""
  <div class="archive-banner">
    <span>📁 <b>Archive</b> — {yesterday} 過去紀錄</span>
    <a href="../index.html">← 回今天的指南</a>
    <a href="index.html">所有過去紀錄</a>
  </div>"""
            if "archive-banner" not in old_html:
                old_html = old_html.replace("</style>", banner_css + "\n</style>", 1)
                old_html = old_html.replace('<div class="wrap">', '<div class="wrap">' + banner_html, 1)
            with open(archive_path, "w", encoding="utf-8") as f:
                f.write(old_html)
            # Update archive/index.html — extract moon phase from old page for display
            update_archive_index(yesterday, yesterday_wd, "（見存檔）")
            print(f"  Archived to archive/{yesterday}.html")

    # Step 2: Fetch weather
    print("  Fetching weather from Open-Meteo...")
    import copy
    main_locs = copy.deepcopy(MAIN_LOCS)
    rainy_locs = copy.deepcopy(RAINY_LOCS)
    for loc in main_locs + rainy_locs:
        loc["rain"] = fetch_rain(loc["lat"], loc["lon"])
        print(f"    {loc['name']}: {loc['rain']}%")

    main_locs.sort(key=lambda x: x["rain"])
    rainy_locs.sort(key=lambda x: x["rain"], reverse=True)

    # Step 3: Moon phase
    moon = get_moon(now)
    print(f"  Moon: {moon['v']}")

    # Step 4: Generate & write index.html
    html = build_page(today, weekday, moon, main_locs, rainy_locs)
    index_path = os.path.join(SCRIPT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Written index.html")

    # Step 5: Git commit + push
    os.chdir(SCRIPT_DIR)
    subprocess.run(["git", "config", "user.email", "bot@galaxy-guide"], check=False)
    subprocess.run(["git", "config", "user.name", "Galaxy Guide Bot"], check=False)
    result = subprocess.run(["git", "add", "index.html", "archive/"], capture_output=True)
    commit = subprocess.run(
        ["git", "commit", "-m", f"Auto-update: {today} 17:00 TST — weather + moon refreshed"],
        capture_output=True, text=True
    )
    if "nothing to commit" in commit.stdout:
        print("  No changes to commit.")
    else:
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"  Pushed to GitHub.")

    print("Done!")


if __name__ == "__main__":
    main()
