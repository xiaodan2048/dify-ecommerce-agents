# ============================================================
# 用在：主流程「E 报告组装」（「E2 报告组装（无异动）」用同一份代码）
# 输入变量（在节点「输入变量」里逐个添加，名字必须一模一样）：
#   facts ← A权限校验与异动检测/facts
#   checked ← D依据校验/checked（E2 节点里改成 ← A权限校验与异动检测/message，它在这条分支上是空的）
# 输出变量（在节点「输出变量」里添加，名字和类型必须一模一样）：
#   report（String）
# 用法：全选本文件（Cmd+A）→ 复制 → 在 Dify 代码框里全选后粘贴覆盖
# ============================================================
import json
import re
import math
from datetime import datetime, date, timedelta

# ---- 本节点逻辑 ----
WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
CH = ["搜索", "推荐", "付费推广", "直播达人", "其他"]


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _cn(s):
    d = _d(s)
    return str(d.month) + "月" + str(d.day) + "日"


def _money(x):
    return "{:,.0f}".format(x)


def _pct(a, b):
    if not b:
        return None
    return round((a - b) / b * 100, 1)


def _sp(x):
    if x is None:
        return "—"
    return ("+" if x > 0 else ("−" if x < 0 else "")) + str(abs(x)) + "%"


def _n(x):
    return ("%g" % x) if isinstance(x, float) else str(x)


def _range(a):
    s = _cn(a["start"]) + "（" + WEEK[_d(a["start"]).weekday()] + "）"
    if a["days"] > 1:
        s += "–" + _cn(a["end"]) + "，连续 " + str(a["days"]) + " 天"
    return s


def _decomp(a):
    dc = a["decomp"]
    return "访客 " + _sp(dc["访客"]) + "｜转化率 " + _sp(dc["转化率"]) + "｜客单价 " + _sp(dc["客单价"]) + \
           " → 主要是**" + a["driver"] + "**变化"


def _cause(it):
    out = []
    if not it:
        return ["- 原因：（未归因）"]
    if it["cat"]:
        out.append("- **主因：" + it["cat"] + "**｜" + (it["text"] or "（无说明）"))
    if it["evidence"]:
        out.append("- 依据：" + "；".join(it["evidence"]))
    if it["verify"]:
        out.append("- 建议核实：" + it["verify"])
    if it["status"] == "已校验":
        out.append("- 校验：✅ 依据已逐条核对")
    elif it["status"] == "部分依据来自运营补充":
        out.append("- 校验：☑️ 数据依据已核对；部分依据来自运营补充，未经数据校验")
    else:
        out.append("- 校验：⚠️ 待人工确认（" + "；".join(it["issues"]) + "）")
    return out


