# 节点G 终稿复检与报告组装（代码执行）
# 作用：合规审核Agent改完以后，再用同一套规则扫一遍终稿（模型改过的东西也要验）。
#   - 保健食品缺少规定声明：自动补上；
#   - 其他规则仍有命中：标记「需人工处理」，不自动放行；
# 最后把终稿、卖点溯源表、合规记录组装成一份交给设计师 / 品牌部的报告。
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
        hits.append({"类型": kind, "命中": word, "上下文": body[s:e].replace("\n", " ")})

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


def _section(text, name):
    m = re.search(r"【" + name + r"】\s*([\s\S]*?)(?=\n【[^】]+】|\Z)", text or "")
    return m.group(1).strip() if m else ""


def main(review_text: str, draft: str, product_json: str, rules_json: str,
         trace_table: str, check_summary: str, rule_hits: str, hit_count: str) -> dict:
    prod = json.loads(product_json)
    rules = json.loads(rules_json)
    decl = rules["保健食品声明"]

    review_text = re.sub(r"<think>[\s\S]*?</think>", "", review_text or "")
    draft = re.sub(r"<think>[\s\S]*?</think>", "", draft or "")
    final = review_text.split("【终稿】", 1)[1].strip() if "【终稿】" in (review_text or "") else ""
    used_fallback = False
    if not final:
        final = draft or ""
        used_fallback = True
    verdict = _section(review_text, "审核结论") or "（未给出）"
    changes = _section(review_text, "修改说明") or "无"

    hits, missing = scan(final, prod, rules)
    auto_fix = ""
    if missing:
        final = final.rstrip() + f"\n\n（{decl}）"
        auto_fix = f"终稿缺少保健食品规定声明，已自动补上「{decl}」"

    if hits:
        status = f"⚠️ 需人工处理：终稿复检仍有 {len(hits)} 处命中"
        recheck = "\n".join(f"- [{h['类型']}] 「{h['命中']}」… {h['上下文']} …" for h in hits)
    else:
        status = "✅ 可交付设计师精修"
        recheck = "无命中"
    if used_fallback:
        status = "⚠️ 需人工处理：合规审核Agent未按格式返回终稿，以下为未审核初稿"

    report = f"""# 内容Agent 输出｜{prod['名称']}｜{prod['平台']}

**状态：{status}**

资质：{prod['资质类型']}｜批准功效：{('、'.join(prod['批准功效'])) or '无'}
运营补充要求：{prod['运营补充要求'] or '无'}

---

## 一、终稿

{final}

---

## 二、卖点溯源表

{check_summary}

{trace_table}

---

## 三、合规审核记录

**① 规则初检（初稿）：命中 {hit_count} 处**

{rule_hits}

**② 合规审核Agent：{verdict}**

{changes}

**③ 终稿规则复检：** {recheck}
{('**自动修正：** ' + auto_fix) if auto_fix else ''}

---
流程：商品理解Agent → 卖点溯源校验（代码）→ 内容生成Agent → 合规规则检查（代码）→ 合规审核Agent → 终稿复检（代码）→ 设计师精修 → 品牌部审核
"""
    return {"report": report, "status": status}
