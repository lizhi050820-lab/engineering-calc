"""
斜截面受剪承载力计算

依据：《混凝土结构设计规范》GB/T 50010-2010（2024年版）
章节：6.3 斜截面承载力计算

支持：
  - 均布荷载作用下配箍筋的受剪承载力
  - 集中荷载作用下配箍筋的受剪承载力
  - 设计模式：给定截面 → 计算混凝土项 V_c、截面限制 V_max、最小配箍率
  - 校核模式：给定箍筋 → 计算 V_cs、配箍率验算
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

from .bearing_capacity import CONCRETE_FC, CONCRETE_FT, REBAR_AREA

# =============================================================================
# 箍筋材料参数
# =============================================================================

# 箍筋抗拉强度设计值 f_yv (MPa)
# GB 50010-2010 表4.2.3-1: 用作受剪、受扭、受冲切承载力计算时
# HRB400 强度设计值取 360 MPa（不受 0.8 折减）
STIRRUP_FYV = {
    "HPB300": 270,
    "HRB400": 360,
}


def get_beta_c(concrete_grade: str) -> float:
    """获取混凝土强度影响系数 β_c（斜截面用）

    GB 50010-2010 第6.3.1条:
    C50及以下: β_c = 1.0
    C80: β_c = 0.8
    中间按线性插值
    """
    num = int(concrete_grade[1:])
    if num <= 50:
        return 1.0
    return max(0.8, round(1.0 - (num - 50) * 0.2 / 30, 2))


def get_beta_h(h0: float) -> float:
    """获取截面高度影响系数 β_h

    GB 50010-2010 第6.3.3条:
    h0 < 800mm: 取 h0 = 800mm, β_h = 1.0
    800 ≤ h0 ≤ 2000mm: β_h = (800/h0)^0.25
    h0 > 2000mm: 取 h0 = 2000mm 计算
    """
    if h0 < 800:
        h0_use = 800
    elif h0 > 2000:
        h0_use = 2000
    else:
        h0_use = h0
    return round((800 / h0_use) ** 0.25, 4)


# =============================================================================
# 输入 / 输出数据类
# =============================================================================

@dataclass
class ShearCapacityInput:
    """斜截面受剪承载力计算输入"""

    b: float                     # 截面宽度 (mm)
    h: float                     # 截面高度 (mm)
    concrete_grade: str          # 混凝土强度等级
    stirrup_grade: str = "HPB300"    # 箍筋牌号
    a_s: float = 40.0            # 纵向钢筋保护层厚度 (mm)
    load_type: Literal["uniform", "concentrated"] = "uniform"
    shear_span_ratio: Optional[float] = None  # 剪跨比 λ (集中荷载时必填, 1.5~3.0)

    # 校核模式 — 给定箍筋配置
    stirrup_diameter: Optional[float] = None  # 箍筋直径 (mm)
    stirrup_legs: int = 2                     # 箍筋肢数
    stirrup_spacing: Optional[float] = None   # 箍筋间距 (mm)


@dataclass
class ShearCapacityResult:
    """斜截面受剪承载力计算结果"""

    # 截面参数
    h0: float           # 有效高度 (mm)
    fc: float           # 混凝土抗压强度 (MPa)
    ft: float           # 混凝土抗拉强度 (MPa)
    f_yv: float          # 箍筋屈服强度 (MPa)
    beta_c: float       # 混凝土强度影响系数
    beta_h: float       # 截面高度影响系数

    # 承载力
    V_c: float          # 混凝土项受剪承载力 (kN)
    V_cs: float         # 配箍筋后受剪承载力 (kN), 未配箍筋时 = V_c
    V_max: float        # 截面限制条件 (kN), 防斜压破坏上限

    # 配箍
    A_sv: float         # 箍筋截面积 (mm²), n × A_sv1
    rho_sv: float       # 实际配箍率
    rho_sv_min: float   # 最小配箍率

    # 判定
    status: str         # "ok" | "insufficient" | "over_limit"
    message: str
    steps: list = field(default_factory=list)


# =============================================================================
# 计算函数
# =============================================================================

def calculate_shear_capacity(inp: ShearCapacityInput) -> ShearCapacityResult:
    """计算矩形截面斜截面受剪承载力"""
    steps = []

    # ---- 参数查表 ----
    fc = CONCRETE_FC.get(inp.concrete_grade)
    if fc is None:
        raise ValueError(f"不支持的混凝土等级: {inp.concrete_grade}")

    ft = CONCRETE_FT.get(inp.concrete_grade, 1.43)

    f_yv = STIRRUP_FYV.get(inp.stirrup_grade)
    if f_yv is None:
        raise ValueError(f"不支持的箍筋牌号: {inp.stirrup_grade}，可选: {list(STIRRUP_FYV.keys())}")

    h0 = inp.h - inp.a_s
    b = inp.b
    beta_c = get_beta_c(inp.concrete_grade)
    beta_h = get_beta_h(h0)

    steps.append(f"=== 斜截面受剪承载力计算 ===")
    steps.append(f"截面: b×h = {b:.0f}×{inp.h:.0f} mm, h₀ = {h0:.0f} mm")
    steps.append(f"材料: {inp.concrete_grade} (fc={fc}, ft={ft}), 箍筋 {inp.stirrup_grade} (fyv={f_yv})")
    steps.append(f"β_c = {beta_c}, β_h = {beta_h:.4f}")

    # ---- 截面限制条件 (防斜压破坏) ----
    V_max = 0.25 * beta_c * fc * b * h0 / 1000  # kN
    steps.append(f"\n1. 截面限制条件: V ≤ 0.25·β_c·fc·b·h₀")
    steps.append(f"   V_max = 0.25 × {beta_c} × {fc} × {b:.0f} × {h0:.0f} / 1000")
    steps.append(f"         = {V_max:.3f} kN")

    # ---- 混凝土项受剪承载力 ----
    if inp.load_type == "concentrated":
        lam = inp.shear_span_ratio
        if lam is None:
            raise ValueError("集中荷载时需提供剪跨比 λ (shear_span_ratio)")
        lam = max(1.5, min(3.0, lam))  # 规范限值
        V_c = (1.75 / (lam + 1)) * ft * b * h0 / 1000  # kN
        steps.append(f"\n2. 混凝土项 V_c (集中荷载, λ={lam:.1f}):")
        steps.append(f"   V_c = 1.75/(λ+1) · ft · b · h₀")
        steps.append(f"       = 1.75/({lam:.1f}+1) × {ft} × {b:.0f} × {h0:.0f} / 1000")
    else:
        V_c = 0.7 * beta_h * ft * b * h0 / 1000  # kN
        steps.append(f"\n2. 混凝土项 V_c (均布荷载):")
        steps.append(f"   V_c = 0.7 · β_h · ft · b · h₀")
        steps.append(f"       = 0.7 × {beta_h:.4f} × {ft} × {b:.0f} × {h0:.0f} / 1000")

    steps.append(f"       = {V_c:.3f} kN")

    # ---- 最小配箍率 ----
    rho_sv_min = 0.24 * ft / f_yv
    steps.append(f"\n3. 最小配箍率: ρ_sv,min = 0.24·ft/fyv = 0.24×{ft}/{f_yv} = {rho_sv_min:.4f}")

    # ---- 箍筋计算 ----
    A_sv = 0.0
    rho_sv = 0.0
    V_cs = V_c
    status = "ok"
    message = ""

    if inp.stirrup_diameter and inp.stirrup_spacing:
        # 校核模式：给定箍筋，计算 V_cs
        single_area = REBAR_AREA.get(int(inp.stirrup_diameter))
        if single_area is None:
            raise ValueError(f"不支持的箍筋直径: {inp.stirrup_diameter}mm")

        A_sv = inp.stirrup_legs * single_area
        s = inp.stirrup_spacing
        rho_sv = A_sv / (b * s)

        V_sv = f_yv * A_sv / s * h0 / 1000  # kN, 箍筋项
        V_cs = V_c + V_sv

        steps.append(f"\n4. 配箍筋后受剪承载力:")
        steps.append(f"   箍筋: Φ{int(inp.stirrup_diameter)}@{int(s)}({inp.stirrup_legs}), A_sv = {inp.stirrup_legs}×{single_area} = {A_sv:.1f} mm²")
        steps.append(f"   配箍率 ρ_sv = A_sv/(b·s) = {A_sv:.1f}/({b:.0f}×{s:.0f}) = {rho_sv:.4f}")
        steps.append(f"   箍筋项 V_sv = fyv·A_sv/s·h₀ = {f_yv}×{A_sv:.1f}/{s:.0f}×{h0:.0f}/1000 = {V_sv:.3f} kN")
        steps.append(f"   V_cs = V_c + V_sv = {V_c:.3f} + {V_sv:.3f} = {V_cs:.3f} kN")

        # 验算
        if rho_sv < rho_sv_min:
            status = "insufficient"
            message = f"配箍率不足！ρ_sv={rho_sv:.4f} < ρ_sv,min={rho_sv_min:.4f}"
            steps.append(f"\n  ⚠ {message}")
        elif V_cs > V_max:
            status = "over_limit"
            message = f"超出截面限制！V_cs={V_cs:.3f} > V_max={V_max:.3f} kN"
            steps.append(f"\n  ⚠ {message}")
        else:
            message = f"满足规范要求，V_cs = {V_cs:.3f} kN"
            steps.append(f"\n  ✓ {message}")
    else:
        # 设计模式：仅输出混凝土项
        steps.append(f"\n4. 未配置箍筋时的承载力:")
        steps.append(f"   V_c = {V_c:.3f} kN（仅混凝土承担）")
        steps.append(f"\n  提示: 输入箍筋直径和间距可计算配箍后的 V_cs。")
        if V_c > V_max:
            status = "over_limit"
            message = f"V_c 超出截面限制，需增大截面"
        else:
            status = "ok"
            message = f"混凝土项 V_c = {V_c:.3f} kN, 截面限制 V_max = {V_max:.3f} kN"

    return ShearCapacityResult(
        h0=round(h0, 1),
        fc=fc, ft=ft,
        f_yv=f_yv,
        beta_c=beta_c,
        beta_h=beta_h,
        V_c=round(V_c, 3),
        V_cs=round(V_cs, 3),
        V_max=round(V_max, 3),
        A_sv=round(A_sv, 1),
        rho_sv=round(rho_sv, 4),
        rho_sv_min=round(rho_sv_min, 4),
        status=status,
        message=message,
        steps=steps,
    )