def main(facts: str, checked: str) -> dict:
    f = json.loads(facts)
    c = json.loads(checked) if (checked or "").strip() else {"items": [], "summary": "", "summary_issues": []}
    items = {x["id"]: x for x in c.get("items", [])}
    foot = "\n\n---\n数字由查询模板直接计算；原因由 Agent 归纳，并经过依据校验节点逐条核对。发给品牌方前请运营确认。"
    L = []
    if f["mode"] == "异动提醒":
        t = f["today"]
        day = f["period"][0]
        if not f["anomalies"]:
            L.append("### ✅ " + f["shop"] + "｜" + _cn(day) + "（" + WEEK[_d(day).weekday()] + "）无异动")
            L.append("GMV " + _money(t["GMV"]) + " 元，较近4周同日中位数 " + _sp(t["较中位数"]) + "，较前7日均值 " +
                     _sp(t["较前7日均值"]) + "。")
            L.append("\n判定规则：" + f["rule"] + "。")
            return {"report": "\n".join(L)}
        a = f["anomalies"][0]
        icon = "📈" if a["dir"] == "上涨" else "📉"
        L.append("### " + icon + " 【异动提醒】" + f["shop"] + "｜" + _cn(day) + "（" + WEEK[_d(day).weekday()] + "）")
        L.append("**GMV " + _money(t["GMV"]) + " 元**，较近4周同日中位数 " + _sp(t["较中位数"]) + "，较前7日均值 " +
                 _sp(t["较前7日均值"]) + ("（自 " + _cn(a["start"]) + " 起已连续 " + str(a["days"]) + " 天）" if a["days"] > 1 else ""))
        L.append("拆解：" + _decomp(a))
        L.append("")
        L += _cause(items.get(a["id"]))
        return {"report": "\n".join(L) + foot}

    # ---------------- 周报 ----------------
    p1, p2 = f["period"]
    k, kp = f["kpi"]["cur"], f["kpi"]["prev"]
    L.append("# " + f["shop"] + " 经营周报（" + _cn(p1) + "–" + _cn(p2) + "）")
    L.append("> 初稿｜周报Agent 生成｜运营：" + f["operator_name"] + "｜数据截止 " + _cn(f["cutoff"]))
    L.append("")
    L.append("## 本周小结")
    if c.get("summary"):
        L.append(c["summary"])
        if c.get("summary_issues"):
            L.append("\n⚠️ " + "；".join(c["summary_issues"]) + "，请人工确认。")
    else:
        L.append("GMV " + _money(k["GMV"]) + " 元，周环比 " + _sp(_pct(k["GMV"], kp["GMV"])) +
                 ("；本周无异动。" if not f["anomalies"] else "。") + "（小结待运营补充）")
    L.append("")
    L.append("## 一、核心指标")
    L.append("| 指标 | 本周 | 上周 | 周环比 |")
    L.append("|---|---:|---:|---:|")
    rows = [("GMV（元）", "GMV", True), ("访客", "访客", True), ("订单数", "订单数", True),
            ("转化率", "转化率%", False), ("客单价（元）", "客单价", True), ("退款率", "退款率%", False),
            ("广告花费（元）", "广告花费", True), ("广告ROI", "广告ROI", False)]
    if f["platform"] == "抖音":
        rows.append(("直播成交（元）", "直播成交", True))
    for name, key, money in rows:
        a, b = k[key], kp[key]
        if key.endswith("%"):
            L.append("| " + name + " | " + str(a) + "% | " + str(b) + "% | " +
                     ("+" if a - b > 0 else "−" if a - b < 0 else "") + str(abs(round(a - b, 2))) + " 个百分点 |")
        elif money:
            L.append("| " + name + " | " + _money(a) + " | " + _money(b) + " | " + _sp(_pct(a, b)) + " |")
        else:
            L.append("| " + name + " | " + str(a) + " | " + str(b) + " | " + _sp(_pct(a, b)) + " |")
    L.append("")
    L.append("## 二、本周异动与原因")
    if not f["anomalies"]:
        L.append("本周没有触发异动规则。（" + f["rule"] + "）")
    for i, a in enumerate(f["anomalies"]):
        L.append("### 异动" + str(i + 1) + "：" + _range(a) + " GMV " + a["dir"])
        L.append("- " + ("当日 " if a["days"] == 1 else "日均 ") + _money(a["gmv"]) + " 元，较近4周同日中位数 " + _sp(a["pct_med"]) + "（合计" +
                 ("多" if a["delta_total"] > 0 else "少") + " " + _money(abs(a["delta_total"])) + " 元）")
        L.append("- 拆解：" + _decomp(a))
        L += _cause(items.get(a["id"]))
        L.append("")
    for a in f.get("others", []):
        L.append("- 另有异动：" + _range(a) + " GMV " + a["dir"] + " " + _sp(a["pct_med"]) + "（影响较小，未展开）")
    L.append("")
    L.append("## 三、流量结构")
    L.append("| 渠道 | 本周访客 | 上周访客 | 周环比 |")
    L.append("|---|---:|---:|---:|")
    for ch in CH:
        a, b = k["渠道"][ch], kp["渠道"][ch]
        L.append("| " + ch + " | " + _money(a) + " | " + _money(b) + " | " + _sp(_pct(a, b)) + " |")
    L.append("")
    L.append("## 四、竞品与库存")
    if not f["competitor"] and not f["inventory"]:
        L.append("本周没有监测到竞品价格变化，也没有缺货记录。")
    for r in f["competitor"]:
        L.append("- 竞品：" + r["商品"] + " " + _cn(r["开始"]) + "–" + _cn(r["结束"]) + " " + r["动作"] +
                 "（" + _n(r["原价"]) + " → " + _n(r["活动价"]) + " 元）")
    for r in f["inventory"]:
        L.append("- 缺货：" + r["商品"] + " " + r["缺货开始"] + " 至 " + r["补货时间"] + "，" + r["说明"])
    L.append("")
    L.append("## 五、下周关注")
    if f["next_week"]:
        for r in f["next_week"]:
            L.append("- " + r["名称"] + "（" + _cn(r["开始"]) + "–" + _cn(r["结束"]) + "，" + r["类型"] + "）：" + r["说明"])
    else:
        L.append("- 活动日历里下周没有排期")
    L.append("- 待运营补充：品牌方本周关心的问题、下周动作计划")
    return {"report": "\n".join(L) + foot}
