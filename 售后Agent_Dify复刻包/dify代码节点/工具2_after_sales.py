# ============================================================
# 用在：工具工作流「after_sales」里的代码节点
# 输入变量（在节点「输入变量」里逐个添加，名字必须一模一样）：
#   action ← 开始/action
#   order_id ← 开始/order_id
#   buyer_id ← 开始/buyer_id
#   shop ← 开始/shop
#   reason_type ← 开始/reason_type
#   opened ← 开始/opened
#   ticket_type ← 开始/ticket_type
#   summary ← 开始/summary
#   buyer_confirmed ← 开始/buyer_confirmed
# 输出变量（在节点「输出变量」里添加，名字和类型必须一模一样）：
#   result（String）
# 用法：全选本文件（Cmd+A）→ 复制 → 在 Dify 代码框里全选后粘贴覆盖
# ============================================================
import json
import re
from datetime import datetime, timedelta

# 演示用的「现在」。固定住时间，评测结果才能复现；想用真实时间可改成 datetime.now() 的格式化字符串
DEMO_NOW = "2026-10-26 14:00"

# ---- 假订单数据（全部虚构）----
ORDERS = {
    'QY20261025001': {'order_id': 'QY20261025001', 'buyer_id': 'U1001', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 洗衣凝珠 52颗', 'qty': 1, 'amount': 59.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-25 10:12', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '林小姐', 'phone': '138****2201', 'address': '广州市天河区天河北路233号云峰广场'}, 'aftersale': None},
    'QY20261022002': {'order_id': 'QY20261022002', 'buyer_id': 'U1001', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 香氛洗衣液 3kg×2', 'qty': 1, 'amount': 89.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-22 09:30', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '林小姐', 'phone': '138****2201', 'address': '广州市天河区天河北路233号云峰广场'}, 'aftersale': None},
    'QY20261024003': {'order_id': 'QY20261024003', 'buyer_id': 'U1002', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 柔顺剂 2L', 'qty': 1, 'amount': 49.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-24 20:15', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '陈先生', 'phone': '139****5512', 'address': '广州市天河区体育西路111号星汇中心'}, 'aftersale': None},
    'QY20261023004': {'order_id': 'QY20261023004', 'buyer_id': 'U1002', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 厨房重油污清洁喷雾 500ml×3', 'qty': 1, 'amount': 45.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-23 11:00', 'status': '已发货', 'ship_time': '2026-10-24 16:20', 'sign_time': None, 'carrier': '远航快递', 'tracking_no': 'ZT78012345610', 'trace': [['2026-10-24 16:20', '商家已发货，快递员已揽收【广州白云仓】'], ['2026-10-25 02:10', '快件已到达【广州转运中心】'], ['2026-10-26 09:15', '快件已到达【广州天河体育西营业部】，正在安排派送']], 'receiver': {'name': '陈先生', 'phone': '139****5512', 'address': '广州市天河区体育西路111号星汇中心'}, 'aftersale': None},
    'QY20261018005': {'order_id': 'QY20261018005', 'buyer_id': 'U1003', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 家清囤货礼盒', 'qty': 1, 'amount': 259.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-18 13:00', 'status': '已签收', 'ship_time': '2026-10-19 10:00', 'sign_time': '2026-10-21 15:30', 'carrier': '远航快递', 'tracking_no': 'ZT26101800588', 'trace': [['2026-10-19 10:00', '商家已发货，快递员已揽收'], ['2026-10-19 23:30', '快件已到达【转运中心】'], ['2026-10-21 15:30', '快件已签收，签收人：本人。感谢使用远航快递（广州市）']], 'receiver': {'name': '王女士', 'phone': '137****8823', 'address': '广州市越秀区环市东路339号'}, 'aftersale': None},
    'QY20261008006': {'order_id': 'QY20261008006', 'buyer_id': 'U1003', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 洗衣凝珠 52颗', 'qty': 1, 'amount': 59.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-08 08:00', 'status': '已签收', 'ship_time': '2026-10-09 10:00', 'sign_time': '2026-10-15 18:00', 'carrier': '远航快递', 'tracking_no': 'ZT26100800688', 'trace': [['2026-10-09 10:00', '商家已发货，快递员已揽收'], ['2026-10-09 23:30', '快件已到达【转运中心】'], ['2026-10-15 18:00', '快件已签收，签收人：本人。感谢使用远航快递（广州市）']], 'receiver': {'name': '王女士', 'phone': '137****8823', 'address': '广州市越秀区环市东路339号'}, 'aftersale': None},
    'QY20261021007': {'order_id': 'QY20261021007', 'buyer_id': 'U1004', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 香氛洗衣液 3kg×2', 'qty': 1, 'amount': 89.0, 'gift': None, 'cold_chain': False, 'freight_insurance': True, 'order_time': '2026-10-21 21:00', 'status': '已签收', 'ship_time': '2026-10-22 11:00', 'sign_time': '2026-10-24 12:00', 'carrier': '远航快递', 'tracking_no': 'ZT26102100788', 'trace': [['2026-10-22 11:00', '商家已发货，快递员已揽收'], ['2026-10-22 23:30', '快件已到达【转运中心】'], ['2026-10-24 12:00', '快件已签收，签收人：本人。感谢使用远航快递（深圳市）']], 'receiver': {'name': '赵先生', 'phone': '136****4410', 'address': '深圳市福田区福华三路88号'}, 'aftersale': None},
    'QY20261012008': {'order_id': 'QY20261012008', 'buyer_id': 'U1004', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 柔顺剂 2L', 'qty': 1, 'amount': 49.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-12 10:00', 'status': '已签收', 'ship_time': '2026-10-12 17:00', 'sign_time': '2026-10-14 11:00', 'carrier': '远航快递', 'tracking_no': 'ZT26101200888', 'trace': [['2026-10-12 17:00', '商家已发货，快递员已揽收'], ['2026-10-12 23:30', '快件已到达【转运中心】'], ['2026-10-14 11:00', '快件已签收，签收人：本人。感谢使用远航快递（深圳市）']], 'receiver': {'name': '赵先生', 'phone': '136****4410', 'address': '深圳市福田区福华三路88号'}, 'aftersale': None},
    'QY20261019009': {'order_id': 'QY20261019009', 'buyer_id': 'U1005', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 香氛洗衣液 3kg×2', 'qty': 1, 'amount': 89.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-19 20:00', 'status': '已签收', 'ship_time': '2026-10-23 10:00', 'sign_time': '2026-10-25 10:00', 'carrier': '远航快递', 'tracking_no': 'ZT26101900988', 'trace': [['2026-10-23 10:00', '商家已发货，快递员已揽收'], ['2026-10-23 23:30', '快件已到达【转运中心】'], ['2026-10-25 10:00', '快件已签收，签收人：本人。感谢使用远航快递（佛山市）']], 'receiver': {'name': '黄女士', 'phone': '135****7731', 'address': '佛山市顺德区大良街道德民路12号'}, 'aftersale': None},
    'QY20261016010': {'order_id': 'QY20261016010', 'buyer_id': 'U1005', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 厨房重油污清洁喷雾 500ml×3', 'qty': 1, 'amount': 45.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-16 12:00', 'status': '已签收', 'ship_time': '2026-10-17 10:00', 'sign_time': '2026-10-20 17:00', 'carrier': '远航快递', 'tracking_no': 'ZT26101601088', 'trace': [['2026-10-17 10:00', '商家已发货，快递员已揽收'], ['2026-10-17 23:30', '快件已到达【转运中心】'], ['2026-10-20 17:00', '快件已签收，签收人：本人。感谢使用远航快递（佛山市）']], 'receiver': {'name': '黄女士', 'phone': '135****7731', 'address': '佛山市顺德区大良街道德民路12号'}, 'aftersale': None},
    'QY20261001011': {'order_id': 'QY20261001011', 'buyer_id': 'U1006', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 洗衣凝珠 52颗', 'qty': 1, 'amount': 59.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-01 09:00', 'status': '已签收', 'ship_time': '2026-10-02 10:00', 'sign_time': '2026-10-04 14:00', 'carrier': '远航快递', 'tracking_no': 'ZT26100101188', 'trace': [['2026-10-02 10:00', '商家已发货，快递员已揽收'], ['2026-10-02 23:30', '快件已到达【转运中心】'], ['2026-10-04 14:00', '快件已签收，签收人：本人。感谢使用远航快递（深圳市）']], 'receiver': {'name': '周先生', 'phone': '188****0912', 'address': '深圳市宝安区新安街道创业二路8号'}, 'aftersale': None},
    'QY20261023012': {'order_id': 'QY20261023012', 'buyer_id': 'U1006', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 家清囤货礼盒', 'qty': 1, 'amount': 259.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-23 10:00', 'status': '已发货', 'ship_time': '2026-10-23 18:00', 'sign_time': None, 'carrier': '远航快递', 'tracking_no': 'ZT78012345612', 'trace': [['2026-10-23 18:00', '商家已发货，快递员已揽收【广州白云仓】'], ['2026-10-23 23:40', '快件已到达【广州转运中心】']], 'receiver': {'name': '周先生', 'phone': '188****0912', 'address': '深圳市宝安区新安街道创业二路8号'}, 'aftersale': None},
    'QY20261017013': {'order_id': 'QY20261017013', 'buyer_id': 'U1007', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 香氛洗衣液 3kg×2', 'qty': 1, 'amount': 89.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-17 15:00', 'status': '售后中', 'ship_time': '2026-10-18 10:00', 'sign_time': '2026-10-20 13:00', 'carrier': '远航快递', 'tracking_no': 'ZT26101701388', 'trace': [['2026-10-18 10:00', '商家已发货，快递员已揽收'], ['2026-10-18 23:30', '快件已到达【转运中心】'], ['2026-10-20 13:00', '快件已签收，签收人：本人。感谢使用远航快递（东莞市）']], 'receiver': {'name': '吴女士', 'phone': '186****3365', 'address': '东莞市南城区鸿福路106号'}, 'aftersale': {'type': '无理由退货', 'apply_time': '2026-10-24 10:00', 'progress': '买家已寄回，等待仓库验收', 'next': '仓库收货后 48 小时内完成审核，审核通过后原路退款'}},
    'QY20261020014': {'order_id': 'QY20261020014', 'buyer_id': 'U1007', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 柔顺剂 2L', 'qty': 1, 'amount': 49.9, 'gift': '赠品：清屿 旅行装柔顺剂 100ml', 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-20 19:00', 'status': '已签收', 'ship_time': '2026-10-21 10:00', 'sign_time': '2026-10-23 19:00', 'carrier': '远航快递', 'tracking_no': 'ZT26102001488', 'trace': [['2026-10-21 10:00', '商家已发货，快递员已揽收'], ['2026-10-21 23:30', '快件已到达【转运中心】'], ['2026-10-23 19:00', '快件已签收，签收人：本人。感谢使用远航快递（东莞市）']], 'receiver': {'name': '吴女士', 'phone': '186****3365', 'address': '东莞市南城区鸿福路106号'}, 'aftersale': None},
    'QY20261024015': {'order_id': 'QY20261024015', 'buyer_id': 'U1008', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 洗衣凝珠 52颗', 'qty': 1, 'amount': 59.9, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-24 22:00', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '郑先生', 'phone': '158****6610', 'address': '广州市番禺区市桥街道光明北路1号'}, 'aftersale': None},
    'QY20261026029': {'order_id': 'QY20261026029', 'buyer_id': 'U1009', 'shop': '清屿官方旗舰店', 'brand': '清屿', 'item': '清屿 厨房重油污清洁喷雾 500ml×3', 'qty': 1, 'amount': 45.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-26 09:00', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '孙女士', 'phone': '159****2287', 'address': '广州市海珠区新港中路397号'}, 'aftersale': None},
    'YY20261025016': {'order_id': 'YY20261025016', 'buyer_id': 'U1001', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油软胶囊 120粒', 'qty': 1, 'amount': 168.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-25 15:00', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '林小姐', 'phone': '138****2201', 'address': '广州市天河区天河北路233号云峰广场'}, 'aftersale': None},
    'YY20261021017': {'order_id': 'YY20261021017', 'buyer_id': 'U1002', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 冷藏益生菌 30条（需冷藏）', 'qty': 1, 'amount': 199.0, 'gift': None, 'cold_chain': True, 'freight_insurance': False, 'order_time': '2026-10-21 10:00', 'status': '已签收', 'ship_time': '2026-10-22 09:00', 'sign_time': '2026-10-23 13:00', 'carrier': '青鸟冷运', 'tracking_no': 'QN26102101788', 'trace': [['2026-10-22 09:00', '商家已发货，快递员已揽收'], ['2026-10-22 23:30', '快件已到达【转运中心】'], ['2026-10-23 13:00', '快件已签收，签收人：本人。感谢使用青鸟冷运（广州市）']], 'receiver': {'name': '陈先生', 'phone': '139****5512', 'address': '广州市天河区体育西路111号星汇中心'}, 'aftersale': None},
    'YY20261019018': {'order_id': 'YY20261019018', 'buyer_id': 'U1003', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油软胶囊 120粒', 'qty': 1, 'amount': 168.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-19 09:00', 'status': '已签收', 'ship_time': '2026-10-20 10:00', 'sign_time': '2026-10-22 16:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26101901888', 'trace': [['2026-10-20 10:00', '商家已发货，快递员已揽收'], ['2026-10-20 23:30', '快件已到达【转运中心】'], ['2026-10-22 16:00', '快件已签收，签收人：本人。感谢使用青鸟速运（广州市）']], 'receiver': {'name': '王女士', 'phone': '137****8823', 'address': '广州市越秀区环市东路339号'}, 'aftersale': None},
    'YY20261015019': {'order_id': 'YY20261015019', 'buyer_id': 'U1003', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油年度囤货装 120粒×3', 'qty': 1, 'amount': 459.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-15 20:00', 'status': '已签收', 'ship_time': '2026-10-16 10:00', 'sign_time': '2026-10-20 11:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26101501988', 'trace': [['2026-10-16 10:00', '商家已发货，快递员已揽收'], ['2026-10-16 23:30', '快件已到达【转运中心】'], ['2026-10-20 11:00', '快件已签收，签收人：本人。感谢使用青鸟速运（广州市）']], 'receiver': {'name': '王女士', 'phone': '137****8823', 'address': '广州市越秀区环市东路339号'}, 'aftersale': None},
    'YY20261010020': {'order_id': 'YY20261010020', 'buyer_id': 'U1004', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 复合维生素片 90片', 'qty': 1, 'amount': 99.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-10 10:00', 'status': '已签收', 'ship_time': '2026-10-11 10:00', 'sign_time': '2026-10-13 15:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26101002088', 'trace': [['2026-10-11 10:00', '商家已发货，快递员已揽收'], ['2026-10-11 23:30', '快件已到达【转运中心】'], ['2026-10-13 15:00', '快件已签收，签收人：本人。感谢使用青鸟速运（深圳市）']], 'receiver': {'name': '赵先生', 'phone': '136****4410', 'address': '深圳市福田区福华三路88号'}, 'aftersale': None},
    'YY20261001021': {'order_id': 'YY20261001021', 'buyer_id': 'U1004', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 叶黄素酯软糖 60粒', 'qty': 1, 'amount': 129.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-01 10:00', 'status': '已签收', 'ship_time': '2026-10-01 18:00', 'sign_time': '2026-10-03 12:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26100102188', 'trace': [['2026-10-01 18:00', '商家已发货，快递员已揽收'], ['2026-10-01 23:30', '快件已到达【转运中心】'], ['2026-10-03 12:00', '快件已签收，签收人：本人。感谢使用青鸟速运（深圳市）']], 'receiver': {'name': '赵先生', 'phone': '136****4410', 'address': '深圳市福田区福华三路88号'}, 'aftersale': None},
    'YY20260915022': {'order_id': 'YY20260915022', 'buyer_id': 'U1005', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油软胶囊 120粒', 'qty': 1, 'amount': 168.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-09-15 10:00', 'status': '已签收', 'ship_time': '2026-09-16 10:00', 'sign_time': '2026-09-18 12:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26091502288', 'trace': [['2026-09-16 10:00', '商家已发货，快递员已揽收'], ['2026-09-16 23:30', '快件已到达【转运中心】'], ['2026-09-18 12:00', '快件已签收，签收人：本人。感谢使用青鸟速运（佛山市）']], 'receiver': {'name': '黄女士', 'phone': '135****7731', 'address': '佛山市顺德区大良街道德民路12号'}, 'aftersale': None},
    'YY20261022023': {'order_id': 'YY20261022023', 'buyer_id': 'U1005', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 冷藏益生菌 30条（需冷藏）', 'qty': 1, 'amount': 199.0, 'gift': None, 'cold_chain': True, 'freight_insurance': False, 'order_time': '2026-10-22 22:00', 'status': '已发货', 'ship_time': '2026-10-23 17:00', 'sign_time': None, 'carrier': '青鸟冷运', 'tracking_no': 'QN1409876543210', 'trace': [['2026-10-23 17:00', '商家已发货，青鸟冷运已揽收【杭州冷链仓】'], ['2026-10-24 06:00', '快件已到达【杭州冷链转运中心】'], ['2026-10-25 21:30', '快件已到达【广州冷链分拨中心】'], ['2026-10-26 10:40', '快件已到达【佛山顺德大良营业点】，预计今日派送']], 'receiver': {'name': '黄女士', 'phone': '135****7731', 'address': '佛山市顺德区大良街道德民路12号'}, 'aftersale': None},
    'YY20261024024': {'order_id': 'YY20261024024', 'buyer_id': 'U1006', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 复合维生素片 90片', 'qty': 1, 'amount': 99.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-24 18:00', 'status': '待发货', 'ship_time': None, 'sign_time': None, 'carrier': None, 'tracking_no': None, 'trace': [], 'receiver': {'name': '周先生', 'phone': '188****0912', 'address': '深圳市宝安区新安街道创业二路8号'}, 'aftersale': None},
    'YY20261023025': {'order_id': 'YY20261023025', 'buyer_id': 'U1006', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 叶黄素酯软糖 60粒', 'qty': 1, 'amount': 129.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-23 12:00', 'status': '已发货', 'ship_time': '2026-10-24 10:00', 'sign_time': None, 'carrier': '长风快递', 'tracking_no': 'CF4312987650', 'trace': [['2026-10-24 10:00', '商家已发货，快递员已揽收【杭州仓】'], ['2026-10-25 04:20', '快件已到达【深圳转运中心】'], ['2026-10-26 07:50', '快件已到达【深圳宝安新安营业部】，正在安排派送']], 'receiver': {'name': '周先生', 'phone': '188****0912', 'address': '深圳市宝安区新安街道创业二路8号'}, 'aftersale': None},
    'YY20261020026': {'order_id': 'YY20261020026', 'buyer_id': 'U1007', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油软胶囊 120粒', 'qty': 1, 'amount': 168.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-20 10:00', 'status': '已签收', 'ship_time': '2026-10-23 10:00', 'sign_time': '2026-10-25 09:30', 'carrier': '青鸟速运', 'tracking_no': 'QN26102002688', 'trace': [['2026-10-23 10:00', '商家已发货，快递员已揽收'], ['2026-10-23 23:30', '快件已到达【转运中心】'], ['2026-10-25 09:30', '快件已签收，签收人：本人。感谢使用青鸟速运（东莞市）']], 'receiver': {'name': '吴女士', 'phone': '186****3365', 'address': '东莞市南城区鸿福路106号'}, 'aftersale': None},
    'YY20261012027': {'order_id': 'YY20261012027', 'buyer_id': 'U1008', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 冷藏益生菌 30条（需冷藏）', 'qty': 1, 'amount': 199.0, 'gift': None, 'cold_chain': True, 'freight_insurance': False, 'order_time': '2026-10-12 10:00', 'status': '已签收', 'ship_time': '2026-10-13 10:00', 'sign_time': '2026-10-15 12:00', 'carrier': '青鸟冷运', 'tracking_no': 'QN26101202788', 'trace': [['2026-10-13 10:00', '商家已发货，快递员已揽收'], ['2026-10-13 23:30', '快件已到达【转运中心】'], ['2026-10-15 12:00', '快件已签收，签收人：本人。感谢使用青鸟冷运（广州市）']], 'receiver': {'name': '郑先生', 'phone': '158****6610', 'address': '广州市番禺区市桥街道光明北路1号'}, 'aftersale': None},
    'YY20261018028': {'order_id': 'YY20261018028', 'buyer_id': 'U1009', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 复合维生素片 90片', 'qty': 1, 'amount': 99.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-18 10:00', 'status': '售后中', 'ship_time': '2026-10-19 10:00', 'sign_time': '2026-10-21 12:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26101802888', 'trace': [['2026-10-19 10:00', '商家已发货，快递员已揽收'], ['2026-10-19 23:30', '快件已到达【转运中心】'], ['2026-10-21 12:00', '快件已签收，签收人：本人。感谢使用青鸟速运（广州市）']], 'receiver': {'name': '孙女士', 'phone': '159****2287', 'address': '广州市海珠区新港中路397号'}, 'aftersale': {'type': '质量问题退款', 'apply_time': '2026-10-25 16:00', 'progress': '等待商家审核', 'next': '商家会在 24 小时内完成审核'}},
    'YY20261008030': {'order_id': 'YY20261008030', 'buyer_id': 'U1010', 'shop': '元养官方旗舰店', 'brand': '元养', 'item': '元养 深海鱼油年度囤货装 120粒×3', 'qty': 1, 'amount': 459.0, 'gift': None, 'cold_chain': False, 'freight_insurance': False, 'order_time': '2026-10-08 10:00', 'status': '已签收', 'ship_time': '2026-10-09 10:00', 'sign_time': '2026-10-11 12:00', 'carrier': '青鸟速运', 'tracking_no': 'QN26100803088', 'trace': [['2026-10-09 10:00', '商家已发货，快递员已揽收'], ['2026-10-09 23:30', '快件已到达【转运中心】'], ['2026-10-11 12:00', '快件已签收，签收人：本人。感谢使用青鸟速运（杭州市）']], 'receiver': {'name': '何先生', 'phone': '177****5098', 'address': '杭州市西湖区文三路90号'}, 'aftersale': None},
}

# ---- 品牌售后政策（结构化、带生效时间）----
POLICIES = {
    '清屿': {'category': '家清（洗衣液、凝珠、柔顺剂、清洁喷雾）', 'ship_promise_hours': 48, 'refund_human_threshold': 200, 'rules': {'QY-R1': {'title': '七天无理由退货', 'text': '签收 7 天内，商品未拆封、不影响二次销售，可无理由退货；退货运费由买家承担，买了运费险的由运费险赔付。', 'window_days': 7, 'effective_from': '2024-01-01'}, 'QY-R1P': {'title': '双11大促无理由退货延长', 'text': '2026-10-10 至 2026-11-11 期间下单的订单，无理由退货期延长至签收后 15 天，其余条件同 QY-R1。', 'window_days': 15, 'order_from': '2026-10-10 00:00', 'order_to': '2026-11-11 23:59', 'effective_from': '2026-10-10', 'effective_to': '2026-11-26'}, 'QY-R2': {'title': '质量问题退换', 'text': '签收 15 天内出现漏液、异味、结块、喷头失灵等质量问题，可退货或换货，需提供问题照片，运费由商家承担。已拆封也适用。', 'window_days': 15, 'evidence': '商品问题处的照片', 'effective_from': '2024-01-01'}, 'QY-R3': {'title': '物流破损', 'text': '签收 48 小时内反馈外包装破损、漏液，可选择免费补发或退款，需提供外箱和破损处照片；超过 48 小时按质量问题（QY-R2）处理。', 'window_hours': 48, 'evidence': '外箱和破损处照片', 'effective_from': '2024-01-01'}, 'QY-R4': {'title': '少件错发', 'text': '签收 7 天内反馈少件（含赠品）或错发，核实后免费补发，需提供开箱照片或快递面单照片。', 'window_days': 7, 'evidence': '开箱照片或快递面单照片', 'effective_from': '2024-01-01'}, 'QY-R5': {'title': '赠品', 'text': '退主商品时需一并退回赠品，赠品已使用的按赠品标价从退款中扣除。', 'effective_from': '2024-01-01'}, 'QY-R6': {'title': '客服授权边界', 'text': '客服不得承诺任何现金补偿、红包、优惠券；退款金额超过 200 元的售后由人工客服处理。', 'effective_from': '2024-01-01'}}},
    '元养': {'category': '保健食品（鱼油、益生菌、维生素、叶黄素）', 'ship_promise_hours': 48, 'refund_human_threshold': 300, 'rules': {'YY-R1': {'title': '七天无理由退货（限未拆封）', 'text': '签收 7 天内，商品未拆封（外层塑封完好）可无理由退货；保健食品属于入口商品，拆封后（含撕开塑封）不支持无理由退货；退货运费由买家承担。', 'window_days': 7, 'effective_from': '2024-01-01'}, 'YY-R1C': {'title': '冷链商品不支持无理由退货', 'text': '需冷藏的冷链商品（如冷藏益生菌）签收后无法确认储存条件，不支持无理由退货；质量问题按 YY-R2 处理。', 'effective_from': '2024-01-01'}, 'YY-R2': {'title': '质量问题退换', 'text': '签收 30 天内出现变质、胀袋、异味、破损、临近保质期（发货时剩余不足 90 天）等质量问题，可退货或换货，需提供问题照片和包装上的生产批号，运费由商家承担。已拆封也适用。', 'window_days': 30, 'evidence': '问题照片 + 包装上的生产批号照片', 'effective_from': '2024-01-01'}, 'YY-R3': {'title': '物流破损', 'text': '签收 48 小时内反馈外包装破损、胶囊破裂漏油，可选择免费补发或退款，需提供外箱和破损处照片；超过 48 小时按质量问题（YY-R2）处理。', 'window_hours': 48, 'evidence': '外箱和破损处照片', 'effective_from': '2024-01-01'}, 'YY-R4': {'title': '少件错发', 'text': '签收 7 天内反馈少件或错发，核实后免费补发，需提供开箱照片或快递面单照片。', 'window_days': 7, 'evidence': '开箱照片或快递面单照片', 'effective_from': '2024-01-01'}, 'YY-R5': {'title': '功效问题不由售后解答', 'text': '售后客服不解答功效、疗效、能否替代药物等问题，统一回复建议咨询医生或营养师；用法用量以包装标签为准。', 'effective_from': '2024-01-01'}, 'YY-R6': {'title': '客服授权边界', 'text': '客服不得承诺任何现金补偿、红包、优惠券；退款金额超过 300 元的售后由人工客服处理。', 'effective_from': '2024-01-01'}}},
}

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


def _ticket(order_id, ticket_type, buyer_id=""):
    """生成演示用工单号（同一订单同一类型得到同一个号，方便复现）。
    v1.2：没有订单号时把买家 ID 一起算进去，避免不同买家拿到同一个工单号（v1.1 评测里 C02、C03 撞号）。"""
    s = (order_id or ("NA-" + (buyer_id or ""))) + ticket_type
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) % 1000000
    return "TK" + NOW.strftime("%m%d") + str(h).zfill(6)


# ---- 本节点逻辑 ----
REASONS = {
    "无理由": ["无理由", "不想要", "拍错", "不喜欢", "买多", "七天", "7天"],
    "质量问题": ["质量"],
    "物流破损": ["破损", "物流破损", "漏液", "漏油", "压坏"],
    "少件错发": ["少件", "错发", "漏发", "少发", "发错"],
}


def _norm_reason(r):
    r = (r or "").strip()
    for k, words in REASONS.items():
        if r == k or any(w in r for w in words):
            return k
    return ""


def _norm_opened(x):
    x = (x or "").strip()
    if x in ("未拆封", "没拆", "没拆封", "未开封", "否", "no", "false"):
        return "未拆封"
    if x in ("已拆封", "拆了", "已开封", "拆封了", "是", "yes", "true"):
        return "已拆封"
    return "未知"


def _rule(brand, rid):
    r = POLICIES[brand]["rules"][rid]
    return rid, "【" + r["title"] + "】" + r["text"]


def _out(decision, rid_text=None, solution="", explain="", next_step="", evidence="", freight="", **kw):
    d = {"decision": decision, "solution": solution, "explain": explain, "next_step": next_step,
         "evidence_required": evidence, "freight": freight}
    if rid_text:
        d["rule_id"], d["rule_text"] = rid_text
    d.update(kw)
    return d


def _check_policy(order_id, buyer_id, shop, reason_type, opened):
    o, err = _find(order_id, buyer_id, shop)
    if err:
        res = _out("订单未找到", explain="本店没有查到该买家的这个订单",
                   next_step="请买家提供正确的订单号（以 QY 或 YY 开头），不要猜测")
        return {"result": json.dumps(res, ensure_ascii=False)}

    brand = o["brand"]
    pol = POLICIES[brand]
    p = "QY" if brand == "清屿" else "YY"
    reason = _norm_reason(reason_type)
    op = _norm_opened(opened)
    amount = o["amount"]
    st = o["status"]

    if st == "售后中":
        a = o["aftersale"]
        res = _out("已在售后中", explain="该订单已有进行中的售后：" + a["type"] + "，" + a["apply_time"] + " 申请",
                   next_step="告知买家当前进度：" + a["progress"] + "；" + a["next"] + "。不要重复发起售后")
    elif st == "待发货":
        res = _out("可办理", solution="仅退款", explain="订单还没发货",
                   next_step="引导买家在订单页点「申请退款」选择「仅退款」，无需退货")
    elif st == "已发货":
        res = _out("可办理", solution="拦截或拒收后退款", explain="订单运输中",
                   next_step="引导买家在订单页申请退款，快递拦截退回；或派送时拒收，仓库收到退回后退款")
    elif not reason:
        res = _out("需补充信息", explain="还不清楚退货原因",
                   next_step="问买家退货原因：是不想要了，还是商品有质量问题、收到时破损、少件或发错？")
    else:
        sign = _t(o["sign_time"])
        days = (NOW - sign).total_seconds() / 86400
        hours = days * 24
        kw = {"days_since_sign": round(days, 1), "refund_amount": amount}

        if reason == "无理由":
            if brand == "元养" and o["cold_chain"]:
                res = _out("不可办理", _rule(brand, "YY-R1C"), explain="冷链商品不支持无理由退货",
                           next_step="如有变质、胀袋等质量问题，可以按质量问题申请", **kw)
            elif op == "未知":
                res = _out("需补充信息", explain="无理由退货要求未拆封",
                           next_step="问买家：商品拆封了吗？（包括撕开外层塑封）", **kw)
            elif op == "已拆封":
                res = _out("不可办理", _rule(brand, p + "-R1"), explain="已拆封不支持无理由退货",
                           next_step="如有漏液、异味、变质等质量问题，可以按质量问题申请", **kw)
            else:
                rid = p + "-R1"
                if brand == "清屿":
                    pr = pol["rules"]["QY-R1P"]
                    ot = _t(o["order_time"])
                    if _t(pr["order_from"]) <= ot <= _t(pr["order_to"]):
                        rid = "QY-R1P"
                win = pol["rules"][rid]["window_days"]
                if days <= win:
                    fr = "买家承担，已买运费险，由运费险赔付" if o["freight_insurance"] else "买家承担"
                    res = _out("可办理", _rule(brand, rid), solution="退货退款",
                               explain="签收 " + str(round(days, 1)) + " 天，在 " + str(win) + " 天无理由期内且未拆封",
                               next_step="引导买家在订单页点「申请售后」-「退货退款」，原因选「七天无理由」，退回时请带上赠品" if o["gift"]
                               else "引导买家在订单页点「申请售后」-「退货退款」，原因选「七天无理由」",
                               freight=fr, **kw)
                else:
                    res = _out("不可办理", _rule(brand, rid),
                               explain="签收已 " + str(round(days, 1)) + " 天，超过 " + str(win) + " 天无理由退货期",
                               next_step="如有质量问题，可以按质量问题申请", **kw)

        elif reason in ("质量问题", "物流破损"):
            if reason == "物流破损" and hours <= pol["rules"][p + "-R3"]["window_hours"]:
                r3 = pol["rules"][p + "-R3"]
                res = _out("可办理", _rule(brand, p + "-R3"), solution="免费补发或退款（买家二选一）",
                           explain="签收 " + str(round(hours)) + " 小时内反馈物流破损",
                           next_step="请买家上传" + r3["evidence"] + "，并问买家选补发还是退款；选补发需买家确认后再建补发工单",
                           evidence=r3["evidence"], freight="商家承担", **kw)
            else:
                r2 = pol["rules"][p + "-R2"]
                pre = "物流破损超过 48 小时，按质量问题处理；" if reason == "物流破损" else ""
                if days <= r2["window_days"]:
                    res = _out("可办理", _rule(brand, p + "-R2"), solution="退货退款或换货",
                               explain=pre + "签收 " + str(round(days, 1)) + " 天，在 " + str(r2["window_days"]) + " 天质量问题售后期内",
                               next_step="请买家上传" + r2["evidence"] + "，在订单页「申请售后」原因选「质量问题」，审核通过后处理",
                               evidence=r2["evidence"], freight="商家承担", **kw)
                else:
                    res = _out("不可办理", _rule(brand, p + "-R2"),
                               explain=pre + "签收已 " + str(round(days, 1)) + " 天，超过 " + str(r2["window_days"]) + " 天质量问题售后期",
                               next_step="诚恳说明已超出售后期；如买家坚持，可转人工进一步核实", **kw)

        else:  # 少件错发
            r4 = pol["rules"][p + "-R4"]
            if days <= r4["window_days"]:
                res = _out("可办理", _rule(brand, p + "-R4"), solution="核实后免费补发",
                           explain="签收 " + str(round(days, 1)) + " 天内反馈少件/错发" + ("（本单含" + o["gift"] + "）" if o["gift"] else ""),
                           next_step="请买家上传" + r4["evidence"] + "；向买家确认补发内容，买家同意后建补发工单",
                           evidence=r4["evidence"], freight="商家承担", **kw)
            else:
                res = _out("不可办理", _rule(brand, p + "-R4"),
                           explain="签收已 " + str(round(days, 1)) + " 天，超过 7 天少件错发反馈期",
                           next_step="诚恳说明；如买家坚持，可转人工核实", **kw)

        # 金额超过客服授权额度：判定可退也必须转人工
        th = pol["refund_human_threshold"]
        if res["decision"] == "可办理" and "退款" in res["solution"] and amount > th:
            res = _out("需转人工", _rule(brand, p + "-R6"), solution=res["solution"],
                       explain="规则上可以办理，但退款金额 " + str(amount) + " 元超过客服授权额度 " + str(th) + " 元",
                       next_step="告诉买家需要人工客服审核，调用 create_ticket（ticket_type=转人工）", **kw)

    return {"result": json.dumps(res, ensure_ascii=False)}


TYPES = ["转人工", "补发", "质量问题审核", "物流异常", "催发货"]


def _create_ticket(order_id, buyer_id, shop, ticket_type, summary, buyer_confirmed):
    tt = (ticket_type or "").strip()
    if tt not in TYPES:
        res = {"ok": False, "error": "BAD_TICKET_TYPE", "message": "ticket_type 只能是：" + "、".join(TYPES)}
        return {"result": json.dumps(res, ensure_ascii=False)}
    o, err = _find(order_id, buyer_id, shop)
    if err and tt != "转人工":
        res = {"ok": False, "error": "ORDER_NOT_FOUND", "message": "没有有效订单，不能创建该类工单"}
    elif tt != "转人工" and (buyer_confirmed or "").strip().lower() not in ("是", "yes", "true", "已确认"):
        res = {"ok": False, "error": "NEED_BUYER_CONFIRM",
               "message": "这是写操作：请先向买家复述要办理的事项并征得同意，买家同意后再调用，buyer_confirmed 传 是"}
    else:
        oid = o["order_id"] if o else ""
        res = {"ok": True, "ticket_id": _ticket(oid, tt, buyer_id), "ticket_type": tt, "order_id": oid,
               "summary": (summary or "")[:200],
               "message": "工单已创建。转人工类：人工客服会尽快接入；其他类：相关团队会跟进处理。不要向买家承诺具体完成时间。"}
    return {"result": json.dumps(res, ensure_ascii=False)}


# ---- 入口：按 action 分流。check_policy 只读；create_ticket 是写操作，需要买家确认 ----
def main(action: str, order_id: str, buyer_id: str, shop: str, reason_type: str, opened: str,
         ticket_type: str, summary: str, buyer_confirmed: str) -> dict:
    a = (action or "").strip()
    if a == "check_policy":
        return _check_policy(order_id, buyer_id, shop, reason_type, opened)
    if a == "create_ticket":
        return _create_ticket(order_id, buyer_id, shop, ticket_type, summary, buyer_confirmed)
    res = {"ok": False, "error": "BAD_ACTION", "message": "action 只能是 check_policy 或 create_ticket"}
    return {"result": json.dumps(res, ensure_ascii=False)}
