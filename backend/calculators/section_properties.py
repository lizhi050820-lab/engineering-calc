"""
截面几何性质计算器

依据：《材料力学》截面几何性质公式

功能：计算矩形、T形、圆形、环形、工字钢五种截面的
      面积、惯性矩、抵抗矩、回转半径、面积矩

支持截面形状:
  - 矩形 (rectangle):        b — 宽度, h — 高度
  - T形 (t-section):         b_f — 翼缘宽, h_f — 翼缘厚, b_w — 腹板宽, h — 总高
  - 圆形 (circle):            d — 直径
  - 环形 (annular):           D — 外径, d — 内径
  - 工字钢 (i-beam):         b_f — 翼缘宽, h — 总高, t_f — 翼缘厚, t_w — 腹板厚
"""

import numpy as np
from dataclasses import dataclass, field


# =============================================================================
# 输入 / 输出 数据结构
# =============================================================================

@dataclass
class SectionPropertiesInput:
    """截面几何性质计算输入"""
    shape: str           # "rectangle" | "t-section" | "circle" | "annular" | "i-beam"
    b: float = 0.0       # 宽度 (mm) — rectangle
    h: float = 0.0       # 截面总高度 (mm) — rectangle, t-section, i-beam
    b_f: float = 0.0     # 翼缘宽度 (mm) — t-section, i-beam
    h_f: float = 0.0     # 翼缘厚度 (mm) — t-section
    b_w: float = 0.0     # 腹板宽度 (mm) — t-section
    t_f: float = 0.0     # 翼缘厚度 (mm) — i-beam
    t_w: float = 0.0     # 腹板厚度 (mm) — i-beam
    d: float = 0.0       # 直径 (mm) — circle; 内径 (mm) — annular
    D: float = 0.0       # 外径 (mm) — annular


@dataclass
class SectionPropertiesResult:
    """截面几何性质计算结果"""
    shape: str            # 截面形状标识
    A: float              # 面积 (mm²)
    I_x: float            # 对x轴惯性矩 (mm⁴)
    I_y: float            # 对y轴惯性矩 (mm⁴)
    W_x: float            # 对x轴抵抗矩（截面系数）(mm³)
    W_y: float            # 对y轴抵抗矩（截面系数）(mm³)
    i_x: float            # 对x轴回转半径 (mm)
    i_y: float            # 对y轴回转半径 (mm)
    S_x: float            # 最大面积矩（对中性轴）(mm³)
    y_c: float = 0.0      # 形心距底边距离 (mm)，对称截面= h/2
    I_p: float = 0.0      # 极惯性矩 (mm⁴)，仅圆形/环形有意义
    status: str = "ok"
    message: str = ""
    steps: list = field(default_factory=list)


# =============================================================================
# 矩形截面
# =============================================================================

def _calc_rectangle(b: float, h: float):
    """计算矩形截面几何性质
    x轴 — 水平形心轴（平行于b）
    y轴 — 竖直形心轴（平行于h）
    """
    A = b * h
    I_x = b * h**3 / 12
    I_y = h * b**3 / 12
    W_x = b * h**2 / 6
    W_y = h * b**2 / 6
    i_x = h / np.sqrt(12)
    i_y = b / np.sqrt(12)
    S_x = b * h**2 / 8   # 半截面对中性轴的面积矩
    y_c = h / 2
    I_p = I_x + I_y
    return A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p


# =============================================================================
# T形截面
# =============================================================================

