"""
PDF 卡牌生成器 - 纸牌原型用

输出 A4 横向布局，每页 3×3 = 9 张卡，标准扑克牌大小（63mm×88mm）。
打印后剪裁即可手玩。

设计风格：海报化 / 复古军令档案
- 阵营色：法兰西蓝、普鲁士黑、俄罗斯墨绿
- 数值布局：左上角费用、左下攻击、右下血量
- 兵种符号：北约军事符号体系简化版
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white

from cards import (Faction, UnitType, Card, Line,
                   build_france_deck, build_prussia_deck, build_russia_deck)

# 注册中文字体（WenQuanYi 是 TrueType collection，subfontIndex=0 取第一个）
pdfmetrics.registerFont(TTFont("NotoSC", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("NotoSC-Bold", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))

# ===== 配置 =====
CARD_W = 63 * mm   # 标准扑克牌宽
CARD_H = 88 * mm   # 标准扑克牌高
PAGE_W, PAGE_H = landscape(A4)  # 297×210 mm
COLS = 4
ROWS = 2
MARGIN_X = (PAGE_W - COLS * CARD_W) / 2
MARGIN_Y = (PAGE_H - ROWS * CARD_H) / 2

# ===== 阵营颜色 =====
FACTION_COLORS = {
    Faction.FRANCE:  HexColor("#2a4a8b"),   # 法兰西蓝
    Faction.PRUSSIA: HexColor("#1a1a1a"),   # 普鲁士黑
    Faction.RUSSIA:  HexColor("#2d5a3d"),   # 俄罗斯墨绿
}
FACTION_ACCENT = {
    Faction.FRANCE:  HexColor("#d4a55c"),
    Faction.PRUSSIA: HexColor("#c0c0c0"),
    Faction.RUSSIA:  HexColor("#c2552c"),
}
FACTION_NAME = {
    Faction.FRANCE:  "法 兰 西",
    Faction.PRUSSIA: "普 鲁 士",
    Faction.RUSSIA:  "俄 罗 斯",
}

# ===== 兵种符号（北约军事符号简化）=====
UNIT_SYMBOLS = {
    UnitType.INFANTRY:   "步",
    UnitType.CAVALRY:    "骑",
    UnitType.ARTILLERY:  "炮",
    UnitType.SKIRMISHER: "散",
    UnitType.GUARD:      "卫",
}
UNIT_LABEL = {
    UnitType.INFANTRY:   "步兵 INFANTRY",
    UnitType.CAVALRY:    "骑兵 CAVALRY",
    UnitType.ARTILLERY:  "炮兵 ARTILLERY",
    UnitType.SKIRMISHER: "散兵 SKIRMISHER",
    UnitType.GUARD:      "近卫 GUARD",
}
LINE_LABEL = {
    Line.SKIRMISH: "散兵线",
    Line.MAIN:     "主力线",
    Line.REAR:     "后方线",
}

# ===== 关键词解释（缩短，方便卡面）=====
KEYWORD_DESC = {
    "冲锋":     "部署当回合可立即行动",
    "结阵":     "受骑兵攻击伤害减半",
    "齐射":     "攻击前先造成1点先制",
    "远程":     "攻击不受反击",
    "闪避":     "首次受非炮兵攻击免疫",
    "突破":     "杀死目标后溢出打HQ",
    "守卫":     "敌方必须先攻击此单位",
    "侧翼迂回": "可越线攻击敌方后方",
    "自残1":    "部署时自损1点HQ",
    "自残2":    "部署时自损2点HQ",
    "光环+1攻": "其他友军永久+1攻击",
    "光环+1血": "其他友军永久+1血量",
}


def draw_card(c: canvas.Canvas, card: Card, x: float, y: float):
    """在 (x, y) 位置画一张卡，左下角为原点"""
    fc = FACTION_COLORS[card.faction]
    accent = FACTION_ACCENT[card.faction]
    parchment = HexColor("#f0e0bd")
    
    # === 卡面背景（羊皮纸色）===
    c.setFillColor(parchment)
    c.setStrokeColor(fc)
    c.setLineWidth(1.2)
    c.rect(x, y, CARD_W, CARD_H, fill=1, stroke=1)
    
    # === 阵营色顶栏（放大）===
    top_h = 11*mm
    c.setFillColor(fc)
    c.rect(x, y + CARD_H - top_h, CARD_W, top_h, fill=1, stroke=0)
    
    # 顶栏文字：阵营名（加大）
    c.setFillColor(white)
    c.setFont("NotoSC-Bold", 10)
    c.drawString(x + 12*mm, y + CARD_H - 7*mm, FACTION_NAME[card.faction])
    
    # 顶栏右侧：部署线
    c.setFillColor(accent)
    c.setFont("NotoSC", 7)
    c.drawRightString(x + CARD_W - 3*mm, y + CARD_H - 7*mm,
                      f"《{LINE_LABEL[card.deploy_line]}》")
    
    # === 费用印章（左上角，部分压在顶栏上）===
    cost_x = x + 7*mm
    cost_y = y + CARD_H - 7*mm
    c.setFillColor(HexColor("#8b3a1f"))
    c.setStrokeColor(parchment)
    c.setLineWidth(1.5)
    c.circle(cost_x, cost_y, 5*mm, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont("NotoSC-Bold", 13)
    c.drawCentredString(cost_x, cost_y - 1.8*mm, str(card.cost))
    
    # === 兵种大圆章（卡面中上部）===
    sym_x = x + CARD_W/2
    sym_y = y + CARD_H - 26*mm
    # 外圈装饰圆环
    c.setFillColor(fc)
    c.setStrokeColor(accent)
    c.setLineWidth(1.5)
    c.circle(sym_x, sym_y, 9*mm, fill=1, stroke=1)
    # 内圈
    c.setStrokeColor(parchment)
    c.setLineWidth(0.8)
    c.circle(sym_x, sym_y, 7.5*mm, fill=0, stroke=1)
    # 兵种字
    c.setFillColor(accent)
    c.setFont("NotoSC-Bold", 16)
    c.drawCentredString(sym_x, sym_y - 2.2*mm, UNIT_SYMBOLS[card.unit_type])
    
    # === 兵种类别（圆章下方）===
    c.setFillColor(fc)
    c.setFont("NotoSC", 7)
    c.drawCentredString(x + CARD_W/2, y + CARD_H - 39*mm, UNIT_LABEL[card.unit_type])
    
    # === 卡牌名称 ===
    c.setFillColor(black)
    c.setFont("NotoSC-Bold", 12)
    name = card.name
    text_width = c.stringWidth(name, "NotoSC-Bold", 12)
    if text_width > CARD_W - 8*mm:
        c.setFont("NotoSC-Bold", 10)
    c.drawCentredString(x + CARD_W/2, y + CARD_H - 47*mm, name)
    
    # 名称下分隔线
    c.setStrokeColor(fc)
    c.setLineWidth(0.4)
    c.line(x + 8*mm, y + CARD_H - 49*mm, x + CARD_W - 8*mm, y + CARD_H - 49*mm)
    
    # === 关键词列表 ===
    kw_y = y + CARD_H - 54*mm
    c.setFont("NotoSC", 7)
    c.setFillColor(HexColor("#3a2a1a"))
    visible_kws = [kw for kw in card.keywords if kw in KEYWORD_DESC]
    for kw in visible_kws[:5]:
        desc = KEYWORD_DESC[kw]
        c.setFillColor(fc)
        c.drawString(x + 4*mm, kw_y, "▸")
        c.setFillColor(HexColor("#3a2a1a"))
        c.drawString(x + 7*mm, kw_y, f"{kw}：{desc}")
        kw_y -= 3.6*mm
    
    # === 底部数值条 ===
    bar_y = y + 3*mm
    bar_h = 9*mm
    c.setFillColor(fc)
    c.rect(x + 2*mm, bar_y, CARD_W - 4*mm, bar_h, fill=1, stroke=0)
    
    # 攻击力（左下，用文字"攻"）
    c.setFillColor(accent)
    c.setFont("NotoSC-Bold", 10)
    c.drawString(x + 5*mm, bar_y + 3*mm, "攻")
    c.setFillColor(white)
    c.setFont("NotoSC-Bold", 18)
    c.drawString(x + 11*mm, bar_y + 2*mm, str(card.attack))
    
    # 中间分隔
    c.setStrokeColor(accent)
    c.setLineWidth(0.5)
    c.line(x + CARD_W/2, bar_y + 1.5*mm, x + CARD_W/2, bar_y + bar_h - 1.5*mm)
    
    # 血量（右下，用文字"防"）
    c.setFillColor(accent)
    c.setFont("NotoSC-Bold", 10)
    c.drawRightString(x + CARD_W - 11*mm, bar_y + 3*mm, "防")
    c.setFillColor(white)
    c.setFont("NotoSC-Bold", 18)
    c.drawRightString(x + CARD_W - 5*mm, bar_y + 2*mm, str(card.health))
    
    # === 装饰内边框 ===
    c.setStrokeColor(accent)
    c.setLineWidth(0.3)
    c.rect(x + 1.5*mm, y + 1.5*mm, CARD_W - 3*mm, CARD_H - 3*mm, fill=0, stroke=1)


def draw_card_back(c: canvas.Canvas, faction: Faction, x: float, y: float):
    """画卡背"""
    fc = FACTION_COLORS[faction]
    accent = FACTION_ACCENT[faction]
    
    c.setFillColor(fc)
    c.rect(x, y, CARD_W, CARD_H, fill=1, stroke=0)
    
    # 装饰边框
    c.setStrokeColor(accent)
    c.setLineWidth(2)
    c.rect(x + 4*mm, y + 4*mm, CARD_W - 8*mm, CARD_H - 8*mm, fill=0, stroke=1)
    
    # 内层框
    c.setLineWidth(0.5)
    c.rect(x + 7*mm, y + 7*mm, CARD_W - 14*mm, CARD_H - 14*mm, fill=0, stroke=1)
    
    # 阵营名（旋转 90°）
    c.setFillColor(accent)
    c.setFont("NotoSC-Bold", 24)
    c.saveState()
    c.translate(x + CARD_W/2, y + CARD_H/2)
    c.drawCentredString(0, 8, FACTION_NAME[faction])
    c.setFont("NotoSC", 9)
    c.drawCentredString(0, -6, "拿 · 破 · 仑 · 战 · 争")
    c.drawCentredString(0, -16, "RULE  PROTOTYPE")
    c.restoreState()


def draw_grid_lines(c: canvas.Canvas):
    """画剪裁辅助线（虚线）"""
    c.setStrokeColor(HexColor("#cccccc"))
    c.setLineWidth(0.2)
    c.setDash(2, 2)
    
    # 水平裁剪线
    for r in range(ROWS + 1):
        y_pos = MARGIN_Y + r * CARD_H
        c.line(MARGIN_X - 6*mm, y_pos, MARGIN_X, y_pos)
        c.line(PAGE_W - MARGIN_X, y_pos, PAGE_W - MARGIN_X + 6*mm, y_pos)
    
    # 垂直裁剪线
    for col in range(COLS + 1):
        x_pos = MARGIN_X + col * CARD_W
        c.line(x_pos, MARGIN_Y - 6*mm, x_pos, MARGIN_Y)
        c.line(x_pos, PAGE_H - MARGIN_Y, x_pos, PAGE_H - MARGIN_Y + 6*mm)
    
    c.setDash()  # 重置


def generate_deck_pdf(output_path: str):
    """生成完整卡牌 PDF"""
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    
    # 收集所有卡牌（去重保留每种 1 张作为参考，但实际游戏要按数量打印）
    decks = [
        (Faction.FRANCE,  build_france_deck()),
        (Faction.PRUSSIA, build_prussia_deck()),
        (Faction.RUSSIA,  build_russia_deck()),
    ]
    
    page_num = 0
    
    for faction, deck in decks:
        # 卡正面：每页 8 张
        cards_in_deck = list(deck)
        for page_start in range(0, len(cards_in_deck), COLS * ROWS):
            page_num += 1
            page_cards = cards_in_deck[page_start:page_start + COLS * ROWS]
            
            # 页眉
            c.setFillColor(HexColor("#888"))
            c.setFont("NotoSC", 8)
            c.drawString(MARGIN_X, PAGE_H - 6*mm,
                         f"{FACTION_NAME[faction]}  ·  正面  ·  Page {page_num}")
            c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 6*mm,
                              "拿破仑战争 · 规则原型 · 沿虚线剪裁")
            
            draw_grid_lines(c)
            
            for i, card in enumerate(page_cards):
                col = i % COLS
                row = i // COLS
                # 注意：reportlab 坐标系原点在左下，row 从上往下数
                cx = MARGIN_X + col * CARD_W
                cy = MARGIN_Y + (ROWS - 1 - row) * CARD_H
                draw_card(c, card, cx, cy)
            
            c.showPage()
    
    # === 卡背页（每个阵营 1 页）===
    for faction in [Faction.FRANCE, Faction.PRUSSIA, Faction.RUSSIA]:
        page_num += 1
        c.setFillColor(HexColor("#888"))
        c.setFont("NotoSC", 8)
        c.drawString(MARGIN_X, PAGE_H - 6*mm, f"{FACTION_NAME[faction]}  ·  卡背")
        c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 6*mm,
                          "（可选打印 · 双面对齐）")
        
        draw_grid_lines(c)
        
        for i in range(COLS * ROWS):
            col = i % COLS
            row = i // COLS
            cx = MARGIN_X + col * CARD_W
            cy = MARGIN_Y + (ROWS - 1 - row) * CARD_H
            draw_card_back(c, faction, cx, cy)
        
        c.showPage()
    
    # === 规则页 ===
    c.setFillColor(black)
    c.setFont("NotoSC-Bold", 18)
    c.drawCentredString(PAGE_W/2, PAGE_H - 20*mm, "拿破仑战争卡牌 · 规则速查")
    
    c.setFont("NotoSC", 10)
    rules = [
        "",
        "■ 战场结构",
        "  双方各有：后方线（炮兵）、主力线（步兵主战）。中间共享：散兵线（前压区）。",
        "  每条线最多容纳 4 个单位。",
        "",
        "■ 起始状态",
        "  双方 HQ 25 血。先手起手 4 张牌、2 军令；后手起手 6 张牌、2 军令。",
        "",
        "■ 回合流程",
        "  1. 抽 1 张牌    2. 军令 +1（封顶 10），重置为上限",
        "  3. 部署阶段：按卡牌费用消耗军令，部署到对应线",
        "  4. 前压阶段：消耗 1 军令把主力线步兵推到散兵线（炮兵不能前压）",
        "  5. 攻击阶段：场上单位攻击敌方目标",
        "",
        "■ 攻击规则",
        "  • 散兵线单位优先攻击敌方散兵线，否则打主力线",
        "  • 主力线单位必须先解决敌方散兵线",
        "  • 守卫单位必须被先攻击",
        "  • 远程炮兵从后方线攻击散兵 / 主力线，不受反击",
        "  • 远程炮兵打 HQ 需额外消耗 1 军令",
        "  • 直接攻击 HQ：仅当从散兵线发起、且敌方散兵+主力均空时",
        "",
        "■ 兵种克制",
        "  • 骑兵 vs 散开步兵：双倍伤害",
        "  • 骑兵 vs 方阵步兵（结阵）：伤害减半，方阵反击全额",
        "  • 炮兵 vs 密集步兵：+1 伤害",
        "",
        "■ 胜利条件",
        "  对方 HQ 血量降至 0。",
        "",
        "■ 推荐玩法",
        "  纸牌原型阶段建议：手牌公开打（用于发现规则问题），双方各取一副 30 张牌。",
        "  目标：每局 8-15 分钟内完成，关注'是否有真决策'而非'是否好看'。",
    ]
    
    text_y = PAGE_H - 32*mm
    for line in rules:
        if line.startswith("■"):
            c.setFont("NotoSC-Bold", 11)
            c.setFillColor(HexColor("#8b3a1f"))
        else:
            c.setFont("NotoSC", 10)
            c.setFillColor(black)
        c.drawString(MARGIN_X + 5*mm, text_y, line)
        text_y -= 5*mm
    
    c.showPage()
    
    c.save()
    print(f"✓ 已生成 {output_path}")
    print(f"  共 {page_num + 1} 页（含规则速查）")
    print(f"  每页 8 张卡（{COLS}×{ROWS}），标准扑克牌大小 63×88mm")
    print(f"  打印建议：A4 横向，无缩放，沿虚线剪裁")


if __name__ == "__main__":
    generate_deck_pdf("napoleon_cards.pdf")
