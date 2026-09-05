# -*- coding: utf-8 -*-
"""扫描故事库 Markdown，生成前端可用的 docs/data.json。
用法: python3 build_site.py
"""
import json
import re
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "data.json"

CATS = [
    {"id": "睡前故事", "icon": "🌙", "name": "睡前故事",
     "desc": "温柔舒缓，有晚安收尾，读着读着就睡着了",
     "subs": ["寓言", "神话", "童话"]},
    {"id": "电台故事", "icon": "🎧", "name": "电台故事",
     "desc": "深夜 FM，给大人的心理按摩", "subs": []},
    {"id": "成语故事", "icon": "📜", "name": "成语故事",
     "desc": "成语背后的经典小故事：警醒 / 发奋 / 历史", "subs": []},
    {"id": "励志故事", "icon": "🌟", "name": "励志故事",
     "desc": "名人轶事与励志寓言，坚持、勇气、勤奋", "subs": []},
    {"id": "反转故事", "icon": "🌀", "name": "反转故事",
     "desc": "欧亨利式结局，意料之外、情理之中", "subs": []},
    {"id": "节日故事", "icon": "🎉", "name": "节日故事",
     "desc": "应景故事包：春节 / 小年 / 元宵 / 清明 / 端午 / 七夕 / 中秋 / 重阳 / 冬至 / 腊八",
     "subs": ["春节", "小年", "元宵", "清明", "端午", "七夕", "中秋", "重阳", "冬至", "腊八"]},
    {"id": "科幻故事", "icon": "🚀", "name": "科幻故事",
     "desc": "原创儿童科幻：月亮、机器人、星空与时间", "subs": []},
    {"id": "诗词故事", "icon": "🖋️", "name": "诗词故事",
     "desc": "经典诗词背后的故事，读诗也读人", "subs": []},
    {"id": "科学故事", "icon": "🔬", "name": "科学趣味故事",
     "desc": "科学发现与发明背后的趣味故事", "subs": []},
]

ENDING_PAT = re.compile(r"\*\*(晚安小结|小启示)\*\*[：:]\s*")


def parse_file(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()

    title = ""
    for ln in lines:
        if ln.startswith("# "):
            title = ln[2:].strip()
            break

    # 正文内容去掉首行标题（页面头部已单独渲染）
    content_lines = []
    title_seen = False
    for ln in lines:
        if not title_seen and ln.startswith("# "):
            title_seen = True
            continue
        content_lines.append(ln)
    text = "\n".join(content_lines).strip()

    # 结尾段（晚安小结 / 小启示）及其后的内容
    ending_label, ending = "", ""
    m = ENDING_PAT.search(text)
    body_md = text
    tail = text
    if m:
        body_md = text[: m.start()].strip()
        tail = text[m.end():].strip()
        ending_label = m.group(1)
        ending = tail
        # 节日小卡片（引用块）从 ending 中拆出，放回正文块之后单独渲染
        card = ""
        card_m = re.search(r"(> \*\*节日小卡片\*\*[\s\S]*)$", ending)
        if card_m:
            card = card_m.group(1).strip()
            ending = ending[: card_m.start()].strip()
    else:
        card = ""

    # 元信息行（开头的 > 引用）
    meta = {}
    body_first = None
    for i, ln in enumerate(lines):
        if ln.startswith(">"):
            for piece in re.split(r"[｜|]", ln.lstrip("> ").strip()):
                piece = piece.strip().strip("*").strip()
                mm = re.match(r"([^：:]+)[：:]\s*(.+)", piece)
                if mm and mm.group(1).strip() not in ("", "出处简洁"):
                    key = mm.group(1).strip().strip("*").strip()
                    val = mm.group(2).strip().strip("*").strip()
                    if key in ("出处", "成语含义", "主题", "适读年龄", "朗读时长", "时长",
                               "适合场景", "人物与出处", "类型", "成语出处", "诗词", "作者",
                               "人物", "发现", "知识点"):
                        meta[key] = val
        elif ln.strip() and not ln.startswith("#") and body_first is None:
            body_first = i
            break

    # 纯文本（摘要 / 搜索 / TTS）
    plain = re.sub(r"[#>*`\-\|]", "", body_md)
    plain = re.sub(r"\s+", "", plain)
    excerpt = plain[:80] + ("…" if len(plain) > 80 else "")

    return {
        "title": title,
        "meta": meta,
        "excerpt": excerpt,
        "endingLabel": ending_label,
        "ending": ending,
        "card": card,
        "content": body_md,
        "plain": plain,
    }


def main():
    stories = []
    total = 0
    for cat in CATS:
        base = ROOT / cat["id"]
        files = []
        if cat["subs"]:
            for sub in cat["subs"]:
                files.extend(sorted((base / sub).glob("[0-9]*.md")))
        else:
            files.extend(sorted(base.glob("[0-9]*.md")))
            files.extend(sorted(base.glob("第*.md")))
        for f in files:
            info = parse_file(f)
            slug = f.stem
            sid = f"{cat['id']}/{slug}" if not cat["subs"] else f"{cat['id']}/{f.parent.name}/{slug}"
            stories.append({
                "id": sid,
                "cat": cat["id"],
                "sub": f.parent.name if cat["subs"] else "",
                "num": slug.split("-")[0],
                "title": info["title"],
                "meta": info["meta"],
                "excerpt": info["excerpt"],
                "endingLabel": info["endingLabel"],
                "ending": info["ending"],
                "card": info["card"],
                "content": info["content"],
                "plain": info["plain"][:1200],
            })
            total += 1

    data = {
        "generatedAt": time.strftime("%Y-%m-%d"),
        "total": total,
        "categories": CATS,
        "stories": stories,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"OK 生成 {OUT}（共 {total} 篇，{OUT.stat().st_size // 1024} KB）")


if __name__ == "__main__":
    main()