def _calc_t_section(b_f: float, h_f: float, b_w: float, h: float):
    """计算T形截面几何性质（平行移轴定理）
    x轴 — 水平形心轴
    y轴 — 对称轴（通过形心）
    T形: 翼缘在上方，腹板在下方
    """
    # 翼缘面积（上）和腹板面积（下）
    A_f = b_f * h_f
    A_w = b_w * (h - h_f)
    A = A_f + A_w

    # 形心距底边距离 y_c
    # 翼缘形心距底边: h - h_f/2
    # 腹板形心距底边: (h - h_f) / 2
    y_c_f = h - h_f / 2
    y_c_w = (h - h_f) / 2
    y_c = (A_f * y_c_f + A_w * y_c_w) / A

    # 对x轴惯性矩（平行移轴定理）
    d_f = y_c_f - y_c  # 翼缘形心到整体形心距离
    d_w = y_c - y_c_w  # 腹板形心到整体形心距离
    I_x_f = b_f * h_f**3 / 12 + A_f * d_f**2
    I_x_w = b_w * (h - h_f)**3 / 12 + A_w * d_w**2
    I_x = I_x_f + I_x_w

    # 对y轴惯性矩（y轴为对称轴）
    I_y = h_f * b_f**3 / 12 + (h - h_f) * b_w**3 / 12

    # 抵抗矩（取较小边距计算最大抵抗矩）
    y_top = h - y_c
    W_x_top = I_x / y_top
    W_x_bot = I_x / y_c
    W_x = min(W_x_top, W_x_bot)  # 取较小者作为控制抵抗矩
    W_y = I_y / (b_f / 2)

    # 回转半径
    i_x = np.sqrt(I_x / A)
    i_y = np.sqrt(I_y / A)

    # 最大面积矩（中性轴处，取中性轴以上或以下部分，取较大者）
    # 中性轴以上（含翼缘+部分腹板）对中性轴的面积矩
    if y_top <= h_f:
        # 中性轴在翼缘内（罕见：翼缘很厚）
        S_x = b_f * y_top**2 / 2
    else:
        # 中性轴在腹板内（常见情况）
        S_top = b_f * h_f * (y_top - h_f / 2) + b_w * (y_top - h_f)**2 / 2
        S_bot = b_w * y_c**2 / 2
        S_x = max(S_top, S_bot)

    I_p = I_x + I_y
    return A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p


# =============================================================================
# 圆形截面
# =============================================================================

def _calc_circle(d: float):
    """计算圆形截面几何性质"""
    A = np.pi * d**2 / 4
    I_x = np.pi * d**4 / 64
    I_y = I_x
    W_x = np.pi * d**3 / 32
    W_y = W_x
    i_x = d / 4
    i_y = i_x
    S_x = d**3 / 12   # 半圆对直径的面积矩
    y_c = d / 2
    I_p = np.pi * d**4 / 32   # 极惯性矩 = 2*I_x
    return A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p


# =============================================================================
# 环形截面
# =============================================================================

def _calc_annular(D: float, d_inner: float):
    """计算环形截面几何性质（D=外径, d_inner=内径）"""
    A = np.pi * (D**2 - d_inner**2) / 4
    I_x = np.pi * (D**4 - d_inner**4) / 64
    I_y = I_x
    W_x = np.pi * (D**4 - d_inner**4) / (32 * D)
    W_y = W_x
    i_x = np.sqrt(D**2 + d_inner**2) / 4
    i_y = i_x
    S_x = (D**3 - d_inner**3) / 12
    y_c = D / 2
    I_p = np.pi * (D**4 - d_inner**4) / 32
    return A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p


# =============================================================================
# 工字钢截面（双轴对称）
# =============================================================================

def _calc_i_beam(b_f: float, h: float, t_f: float, t_w: float):
    """计算工字钢截面几何性质（双轴对称）
    x轴 — 水平形心轴（强轴）
    y轴 — 竖直形心轴（弱轴，对称轴）
    """
    # 面积
    h_w = h - 2 * t_f   # 腹板净高
    A = 2 * b_f * t_f + h_w * t_w

    # 对x轴惯性矩（外矩形 - 腹板两侧空缺矩形）
    I_x = b_f * h**3 / 12 - (b_f - t_w) * h_w**3 / 12

    # 对y轴惯性矩（两个翼缘 + 腹板）
    I_y = 2 * (t_f * b_f**3 / 12) + h_w * t_w**3 / 12

    # 抵抗矩
    W_x = I_x / (h / 2)
    W_y = I_y / (b_f / 2)

    # 回转半径
    i_x = np.sqrt(I_x / A)
    i_y = np.sqrt(I_y / A)

    # 最大面积矩（中性轴处，取半截面对中性轴）
    # = 翼缘对中性轴的面积矩 + 半个腹板对中性轴的面积矩
    S_flange = b_f * t_f * (h / 2 - t_f / 2)
    S_web_half = t_w * (h_w / 2) * (h_w / 4)
    S_x = S_flange + S_web_half

    y_c = h / 2
    I_p = I_x + I_y
    return A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p


# =============================================================================
# 公共计算函数
# =============================================================================

SHAPE_NAMES = {
    "rectangle": "矩形",
    "t-section": "T形",
    "circle": "圆形",
    "annular": "环形",
    "i-beam": "工字钢",
}


