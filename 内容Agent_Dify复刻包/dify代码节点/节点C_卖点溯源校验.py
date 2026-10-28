# 节点C 卖点溯源校验（代码执行）
# 作用：逐条检查「商品理解Agent」给出的卖点——
#   1. 必须引用编号，且编号真实存在（没有依据就不写）；
#   2. 卖点里不能出现超出「批准功效」的功效词（买家说"感冒少了"不等于商品能宣称增强免疫力）；
#   3. 不能出现医疗用语。
# 只有通过的卖点才交给「内容生成Agent」，从源头拦住编造功效。
import json
import re


def _parse(text):
    t = (text or "").strip()
    t = re.sub(r"^```(json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", t)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _effect_hits(text, rules, approved_cats):
    hits = []
    for cat, pats in rules["功效词"].items():
        if cat in approved_cats:
            continue
        for pat in pats:
            m = re.search(pat, text)
            if m:
                hits.append((cat, m.group(0)))
                break
    return hits


def _medical_hits(text, rules):
    out = []
    for pat in rules["医疗用语"]:
        m = re.search(pat, text)
        if m:
            out.append(m.group(0))
    return out


def main(agent_text: str, product_json: str, rules_json: str) -> dict:
    prod = json.loads(product_json)
    rules = json.loads(rules_json)
    source = prod["依据"]
    approved_cats = [rules["批准功效映射"].get(x, x) for x in prod["批准功效"]]

    agent_text = re.sub(r"<think>[\s\S]*?</think>", "", agent_text or "")
    data = _parse(agent_text)
    if not data or not isinstance(data.get("卖点"), list):
        return {
            "verified_points": "（商品理解Agent输出格式异常，未能解析卖点）",
            "trace_table": "商品理解Agent输出格式异常，原文：\n" + (agent_text or "")[:800],
            "check_summary": "卖点解析失败",
        }

    kept, dropped = [], []
    for item in data["卖点"]:
        point = str(item.get("卖点", "")).strip()
        refs = item.get("依据") or []
        if isinstance(refs, str):
            refs = re.findall(r"P\d{2}-[参评]\d+", refs)
        refs = [r.strip() for r in refs if str(r).strip()]
        if not point:
            continue
        reason = ""
        if not refs:
            reason = "没有标依据"
        else:
            bad = [r for r in refs if r not in source]
            if bad:
                reason = "引用的编号不存在：" + "、".join(bad)
        if not reason:
            eh = _effect_hits(point, rules, approved_cats)
            if eh:
                reason = "超出批准功效：" + "、".join(f"「{w}」属于{c}" for c, w in eh)
        if not reason:
            mh = _medical_hits(point, rules)
            if mh:
                reason = "医疗用语：" + "、".join(mh)
        if reason:
            dropped.append((point, refs, reason))
        else:
            kept.append((point, refs))

    crowd = data.get("人群") or []
    crowd_lines = []
    for c in crowd:
        if isinstance(c, dict):
            crowd_lines.append(f"- {c.get('人群', '')}（依据：{'、'.join(c.get('依据') or [])}）")
        else:
            crowd_lines.append(f"- {c}")

    vp = []
    for i, (pt, refs) in enumerate(kept, 1):
        vp.append(f"卖点{i}：{pt}（依据：{'、'.join(refs)}）")
    verified_points = "\n".join(vp) if vp else "（没有通过校验的卖点）"
    if crowd_lines:
        verified_points += "\n\n目标人群：\n" + "\n".join(crowd_lines)

    tbl = ["| 卖点 | 依据编号 | 依据原文 | 结果 |", "|---|---|---|---|"]
    for pt, refs in kept:
        src = "；".join(source.get(r, "") for r in refs)
        tbl.append(f"| {pt} | {'、'.join(refs)} | {src} | ✅ 采用 |")
    for pt, refs, reason in dropped:
        src = "；".join(source.get(r, "（不存在）") for r in refs) if refs else "—"
        tbl.append(f"| {pt} | {'、'.join(refs) or '—'} | {src} | ❌ 拦截：{reason} |")

    summary = f"商品理解Agent共提炼 {len(kept) + len(dropped)} 条卖点，采用 {len(kept)} 条，拦截 {len(dropped)} 条"
    return {"verified_points": verified_points, "trace_table": "\n".join(tbl), "check_summary": summary}
