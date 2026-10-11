#!/usr/bin/env python3
"""
Circuit Theory — Interactive Presentation & Simulator
Built with PySide6
"""

import sys
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QLabel, QSlider, QTabWidget,
    QScrollArea, QFrame, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QPainterPath,
    QPolygonF, QLinearGradient, QRadialGradient
)

# ═══════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════
C_BG      = "#0d1117"
C_BG2     = "#161b22"
C_BG3     = "#1c2128"
C_TEXT    = "#e6edf3"
C_TEXT2   = "#8b949e"
C_ACCENT  = "#58a6ff"
C_GREEN   = "#3fb950"
C_ORANGE  = "#f0883e"
C_RED     = "#f85149"
C_PURPLE  = "#bc8cff"
C_WIRE    = "#6e7681"
C_ELEC    = "#79c0ff"
C_GRID    = "#151b23"
C_BORDER  = "#30363d"
C_BTN     = "#1f6feb"
C_YELLOW  = "#e3b341"

STYLESHEET = f"""
QMainWindow {{ background: {C_BG}; }}
QWidget {{ color: {C_TEXT}; font-family: 'Segoe UI', 'Arial', sans-serif; }}
QScrollArea {{ background: {C_BG}; border: none; }}
QScrollBar:vertical {{ background: {C_BG}; width: 8px; }}
QScrollBar::handle:vertical {{ background: {C_BG3}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QSlider::groove:horizontal {{ height: 5px; background: {C_BG3}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 16px; height: 16px; margin: -6px 0;
    background: {C_ACCENT}; border-radius: 8px; }}
QSlider::sub-page:horizontal {{ background: {C_ACCENT}; border-radius: 2px; }}
QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_BG}; border-radius: 0 0 8px 8px; }}
QTabBar::tab {{ background: {C_BG2}; color: {C_TEXT2}; padding: 10px 24px;
    border: 1px solid {C_BORDER}; border-bottom: none;
    border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 13px; }}
QTabBar::tab:selected {{ background: {C_BG}; color: {C_ACCENT}; border-bottom: 2px solid {C_ACCENT}; }}
"""


# ═══════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════
class Wire:
    def __init__(self, x1, y1, x2, y2, current=1.0):
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        self.current = float(current)
        self.length = math.hypot(x2 - x1, y2 - y1)


class Comp:
    def __init__(self, kind, x1, y1, x2, y2, label="", value=""):
        self.kind = kind
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        self.label, self.value = label, value

    @property
    def cx(self): return (self.x1 + self.x2) / 2
    @property
    def cy(self): return (self.y1 + self.y2) / 2
    @property
    def horizontal(self): return abs(self.y2 - self.y1) < 2
    @property
    def vertical(self): return abs(self.x2 - self.x1) < 2


