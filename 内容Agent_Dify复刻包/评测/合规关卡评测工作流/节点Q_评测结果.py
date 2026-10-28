# 节点Q 评测结果（代码执行）——只用于「合规关卡-评测」工作流
# 作用：输入一条现成文案，跑「规则初检 → 合规审核Agent → 终稿复检」，
#       输出规则层是否命中、模型是否修改、终稿是否还有命中，方便统计拦截率和误拦率。
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
        hits.append(f"[{kind}]{word}")

    for pat in rules["极限词"]:
        for m in re.finditer(pat, body):
            add("极限词", m.group(0), m.start())
    for pat in rules["医疗用语"]:
        for m in re.finditer(pat, body):
            add("医疗用语", m.group(0), m.start())
    for cat, pats in rules["功效词"].items():
        if cat in approved_cats:
            continue
        for pat in pats:
            for m in re.finditer(pat, body):
                add("超出批准功效", m.group(0), m.start())
    for pat in rules["竞品对比"]:
        for m in re.finditer(pat, body):
            add("贬低竞品", m.group(0), m.start())
    if prod["资质类型"] != "保健食品":
        for pat in rules["普通食品冒充保健"]:
            for m in re.finditer(pat, body):
                add("普通食品称保健", m.group(0), m.start())
    missing_decl = prod["资质类型"] == "保健食品" and decl not in (text or "")
    return hits, missing_decl


def _section(text, name):
    m = re.search(r"【" + name + r"】\s*([\s\S]*?)(?=\n【[^】]+】|\Z)", text or "")
    return m.group(1).strip() if m else ""


def main(review_text: str, original: str, product_json: str, rules_json: str, hit_count: str, rule_hits: str) -> dict:
    prod = json.loads(product_json)
    rules = json.loads(rules_json)
    decl = rules["保健食品声明"]
    review_text = re.sub(r"<think>[\s\S]*?</think>", "", review_text or "")
    verdict = _section(review_text, "审核结论")
    final = review_text.split("【终稿】", 1)[1].strip() if "【终稿】" in review_text else ""
    if not final:
        final = original or ""
    hits, missing = scan(final, prod, rules)
    auto_fix = False
    if missing:
        final = final.rstrip() + f"（{decl}）"
        auto_fix = True
    result = {
        "规则初检命中": int(hit_count or 0),
        "模型结论": "已修改" if "已修改" in verdict else ("通过" if "通过" in verdict else verdict[:20]),
        "终稿复检命中": len(hits),
        "终稿复检明细": hits,
        "自动补声明": auto_fix,
        "终稿": final,
    }
    changes = _section(review_text, "修改说明") or "无"
    caught = int(hit_count or 0) > 0 or result["模型结论"] == "已修改"
    report = f"""# 合规关卡评测｜{prod['名称']}

**是否判定违规：{'是' if caught else '否'}**　｜　规则初检命中 {result['规则初检命中']} 处　｜　合规审核Agent：{result['模型结论']}　｜　终稿复检命中 {result['终稿复检命中']} 处

## 原文
{original}

## ① 规则初检
{rule_hits}

## ② 合规审核Agent 修改说明
{changes}

## ③ 终稿（已复检{'，已自动补规定声明' if auto_fix else ''}）
{final}

---
评测记录：{json.dumps({k: v for k, v in result.items() if k != '终稿'}, ensure_ascii=False)}
"""
    return {"report": report, "eval_json": json.dumps(result, ensure_ascii=False)}
