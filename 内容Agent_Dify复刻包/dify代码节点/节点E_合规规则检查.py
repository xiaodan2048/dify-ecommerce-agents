# 节点E 合规规则检查（代码执行）
# 作用：对「内容生成Agent」的初稿做确定性的规则扫描：
#   广告法极限词、医疗用语、超出批准功效的功效词、贬低竞品、普通食品冒充保健品、保健食品缺少规定声明。
# 规则能判的交给规则（稳定、可解释、零成本）；规则判不了的暗示和夸大，再交给「合规审核Agent」。
import json
import re


def scan(text, prod, rules):
    hits = []
    decl = rules["保健食品声明"]
    body = (text or "").replace(decl, "")
    if prod["资质类型"] == "保健食品":
        for ph in rules.get("法定用语", []):
            body = body.replace(ph, "")
    approved_cats = [rules["批准功效映射"].get(x, x) for x in prod["批准功效"]]

    spans = []

    def add(kind, word, pos):
        end = pos + len(word)
        for a, b in spans:
            if pos < b and end > a:
                return
        spans.append((pos, end))
        s = max(0, pos - 12)
        e = min(len(body), pos + len(word) + 12)
        ctx = body[s:e].replace("\n", " ")
        hits.append({"类型": kind, "命中": word, "上下文": ctx})

    for pat in rules["极限词"]:
        for m in re.finditer(pat, body):
            add("广告法极限词", m.group(0), m.start())
    for pat in rules["医疗用语"]:
        for m in re.finditer(pat, body):
            add("医疗用语", m.group(0), m.start())
    for cat, pats in rules["功效词"].items():
        if cat in approved_cats:
            continue
        for pat in pats:
            for m in re.finditer(pat, body):
                add(f"超出批准功效（{cat}）", m.group(0), m.start())
    for pat in rules["竞品对比"]:
        for m in re.finditer(pat, body):
            add("贬低竞品", m.group(0), m.start())
    if prod["资质类型"] != "保健食品":
        for pat in rules["普通食品冒充保健"]:
            for m in re.finditer(pat, body):
                add("普通食品不得称保健品", m.group(0), m.start())
    missing_decl = prod["资质类型"] == "保健食品" and decl not in (text or "")
    return hits, missing_decl


def fmt(hits, missing_decl, decl):
    lines = []
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. [{h['类型']}] 「{h['命中']}」… {h['上下文']} …")
    if missing_decl:
        lines.append(f"{len(hits) + 1}. [缺少规定声明] 保健食品内容必须包含「{decl}」")
    return "\n".join(lines) if lines else "无命中"


def main(draft: str, product_json: str, rules_json: str) -> dict:
    prod = json.loads(product_json)
    rules = json.loads(rules_json)
    draft = re.sub(r"<think>[\s\S]*?</think>", "", draft or "")
    hits, missing = scan(draft, prod, rules)
    n = len(hits) + (1 if missing else 0)
    return {"rule_hits": fmt(hits, missing, rules["保健食品声明"]), "hit_count": str(n)}