# ═══════════════════════════════════════════════════════════
# CIRCUIT CANVAS — animated circuit visualisation
# ═══════════════════════════════════════════════════════════
class CircuitCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(660, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.wires = []
        self.components = []
        self.info = []
        self.junctions = []
        self.phase = 0.0
        self.speed = 0.006
        self.on = True
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
        self._t.start(30)

    def _tick(self):
        if self.on:
            self.phase = (self.phase + self.speed) % 1.0
        self.update()

    def clear(self):
        self.wires.clear(); self.components.clear()
        self.info.clear(); self.junctions.clear()

    # ── circuit setups ──────────────────────────
    def setup_simple(self, V=5.0, R=100.0):
        self.clear(); self.on = True
        I = V / R
        self.speed = 0.003 + 0.012 * min(I, 0.5)
        self.wires = [
            Wire(110, 110, 510, 110), Wire(510, 110, 510, 290),
            Wire(510, 290, 110, 290), Wire(110, 290, 110, 110)]
        self.components = [
            Comp('resistor', 220, 110, 400, 110, 'R', f'{R:.0f} Ω'),
            Comp('battery', 110, 265, 110, 135, 'V', f'{V:.1f} V')]
        self.info = [(f'I = {I*1000:.1f} mA', 270, 165),
                     (f'P = {V*I*1000:.1f} mW', 270, 185)]

    def setup_series(self, V=12.0, R1=100.0, R2=200.0):
        self.clear(); self.on = True
        Rt = R1 + R2; I = V / Rt
        self.speed = 0.003 + 0.012 * min(I, 0.5)
        V1, V2 = I * R1, I * R2
        self.wires = [
            Wire(100, 100, 530, 100), Wire(530, 100, 530, 300),
            Wire(530, 300, 100, 300), Wire(100, 300, 100, 100)]
        self.components = [
            Comp('resistor', 155, 100, 280, 100, 'R₁', f'{R1:.0f} Ω'),
            Comp('resistor', 350, 100, 475, 100, 'R₂', f'{R2:.0f} Ω'),
            Comp('battery', 100, 270, 100, 130, 'V', f'{V:.1f} V')]
        self.info = [
            (f'I = {I*1000:.1f} mA', 270, 150),
            (f'V₁ = {V1:.2f} V', 218, 78), (f'V₂ = {V2:.2f} V', 413, 78),
            (f'R_total = {Rt:.0f} Ω   P = {V*I*1000:.1f} mW', 180, 340)]

    def setup_parallel(self, V=12.0, R1=200.0, R2=300.0):
        self.clear(); self.on = True
        I1, I2 = V / R1, V / R2
        It = I1 + I2; Req = 1 / (1/R1 + 1/R2)
        self.speed = 0.003 + 0.012 * min(It, 0.5)
        r1, r2 = I1 / It, I2 / It
        self.wires = [
            Wire(520, 330, 520, 200, 1.0),
            Wire(520, 200, 100, 200, r2),
            Wire(520, 200, 520, 80, r1),
            Wire(520, 80, 100, 80, r1),
            Wire(100, 80, 100, 200, r1),
            Wire(100, 200, 100, 330, 1.0),
            Wire(100, 330, 520, 330, 1.0)]
        self.components = [
            Comp('resistor', 200, 80, 420, 80, 'R₁', f'{R1:.0f} Ω'),
            Comp('resistor', 200, 200, 420, 200, 'R₂', f'{R2:.0f} Ω'),
            Comp('battery', 250, 330, 370, 330, 'V', f'{V:.1f} V')]
        self.junctions = [(100, 200), (520, 200)]
        self.info = [
            (f'I₁ = {I1*1000:.1f} mA', 265, 62),
            (f'I₂ = {I2*1000:.1f} mA', 265, 182),
            (f'I_total = {It*1000:.1f} mA', 220, 372),
            (f'R_eq = {Req:.1f} Ω', 420, 372)]

    def setup_kirchhoff(self):
        self.clear(); self.on = False
        self.wires = [
            Wire(100, 80, 310, 80), Wire(310, 80, 520, 80),
            Wire(520, 80, 520, 280), Wire(520, 280, 310, 280),
            Wire(310, 280, 100, 280), Wire(100, 280, 100, 80),
            Wire(310, 80, 310, 280)]
        self.components = [
            Comp('resistor', 145, 80, 265, 80, 'R₁', '100 Ω'),
            Comp('resistor', 355, 80, 475, 80, 'R₂', '200 Ω'),
            Comp('resistor', 310, 135, 310, 225, 'R₃', '150 Ω'),
            Comp('battery', 100, 245, 100, 115, 'V', '12 V')]
        self.junctions = [(310, 80), (310, 280)]
        self.info = [
            ('KVL Loop 1:  V − I₁R₁ − (I₁−I₂)R₃ = 0', 130, 325),
            ('KVL Loop 2:  (I₁−I₂)R₃ − I₂R₂ = 0', 130, 350),
            ('KCL at node B:  I₁ = I_R₃ + I₂', 130, 375)]

    # ── painting ────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # background gradient
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(C_BG)); bg.setColorAt(1, QColor("#0a0e14"))
        p.fillRect(self.rect(), bg)
        self._grid(p, w, h)
        self._wires(p)
        if self.on: self._electrons(p)
        self._comps(p)
        self._junctions(p)
        if self.on: self._arrows(p)
        self._labels(p)
        p.end()

    def _grid(self, p, w, h):
        p.setPen(QPen(QColor(C_GRID), 0.5))
        for x in range(0, w, 30): p.drawLine(x, 0, x, h)
        for y in range(0, h, 30): p.drawLine(0, y, w, y)

    def _wires(self, p):
        pen = QPen(QColor(C_WIRE), 2.5, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for s in self.wires:
            p.drawLine(QPointF(s.x1, s.y1), QPointF(s.x2, s.y2))

    def _electrons(self, p):
        for s in self.wires:
            if s.current < 0.01: continue
            n = max(2, int(s.length / 38 * s.current))
            for i in range(n):
                t = (self.phase * s.current * 3.0 + i / n) % 1.0
                ex = s.x1 + t * (s.x2 - s.x1)
                ey = s.y1 + t * (s.y2 - s.y1)
                gc = QColor(C_ELEC); gc.setAlpha(30)
                p.setPen(Qt.NoPen); p.setBrush(gc)
                p.drawEllipse(QPointF(ex, ey), 10, 10)
                p.setBrush(QColor(C_ELEC))
                p.drawEllipse(QPointF(ex, ey), 3.2, 3.2)

    def _comps(self, p):
        for c in self.components:
            getattr(self, f'_draw_{c.kind}')(p, c)

    def _draw_resistor(self, p, c):
        p.setPen(Qt.NoPen); p.setBrush(QColor(C_BG))
        if c.horizontal:
            p.drawRect(QRectF(c.x1 - 4, c.y1 - 20, c.x2 - c.x1 + 8, 40))
        else:
            p.drawRect(QRectF(c.x1 - 20, c.y1 - 4, 40, c.y2 - c.y1 + 8))
        path = QPainterPath()
        col = QColor(C_ORANGE)
        p.setPen(QPen(col, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        if c.horizontal:
            x1, y, x2 = c.x1, c.y1, c.x2
            m = 22; zx1, zx2 = x1 + m, x2 - m
            nz = 6; zw = (zx2 - zx1) / (nz * 2); zh = 11
            path.moveTo(x1, y); path.lineTo(zx1, y)
            for i in range(nz * 2):
                path.lineTo(zx1 + (i + 1) * zw, y + (zh if i % 2 == 0 else -zh))
            path.lineTo(zx2, y); path.lineTo(x2, y)
        else:
            x, y1, y2 = c.x1, c.y1, c.y2
            m = 22; zy1, zy2 = y1 + m, y2 - m
            nz = 6; zh = (zy2 - zy1) / (nz * 2); zw = 11
            path.moveTo(x, y1); path.lineTo(x, zy1)
            for i in range(nz * 2):
                path.lineTo(x + (zw if i % 2 == 0 else -zw), zy1 + (i + 1) * zh)
            path.lineTo(x, zy2); path.lineTo(x, y2)
        p.drawPath(path)
        self._comp_label(p, c)

    def _draw_battery(self, p, c):
        p.setPen(Qt.NoPen); p.setBrush(QColor(C_BG))
        if c.horizontal:
            p.drawRect(QRectF(c.x1 - 4, c.y1 - 22, c.x2 - c.x1 + 8, 44))
        else:
            p.drawRect(QRectF(c.x1 - 22, c.y1 - 4, 44, c.y2 - c.y1 + 8))
        col = QColor(C_GREEN)
        if c.horizontal:
            x1, y, x2 = c.x1, c.y1, c.x2
            mx = (x1 + x2) / 2; g = 8
            p.setPen(QPen(col, 3))
            p.drawLine(QPointF(mx - g, y - 17), QPointF(mx - g, y + 17))
            p.setPen(QPen(col, 2))
            p.drawLine(QPointF(mx + g, y - 10), QPointF(mx + g, y + 10))
            p.setPen(QPen(QColor(C_WIRE), 2.5))
            p.drawLine(QPointF(x1, y), QPointF(mx - g, y))
            p.drawLine(QPointF(mx + g, y), QPointF(x2, y))
            p.setPen(col); p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.drawText(QPointF(mx - g - 16, y + 5), "+")
            p.drawText(QPointF(mx + g + 4, y + 5), "−")
        else:
            x, y1, y2 = c.x1, c.y1, c.y2
            my = (y1 + y2) / 2; g = 8
            p.setPen(QPen(col, 3))
            p.drawLine(QPointF(x - 17, my - g), QPointF(x + 17, my - g))
            p.setPen(QPen(col, 2))
            p.drawLine(QPointF(x - 10, my + g), QPointF(x + 10, my + g))
            p.setPen(QPen(QColor(C_WIRE), 2.5))
            p.drawLine(QPointF(x, y1), QPointF(x, my - g))
            p.drawLine(QPointF(x, my + g), QPointF(x, y2))
            p.setPen(col); p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.drawText(QPointF(x + 20, my - g + 5), "+")
            p.drawText(QPointF(x + 14, my + g + 5), "−")
        self._comp_label(p, c)

    def _draw_led(self, p, c):
        p.setPen(Qt.NoPen); p.setBrush(QColor(C_BG))
        if c.horizontal:
            p.drawRect(QRectF(c.x1 - 4, c.y1 - 18, c.x2 - c.x1 + 8, 36))
        else:
            p.drawRect(QRectF(c.x1 - 18, c.y1 - 4, 36, c.y2 - c.y1 + 8))
        col = QColor(C_RED); p.setPen(QPen(col, 2.5)); p.setBrush(Qt.NoBrush)
        if c.horizontal:
            x1, y, x2 = c.x1, c.y1, c.x2
            mx = (x1 + x2) / 2; sz = 14
            p.drawLine(QPointF(x1, y), QPointF(mx - sz, y))
            p.drawLine(QPointF(mx - sz, y), QPointF(mx + sz, y))
            tri = QPolygonF([QPointF(mx - sz, y - sz), QPointF(mx - sz, y + sz), QPointF(mx + sz, y)])
            p.setBrush(QColor(C_RED).lighter(140)); p.drawPolygon(tri)
            p.drawLine(QPointF(mx + sz, y - sz), QPointF(mx + sz, y + sz))
            p.drawLine(QPointF(mx + sz, y), QPointF(x2, y))
            # arrows for light emission
            for dy in [-8, 0, 8]:
                ax = mx + 4; ay = y + dy
                p.setPen(QPen(QColor(C_RED).lighter(160), 1))
                p.drawLine(QPointF(ax, ay), QPointF(ax + 10, ay - 6))
                p.drawLine(QPointF(ax + 10, ay - 6), QPointF(ax + 7, ay - 4))
                p.drawLine(QPointF(ax + 10, ay - 6), QPointF(ax + 9, ay - 2))
        else:
            x, y1, y2 = c.x1, c.y1, c.y2
            my = (y1 + y2) / 2; sz = 14
            p.drawLine(QPointF(x, y1), QPointF(x, my - sz))
            p.drawLine(QPointF(x, my - sz), QPointF(x, my + sz))
            tri = QPolygonF([QPointF(x - sz, my - sz), QPointF(x + sz, my - sz), QPointF(x, my + sz)])
            p.setBrush(QColor(C_RED).lighter(140)); p.drawPolygon(tri)
            p.drawLine(QPointF(x - sz, my + sz), QPointF(x + sz, my + sz))
            p.drawLine(QPointF(x, my + sz), QPointF(x, y2))
        p.setBrush(Qt.NoBrush)
        self._comp_label(p, c)

    def _comp_label(self, p, c):
        if c.label:
            p.setPen(QColor(C_TEXT)); p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            if c.horizontal:
                p.drawText(QPointF(c.cx - len(c.label)*3.5, c.cy - 22), c.label)
            else:
                p.drawText(QPointF(c.cx + 20, c.cy + 5), c.label)
        if c.value:
            p.setPen(QColor(C_TEXT2)); p.setFont(QFont("Consolas", 9))
            if c.horizontal:
                p.drawText(QPointF(c.cx - len(c.value)*3, c.cy + 32), c.value)
            else:
                p.drawText(QPointF(c.cx + 20, c.cy + 20), c.value)

    def _junctions(self, p):
        p.setPen(Qt.NoPen); p.setBrush(QColor(C_WIRE))
        for jx, jy in self.junctions:
            p.drawEllipse(QPointF(jx, jy), 5, 5)

    def _arrows(self, p):
        p.setPen(Qt.NoPen); p.setBrush(QColor(C_ACCENT))
        for s in self.wires:
            if s.current < 0.01 or s.length < 50: continue
            mx = (s.x1 + s.x2) / 2; my = (s.y1 + s.y2) / 2
            a = math.atan2(s.y2 - s.y1, s.x2 - s.x1); sz = 6
            p.drawPolygon(QPolygonF([
                QPointF(mx + sz * math.cos(a), my + sz * math.sin(a)),
                QPointF(mx + sz * math.cos(a + 2.5), my + sz * math.sin(a + 2.5)),
                QPointF(mx + sz * math.cos(a - 2.5), my + sz * math.sin(a - 2.5))]))

    def _labels(self, p):
        p.setPen(QColor(C_YELLOW)); p.setFont(QFont("Consolas", 10))
        for txt, x, y in self.info:
            p.drawText(QPointF(x, y), txt)


# ═══════════════════════════════════════════════════════════
# SLIDE HELPERS
# ═══════════════════════════════════════════════════════════
def text_slide(html):
    sa = QScrollArea(); sa.setWidgetResizable(True)
    lb = QLabel(); lb.setWordWrap(True); lb.setTextFormat(Qt.RichText)
    lb.setText(html)
    lb.setStyleSheet(f"QLabel{{color:{C_TEXT};background:transparent;padding:40px 50px;}}")
    sa.setWidget(lb); return sa


CTRL_STYLE = f"""
QWidget#ctrl {{background:{C_BG2};border-top:1px solid {C_BORDER};}}
QLabel{{color:{C_TEXT2};font-size:12px;}}
QLabel#val{{color:{C_ACCENT};font-size:13px;font-weight:bold;min-width:75px;}}
QLabel#heading{{color:{C_TEXT};font-size:14px;font-weight:bold;padding:4px 0;}}
"""


def make_slider_row(label_text, lo, hi, val, suffix, callback):
    row = QWidget()
    lay = QHBoxLayout(row); lay.setContentsMargins(0, 2, 0, 2)
    lbl = QLabel(label_text); lbl.setObjectName("heading"); lbl.setFixedWidth(90)
    sl = QSlider(Qt.Horizontal); sl.setRange(lo, hi); sl.setValue(val)
    vl = QLabel(f"{val} {suffix}"); vl.setObjectName("val"); vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    sl.valueChanged.connect(lambda v: (vl.setText(f"{v} {suffix}"), callback(v)))
    lay.addWidget(lbl); lay.addWidget(sl, 1); lay.addWidget(vl)
    return row, sl


# ═══════════════════════════════════════════════════════════
# INTERACTIVE PAGES
# ═══════════════════════════════════════