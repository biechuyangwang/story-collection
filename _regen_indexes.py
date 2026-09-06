# -*- coding: utf-8 -*-
"""按磁盘实际文件重新生成各分类索引.md。
用法: python3 _regen_indexes.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://biechuyangwang.github.io/story-collection/"

CATS = [
    ("睡前故事", "🌙", ["寓言", "神话", "童话"]),
    ("电台故事", "🎧", []),
    ("成语故事", "📜", []),
    ("励志故事", "🌟", []),
    ("反转故事", "🌀", []),
    ("节日故事", "🎉", ["春节", "小年", "元宵", "清明", "端午", "七夕", "中秋", "重阳", "冬至", "腊八",
                    "二月二", "三月三", "中元", "寒衣", "下元"]),
    ("科幻故事", "🚀", []),
    ("诗词故事", "🖋️", []),
    ("科学故事", "🔬", []),
    ("节气故事", "🌾", []),
    ("名著故事", "🐒", ["西游记"]),
]

INTRO = {
    "睡前故事": "温柔舒缓，有晚安收尾，读着读着就睡着了。",
    "电台故事": "深夜 FM，给大人的心理按摩。",
    "成语故事": "成语背后的经典小故事：警醒 / 发奋 / 历史。",
    "励志故事": "名人轶事与励志寓言，坚持、勇气、勤奋。",
    "反转故事": "欧亨利式结局，意料之外、情理之中。",
    "节日故事": "应景故事包：春节 / 小年 / 元宵 / 清明 / 端午 / 七夕 / 中秋 / 重阳 / 冬至 / 腊八 等。",
    "科幻故事": "原创儿童科幻：月亮、机器人、星空与时间。",
    "诗词故事": "经典诗词背后的故事，读诗也读人。",
    "科学故事": "科学发现与发明背后的趣味故事。",
    "节气故事": "二十四节气：物候、农事与应景小故事，跟着季节过日子。",
    "名著故事": "经典名著的儿童版章节故事，从西游记开始。",
}


def meta_line(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for ln in text.splitlines():
        if ln.startswith(">"):
            pieces = [p.strip().strip("*").strip()
                      for p in re.split(r"[｜|]", ln.lstrip("> ").strip()) if p.strip()]
            return "｜".join(pieces)
    return ""


def table(files):
    rows = ["| # | 篇目 | 信息 |", "|---|------|------|"]
    for i, f in enumerate(files, 1):
        info = meta_line(f).replace("|", "／") or "—"
        rows.append(f"| {i} | [{f.stem.split('-', 1)[-1]}]({f.name}) | {info} |")
    return "\n".join(rows)


def main():
    grand = 0
    for cat, icon, subs in CATS:
        base = ROOT / cat
        out = [f"# {icon} {cat}索引", "", INTRO[cat], "",
               f"> 在线阅读：[{SITE}]({SITE})", ""]
        n_cat = 0
        if subs:
            for sub in subs:
                files = sorted((base / sub).glob("[0-9]*.md"))
                n_cat += len(files)
                if files:
                    out += [f"## {sub}（{len(files)} 篇）", "", table(files), ""]
        else:
            files = sorted(base.glob("[0-9]*.md")) + sorted(base.glob("第*.md"))
            files = [f for f in files if f.name != "索引.md"]
            n_cat = len(files)
            out += [f"共 {n_cat} 篇", "", table(files), ""]
        grand += n_cat
        base.mkdir(parents=True, exist_ok=True)
        (base / "索引.md").write_text("\n".join(out), encoding="utf-8")
        print(f"{cat}: {n_cat} 篇 → 索引.md")
    print(f"合计 {grand} 篇")


if __name__ == "__main__":
    main()
