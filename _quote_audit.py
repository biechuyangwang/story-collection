# -*- coding: utf-8 -*-
"""审计全库直引号用法：统计对话与特指两类引号的规模与判别特征。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = (".git", "合集打印版", "docs", "assets")

SAY = ("说", "道", "问", "答", "喊", "叫", "回答", "问道", "喊道", "叫道",
       "嘀咕", "嘟囔", "喃喃", "欢呼", "惊呼", "叹道", "笑道", "哭道", "念",
       "念叨", "自言自语", "心想", "商量", "小声说", "大声说", "接着说", "又说")

PAIR = re.compile(r"\"([^\"\n]{1,300}?)\"")

stats = Counter = {"dialogue": 0, "term": 0, "ambiguous": 0, "total": 0}
dial_ex, term_ex, amb_ex = [], [], []

for p in sorted(ROOT.rglob("*.md")):
    if any(s in str(p) for s in SKIP) or p.name in ("README.md", "索引.md"):
        continue
    text = p.read_text(encoding="utf-8")
    for m in PAIR.finditer(text):
        inner = m.group(1)
        before = text[max(0, m.start() - 4): m.start()]
        stats["total"] += 1

        is_say_intro = any(before.endswith(w) for w in SAY) or (
            before.endswith("：") and any(before[:-1].endswith(w) for w in SAY))
        has_sent_punct = bool(re.search(r"[！？。…，、；]", inner))
        short = len(inner) <= 8

        if is_say_intro:
            stats["dialogue"] += 1
            if len(dial_ex) < 5:
                dial_ex.append(f"…{before}\"{inner[:20]}\"")
        elif short and not has_sent_punct:
            stats["term"] += 1
            if len(term_ex) < 10:
                term_ex.append(f"…{before}\"{inner}\"")
        else:
            stats["ambiguous"] += 1
            if len(amb_ex) < 10:
                amb_ex.append(f"…{before}\"{inner[:36]}\"")

print(f"引号对总数: {stats['total']}")
t = stats["total"]
print(f"  A. 对话（紧跟说/道/问类引导词或冒号）: {stats['dialogue']} ({stats['dialogue']*100//t}%)")
print(f"  B. 特指（短于8字、句内无标点、无引导词）: {stats['term']} ({stats['term']*100//t}%)")
print(f"  C. 规则外（引导词缺失，多为对话漏了引导词）: {stats['ambiguous']} ({stats['ambiguous']*100//t}%)")
print("\n--- B 特指示例 ---")
for e in term_ex:
    print(" ", e)
print("\n--- C 规则外示例 ---")
for e in amb_ex:
    print(" ", e)

# 单引号与孤立弯引号上下文
print("\n--- ASCII 单引号上下文（前 8 处）---")
n = 0
for p in sorted(ROOT.rglob("*.md")):
    if any(s in str(p) for s in SKIP) or p.name in ("README.md", "索引.md"):
        continue
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r".{0,20}'[^'\n]{1,40}'.{0,10}", text):
        if n < 8:
            print(" ", f"{p.name}: {m.group(0)}")
        n += 1
print(f"  共 {n} 处")
