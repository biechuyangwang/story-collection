# -*- coding: utf-8 -*-
"""为中国国家地理分类从 Wikimedia Commons 检索并下载开放授权图片。
用法: python3 _fetch_geo_images.py
输出: assets/images/geo/geoXXa.jpg ... + 中国国家地理/图片版权.md
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "images" / "geo"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "StoryCollectionBot/1.0 (educational children stories; github.com/biechuyangwang/story-collection)"}

# 每个故事 2 张图：(slug, 标题, [Commons 搜索词1, 搜索词2])
STORIES = [
    ("01", "珠穆朗玛峰", ["Mount Everest north face", "Everest Base Camp tents Nepal"]),
    ("02", "黄河壶口瀑布", ["Hukou Waterfall", "Yellow River Hukou"]),
    ("03", "长江三峡", ["Three Gorges Yangtze River", "Qutang Gorge"]),
    ("04", "桂林山水", ["Li River Guilin karst", "Guilin landscape"]),
    ("05", "九寨沟", ["Jiuzhaigou valley", "Jiuzhaigou Five Flower Lake"]),
    ("06", "张家界", ["Zhangjiajie mountains", "Zhangjiajie pillar"]),
    ("07", "敦煌月牙泉", ["Crescent Lake Dunhuang", "Mingsha dunes Dunhuang"]),
    ("08", "呼伦贝尔草原", ["Hulunbuir grassland", "Inner Mongolia grassland"]),
    ("09", "塔克拉玛干沙漠", ["Taklamakan Desert", "Taklamakan dunes"]),
    ("10", "海南珊瑚海", ["Sanya beach Hainan", "Wuzhizhou Island Sanya"]),
    ("11", "长白山天池", ["Changbai Mountain Heaven Lake", "Heaven Lake Changbai Shan"]),
    ("12", "稻城亚丁", ["Daocheng Yading", "Yading Nature Reserve"]),
    ("13", "元阳梯田", ["Yuanyang rice terraces", "Hani terraces Yuanyang"]),
    ("14", "茶卡盐湖", ["Chaka Salt Lake", "Chaka lake Qinghai mirror"]),
    ("15", "黄果树瀑布", ["Huangguoshu Waterfall", "Huangguoshu falls Guizhou"]),
    ("16", "故宫", ["Forbidden City Hall of Supreme Harmony", "Forbidden City meridian gate"]),
    ("17", "长城", ["Great Wall Mutianyu", "Jinshanling Great Wall"]),
    ("18", "大熊猫家园", ["Giant Panda eating bamboo", "Giant Panda Sichuan forest"]),
    ("19", "张掖丹霞", ["Zhangye Danxia", "Rainbow mountains Zhangye"]),
    ("20", "丽江玉龙雪山", ["Jade Dragon Snow Mountain", "Lijiang old town"]),
]

BAD = re.compile(
    r"map|diagram|plan|chart|logo|coat|flag|drawing|sketch|painting|portrait|"
    r"hotel|building|street|satellite|landsat|metro|railway|station|airport", re.I)


def api_search(term):
    q = urllib.parse.urlencode({
        "action": "query", "format": "json",
        "generator": "search", "gsrnamespace": "6", "gsrsearch": term,
        "gsrlimit": "10",
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": "1280",
        "iiextmetadatafilter": "Artist|LicenseShortName",
    })
    url = "https://commons.wikimedia.org/w/api.php?" + q
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(20)
                continue
            raise
    return {}


def pick(data):
    """挑选合适的风景图：jpg/png、横幅、够宽、标题无杂词。"""
    pages = data.get("query", {}).get("pages", {})
    cands = []
    for p in pages.values():
        info = (p.get("imageinfo") or [{}])[0]
        title = p.get("title", "")
        if BAD.search(title):
            continue
        w, h = info.get("width", 0), info.get("height", 0)
        if not (1000 <= w and 1.15 <= (w / max(h, 1)) <= 2.4):
            continue
        thumb = info.get("thumburl") or info.get("url")
        if not thumb or not thumb.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
            continue
        meta = info.get("extmetadata", {})
        artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "") or "佚名").strip()
        lic = meta.get("LicenseShortName", {}).get("value", "") or "CC 授权"
        cands.append((p.get("index", 99), {"title": title, "thumb": thumb,
                                           "artist": artist[:60], "license": lic,
                                           "descurl": info.get("descriptionurl", "")}))
    cands.sort(key=lambda x: x[0])
    return [c[1] for c in cands]


def download(url, dest):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest.stat().st_size > 15000
    except Exception as e:
        print(f"    下载失败: {e}")
        return False


def strip(text):
    return text.strip().strip('"').replace("|", "／")[:80]


credits = []
seen_titles = set()
for c in (json.loads((OUT / "credits.json").read_text(encoding="utf-8"))
          if (OUT / "credits.json").exists() else []):
    credits.append(c)
    seen_titles.add(c["title"][:50])
for num, title, terms in STORIES:
    got = len([f for f in ("geo{}a.jpg", "geo{}b.jpg") if (OUT / f.format(num)).exists()])
    for ti, term in enumerate(terms):
        if got >= 2:
            break
        letter = "ab"[got]
        fname = f"geo{num}{letter}.jpg"
        if (OUT / fname).exists():
            continue
        try:
            data = api_search(term)
        except Exception as e:
            print(f"[{num}] 搜索失败 {term}: {e}")
            continue
        for c in pick(data):
            if c["title"][:50] in seen_titles:
                continue
            if download(c["thumb"], OUT / fname):
                got += 1
                seen_titles.add(c["title"][:50])
                credits.append({"file": fname, "story": f"{num}-{title}",
                                "title": strip(c["title"]), "artist": strip(c["artist"]),
                                "license": strip(c["license"]), "url": c["descurl"]})
                print(f"[{num}] {fname} <- {c['title'][:50]} ({c['license']})")
                break
            else:
                (OUT / fname).unlink(missing_ok=True)
        time.sleep(2.5)
    if got < 2:
        print(f"!! [{num}-{title}] 仅获 {got} 张")

(ROOT / "assets" / "images" / "geo" / "credits.json").write_text(
    json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n共下载 {len(credits)} 张，credits.json 已写入")
