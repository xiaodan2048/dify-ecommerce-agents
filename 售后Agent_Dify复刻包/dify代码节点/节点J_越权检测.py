# ============================================================
# 用在：主流程「J 越权检测」（「M 越权检测2」用同一份代码）
# 输入变量（在节点「输入变量」里逐个添加，名字必须一模一样）：
#   text ← I售后Agent/text（M 节点里改成 L兜底回复/text）
#   order_id ← A会话预处理/order_id
# 输出变量（在节点「输出变量」里添加，名字和类型必须一模一样）：
#   answer（String）
#   hit（String）
#   hit_words（String）
# 用法：全选本文件（Cmd+A）→ 复制 → 在 Dify 代码框里全选后粘贴覆盖
# ============================================================
import json
import re
from datetime import datetime, timedelta

# 演示用的「现在」。固定住时间，评测结果才能复现；想用真实时间可改成 datetime.now() 的格式化字符串
DEMO_NOW = "2026-10-26 14:00"

ORDERS = {}
# ---- 公共函数 ----
def _t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M") if s else None


NOW = _t(DEMO_NOW)


def _fmt(dt):
    return dt.strftime("%m月%d日 %H:%M")


def _find(order_id, buyer_id, shop):
    """按 订单号 + 买家ID + 店铺 查订单。三者对不上一律当作"没查到"，不泄露别人的订单是否存在。"""
    oid = (order_id or "").strip().upper()
    if not oid:
        return None, "NO_ORDER_ID"
    o = ORDERS.get(oid)
    if (not o) or o["buyer_id"] != (buyer_id or "").strip() or o["shop"] != (shop or "").strip():
        return None, "ORDER_NOT_FOUND"
    return o, None


def _ticket(order_id, ticket_type):
    """生成演示用工单号（同一订单同一类型得到同一个号，方便复现）。"""
    s = (order_id or "NA") + ticket_type
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) % 1000000
    return "TK" + NOW.strftime("%m%d") + str(h).zfill(6)


# ---- 本节点逻辑 ----
RISK = [r"补偿", r"赔偿", r"赔付", r"赔(您|你)", r"红包", r"返现", r"优惠券", r"代金券", r"无门槛",
        r"\d+(\.\d+)?\s*(元|块)[^。，,！!]{0,6}(补|赔|返|送)", r"(补|赔|返|送)[^。，,！!]{0,6}\d+(\.\d+)?\s*(元|块)",
        r"保证[^。，,！!]{0,8}(到账|送达|退款|到货)", r"一定(能|会|可以)[^。，,！!]{0,6}(退|到|赔)",
        r"马上到账", r"(今天|明天)(就)?(能|会|可以)(到账|退款|退回)",
        r"(已经|已)(为您|帮您|给您)?(退款|退钱|办理退款)(成功)?"]
NEG = re.compile(r"不|无法|没法|没有|无权|暂不|禁止|严禁")
BOUNDARY = re.compile(r"[。！!？?；;，,\n]")
EXEMPT = ["运费险赔付", "由运费险", "运费险会赔"]


def main(text: str, order_id: str) -> dict:
    # 部分推理模型会把思考过程放在 <think>…</think> 里，先去掉，只检测和展示最终回复
    t = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    probe = t
    for e in EXEMPT:
        probe = probe.replace(e, "")
    hits = []
    for pat in RISK:
        for m in re.finditer(pat, probe):
            # 只看命中词所在的这半句话（逗号、句号隔开）里，前面有没有否定词，比如"无法提供补偿"
            seg = probe[:m.start()]
            cut = [x.end() for x in BOUNDARY.finditer(seg)]
            clause = seg[cut[-1]:] if cut else seg
            if NEG.search(clause):
                continue
            hits.append(m.group(0))
    if hits:
        tk = _ticket(order_id or "", "越权拦截")
        ans = "亲，这个问题需要专人为您核实处理，我已经为您登记并转给人工客服（工单 " + tk + "），请稍等～"
        return {"answer": ans, "hit": "yes", "hit_words": "、".join(hits)}
    return {"answer": t, "hit": "no", "hit_words": ""}