def calculate_section_properties(inp: SectionPropertiesInput) -> SectionPropertiesResult:
    """计算截面几何性质"""
    shape = inp.shape.lower().strip()

    if shape not in SHAPE_NAMES:
        raise ValueError(
            f"不支持的截面形状: {shape}，可选: {list(SHAPE_NAMES.keys())}"
        )

    shape_cn = SHAPE_NAMES[shape]
    steps = []
    steps.append(f"=== {shape_cn}截面几何性质计算 ===")

    # 根据形状分发计算
    if shape == "rectangle":
        b = inp.b
        h = inp.h
        if b <= 0 or h <= 0:
            raise ValueError("矩形截面：请提供有效的宽度 b 和高度 h（> 0）")
        A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p = _calc_rectangle(b, h)
        steps.append(f"面积 A = b·h = {b:.0f}×{h:.0f} = {A:.1f} mm²")
        steps.append(f"惯性矩 I_x = b·h³/12 = {b:.0f}×{h:.0f}³/12 = {I_x:.0f} mm⁴")
        steps.append(f"惯性矩 I_y = h·b³/12 = {h:.0f}×{b:.0f}³/12 = {I_y:.0f} mm⁴")
        steps.append(f"抵抗矩 W_x = b·h²/6 = {b:.0f}×{h:.0f}²/6 = {W_x:.0f} mm³")
        steps.append(f"抵抗矩 W_y = h·b²/6 = {h:.0f}×{b:.0f}²/6 = {W_y:.0f} mm³")
        steps.append(f"回转半径 i_x = h/√12 = {h:.0f}/√12 = {i_x:.1f} mm")
        steps.append(f"回转半径 i_y = b/√12 = {b:.0f}/√12 = {i_y:.1f} mm")
        steps.append(f"面积矩 S_x = b·h²/8 = {b:.0f}×{h:.0f}²/8 = {S_x:.0f} mm³")
        steps.append(f"形心距底边 y_c = h/2 = {y_c:.1f} mm")
        steps.append(f"极惯性矩 I_p = I_x + I_y = {I_p:.0f} mm⁴")

    elif shape == "t-section":
        b_f, h_f, b_w, h = inp.b_f, inp.h_f, inp.b_w, inp.h
        if b_f <= 0 or h_f <= 0 or b_w <= 0 or h <= 0:
            raise ValueError("T形截面：请提供有效的 b_f, h_f, b_w, h（> 0）")
        if h_f >= h:
            raise ValueError(f"T形截面：翼缘厚度 h_f({h_f:.0f}) 应小于总高度 h({h:.0f})")
        if b_w > b_f:
            raise ValueError(f"T形截面：腹板宽度 b_w({b_w:.0f}) 应 ≤ 翼缘宽度 b_f({b_f:.0f})")
        A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p = _calc_t_section(b_f, h_f, b_w, h)
        steps.append(f"翼缘面积 A_f = b_f·h_f = {b_f:.0f}×{h_f:.0f} = {b_f*h_f:.1f} mm²")
        steps.append(f"腹板面积 A_w = b_w·(h-h_f) = {b_w:.0f}×{h-h_f:.0f} = {b_w*(h-h_f):.1f} mm²")
        steps.append(f"总面积 A = A_f + A_w = {A:.1f} mm²")
        steps.append(f"形心距底边 y_c = {y_c:.1f} mm")
        steps.append(f"惯性矩 I_x（平行移轴）= {I_x:.0f} mm⁴")
        steps.append(f"惯性矩 I_y = {I_y:.0f} mm⁴")
        steps.append(f"抵抗矩 W_x = {W_x:.0f} mm³（取较小边距）")
        steps.append(f"抵抗矩 W_y = {W_y:.0f} mm³")
        steps.append(f"回转半径 i_x = √(I_x/A) = {i_x:.1f} mm")
        steps.append(f"回转半径 i_y = √(I_y/A) = {i_y:.1f} mm")
        steps.append(f"面积矩 S_x = {S_x:.0f} mm³")

    elif shape == "circle":
        d = inp.d
        if d <= 0:
            raise ValueError("圆形截面：请提供有效的直径 d（> 0）")
        A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p = _calc_circle(d)
        steps.append(f"面积 A = π·d²/4 = π×{d:.0f}²/4 = {A:.1f} mm²")
        steps.append(f"惯性矩 I_x = I_y = π·d⁴/64 = {I_x:.0f} mm⁴")
        steps.append(f"抵抗矩 W_x = W_y = π·d³/32 = {W_x:.0f} mm³")
        steps.append(f"回转半径 i_x = i_y = d/4 = {d:.0f}/4 = {i_x:.1f} mm")
        steps.append(f"面积矩 S_x = d³/12 = {d:.0f}³/12 = {S_x:.0f} mm³")
        steps.append(f"极惯性矩 I_p = π·d⁴/32 = {I_p:.0f} mm⁴")

    elif shape == "annular":
        D = inp.D
        d_inner = inp.d
        if D <= 0 or d_inner <= 0:
            raise ValueError("环形截面：请提供有效的外径 D 和内径 d（> 0）")
        if d_inner >= D:
            raise ValueError(f"环形截面：内径 d({d_inner:.0f}) 应小于外径 D({D:.0f})")
        A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p = _calc_annular(D, d_inner)
        steps.append(f"面积 A = π·(D²-d²)/4 = π×({D:.0f}²-{d_inner:.0f}²)/4 = {A:.1f} mm²")
        steps.append(f"惯性矩 I_x = I_y = π·(D⁴-d⁴)/64 = {I_x:.0f} mm⁴")
        steps.append(f"抵抗矩 W_x = W_y = π·(D⁴-d⁴)/(32D) = {W_x:.0f} mm³")
        steps.append(f"回转半径 i_x = i_y = √(D²+d²)/4 = {i_x:.1f} mm")
        steps.append(f"面积矩 S_x = (D³-d³)/12 = {S_x:.0f} mm³")
        steps.append(f"极惯性矩 I_p = π·(D⁴-d⁴)/32 = {I_p:.0f} mm⁴")

    elif shape == "i-beam":
        b_f, h, t_f, t_w = inp.b_f, inp.h, inp.t_f, inp.t_w
        if b_f <= 0 or h <= 0 or t_f <= 0 or t_w <= 0:
            raise ValueError("工字钢截面：请提供有效的 b_f, h, t_f, t_w（> 0）")
        if 2 * t_f >= h:
            raise ValueError(f"工字钢截面：翼缘总厚 2·t_f({2*t_f:.0f}) 应小于总高度 h({h:.0f})")
        if t_w > b_f:
            raise ValueError(f"工字钢截面：腹板厚度 t_w({t_w:.0f}) 应 ≤ 翼缘宽度 b_f({b_f:.0f})")
        A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p = _calc_i_beam(b_f, h, t_f, t_w)
        h_w = h - 2 * t_f
        steps.append(f"腹板净高 h_w = h - 2·t_f = {h:.0f} - 2×{t_f:.0f} = {h_w:.0f} mm")
        steps.append(f"面积 A = 2·b_f·t_f + h_w·t_w = {A:.1f} mm²")
        steps.append(f"惯性矩 I_x（强轴）= {I_x:.0f} mm⁴")
        steps.append(f"惯性矩 I_y（弱轴）= {I_y:.0f} mm⁴")
        steps.append(f"抵抗矩 W_x = I_x/(h/2) = {W_x:.0f} mm³")
        steps.append(f"抵抗矩 W_y = I_y/(b_f/2) = {W_y:.0f} mm³")
        steps.append(f"回转半径 i_x = √(I_x/A) = {i_x:.1f} mm")
        steps.append(f"回转半径 i_y = √(I_y/A) = {i_y:.1f} mm")
        steps.append(f"面积矩 S_x = {S_x:.0f} mm³（半截面对中性轴）")

    # 精度处理
    A = round(A, 1)
    I_x = round(I_x, 0)
    I_y = round(I_y, 0)
    W_x = round(W_x, 0)
    W_y = round(W_y, 0)
    i_x = round(i_x, 1)
    i_y = round(i_y, 1)
    S_x = round(S_x, 0)
    y_c = round(y_c, 1)
    I_p = round(I_p, 0)

    return SectionPropertiesResult(
        shape=shape,
        A=A,
        I_x=I_x,
        I_y=I_y,
        W_x=W_x,
        W_y=W_y,
        i_x=i_x,
        i_y=i_y,
        S_x=S_x,
        y_c=y_c,
        I_p=I_p,
        status="ok",
        message=f"{shape_cn}截面几何性质计算完成",
        steps=steps,
    )
