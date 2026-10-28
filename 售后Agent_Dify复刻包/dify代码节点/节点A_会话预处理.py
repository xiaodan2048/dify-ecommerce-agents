# ============================================================
# 用在：主流程「A 会话预处理」
# 输入变量（在节点「输入变量」里逐个添加，名字必须一模一样）：
#   query ← sys.query
#   current_order_id ← 会话变量 current_order_id
#   pending_action ← 会话变量 pending_action
# 输出变量（在节点「输出变量」里添加，名字和类型必须一模一样）：
#   order_id（String）
#   route（String）
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
OID = re.compile(r"(QY|YY)\d{11}", re.I)
CONFIRM = ["确认", "确定", "是", "是的", "对", "对的", "没问题", "可以", "好", "好的", "嗯", "ok", "改吧", "确认修改"]
CANCEL = ["算了", "不改了", "取消", "不用了", "先不改", "不要改", "别改"]


def main(query: str, current_order_id: str, pending_action: str) -> dict:
    q = query or ""
    m = OID.search(q)
    order_id = m.group(0).upper() if m else (current_order_id or "")
    s = re.sub(r"[\s。！!，,.~～?？]", "", q).lower()
    route = "normal"
    if (pending_action or "").strip():
        if any(w in s for w in CANCEL):
            route = "cancel"
        elif s in CONFIRM or s.startswith("确认"):
            route = "confirm"
    return {"order_id": order_id, "route": route}
