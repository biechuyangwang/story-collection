# -*- coding: utf-8 -*-
"""全库引号规范化：对话 → “”，特指 → 「」，内层引用 → ‘’。
用法:
  python3 _quote_convert.py --dry   # 干跑，只打印分桶统计与样例
  python3 _quote_convert.py         # 实际写入
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = (".git", "合集打印版", "docs", "assets")

DRY = "--dry" in sys.argv

# 说话引导词（引号前紧邻，允许隔一个冒号/逗号）
SAY_RE = re.compile(
    r"(说|说道|问道|答道|喊道|叫道|笑道|哭道|叹道|念道|回答|回应|嘀咕|嘟囔|喃喃|"
    r"欢呼|惊呼|感叹|心想|想着|想|自言自语|商量|哄笑|追问|反问|接着说|又说|大喊|"
    r"大叫|安慰|鼓励|提醒|叮嘱|吩咐|开玩笑|脱口而出|低声|大声|小声|说)$"
)
# 特指引导（引号前紧邻，短术语语境）
TERM_RE = re.compile(
    r"(是|叫|称作|称为|尊称|人称|叫作|叫做|名叫|名为|就是|所谓|这个|一个|"
    r"写着|题着|的)$"
)
SENT_PUNCT = re.compile(r"[。！？…；]")


def classify(before, inner, after, prev_tail):
    """返回 'dial' 或 'term'。"""
    b = before.rstrip()
    a = after.lstrip()
    in_dial_like = bool(SENT_PUNCT.search(inner)) or len(inner) > 10

    # 1) 引导词 + 可选冒号/逗号 → 对话
    m = SAY_RE.search(b[-8:]) if b else None
    if m and (len(b) == m.end() or b[m.end():] in ("：", ":", "，", ",")):
        return "dial"
    # 2) 特指引导词 + 短内容无句末标点 → 特指
    if TERM_RE.search(b[-6:]) if b else False:
        if not SENT_PUNCT.search(inner) and len(inner) <= 12:
            return "term"
    # 3) 整行就是引号内容 → 对话（对话轮次）
    if b.strip() in ("", ">", "-", "*") and a.strip() == "":
        return "dial"
    # 4) 行首引号，内含句末标点 → 对话
    if b.strip() == "" and SENT_PUNCT.search(inner):
        return "dial"
    # 5) 行首引号，短无标点：上一行以特指语境结尾 → 特指；否则对话
    if b.strip() == "":
        if prev_tail and TERM_RE.search(prev_tail[-4:]):
            return "term"
        return "dial"
    # 6) 行中短引号、无句末标点 → 特指
    if not in_dial_like:
        return "term"
    # 7) 其余（行中长引号/含标点）→ 对话
    return "dial"


def pair_quotes(line):
    """把一行内的直引号按奇偶配对；返回 [(start, end, inner)]。"""
    idx = [m.start() for m in re.finditer(r"\"", line)]
    if len(idx) % 2 != 0:
        return None
    return [(idx[i], idx[i + 1]) for i in range(0, len(idx), 2)]


def convert_inner_quotes(inner):
    """内层 '...' → ‘...’（按奇偶配对）。"""
    idx = [m.start() for m in re.finditer(r"'", inner)]
    if len(idx) % 2 != 0:
        return inner, len(idx)
    out, last, pairs = [], 0, 0
    for i in range(0, len(idx), 2):
        out.append(inner[last:idx[i]] + "\u2018")
        out.append(inner[idx[i] + 1:idx[i + 1]] + "\u2019")
        last = idx[i + 1] + 1
        pairs += 1
    out.append(inner[last:])
    return "".join(out), pairs


def convert_file(path, report):
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    new_lines = []
    prev_tail = ""
    for line in lines:
        pairs = pair_quotes(line)
        if pairs is None:
            report["odd_lines"].append(f"{path.relative_to(ROOT)}: {line[:60]}")
            new_lines.append(line)
            prev_tail = line.rstrip()[-6:]
            continue
        if not pairs:
            new_lines.append(line)
            prev_tail = line.rstrip()[-6:]
            continue
        out, last = [], 0
        for start, end in pairs:
            inner = line[start + 1: end]
            before = line[:start]
            after = line[end + 1:]
            kind = classify(before, inner, after, prev_tail)
            report[kind] += 1
            report.setdefault(f"ex_{kind}", []).append(
                f"{path.name}: {before[-14:]}\"{inner[:24]}\"")
            inner2, npairs = convert_inner_quotes(inner)
            report["inner_quotes"] += npairs
            if kind == "dial":
                rep = "\u201c" + inner2 + "\u201d"
            else:
                rep = "\u300c" + inner2 + "\u300d"
            out.append(line[last:start] + rep)
            last = end + 1
        out.append(line[last:])
        new_lines.append("".join(out))
        prev_tail = line.rstrip()[-6:]
    new_text = "\n".join(new_lines)
    if new_text != text:
        report["changed_files"] += 1
        if not DRY:
            path.write_text(new_text, encoding="utf-8")


def main():
    report = {"dial": 0, "term": 0, "inner_quotes": 0, "changed_files": 0,
              "odd_lines": [], "ex_dial": [], "ex_term": []}
    files = [p for p in sorted(ROOT.rglob("*.md"))
             if not any(s in str(p) for s in SKIP_DIRS)]
    for p in files:
        convert_file(p, report)

    mode = "DRY" if DRY else "APPLIED"
    print(f"[{mode}] 对话 “”: {report['dial']} ｜ 特指 「」: {report['term']} ｜ "
          f"内层 ‘’: {report['inner_quotes']} ｜ 改动文件: {report['changed_files']}")
    if report["odd_lines"]:
        print(f"\n!! 奇数引号行（未处理 {len(report['odd_lines'])} 行）:")
        for e in report["odd_lines"][:10]:
            print("  ", e)
    import random
    random.seed(42)
    for kind, label in (("ex_dial", "对话样例"), ("ex_term", "特指样例")):
        print(f"\n--- {label}（随机 15 / {len(report[kind])}）---")
        for e in random.sample(report[kind], min(15, len(report[kind]))):
            print("  ", e)


if __name__ == "__main__":
    main()
