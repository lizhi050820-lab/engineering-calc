"""
正截面承载力计算（受弯构件）

依据：《混凝土结构设计规范》GB/T 50010-2010（2024年版）
章节：6.2 正截面承载力计算

支持：
  - 单筋矩形截面 (single reinforcement)
  - 双筋矩形截面 (double reinforcement)
  - 校核模式：给定配筋 → 计算承载力 Mu
  - 设计模式：给定截面 → 输出最小/经济/最大三档配筋方案
"""

import numpy as np
from dataclasses import dataclass
from typing import Literal, Optional

# =============================================================================
# 材料参数数据库
# =============================================================================

# 混凝土轴心抗压强度设计值 fc (N/mm² = MPa)
CONCRETE_FC = {
    "C20": 9.6,
    "C25": 11.9,
    "C30": 14.3,
    "C35": 16.7,
    "C40": 19.1,
    "C45": 21.1,
    "C50": 23.1,
    "C55": 25.3,
    "C60": 27.5,
    "C65": 29.7,
    "C70": 31.8,
    "C75": 33.8,
    "C80": 35.9,
}

# 混凝土轴心抗拉强度设计值 ft (MPa)
CONCRETE_FT = {
    "C20": 1.10,
    "C25": 1.27,
    "C30": 1.43,
    "C35": 1.57,
    "C40": 1.71,
    "C45": 1.80,
    "C50": 1.89,
    "C55": 1.96,
    "C60": 2.04,
    "C65": 2.09,
    "C70": 2.14,
    "C75": 2.18,
    "C80": 2.22,
}

# α₁ 系数：C50及以下为 1.0，C55-C80 按线性插值
# GB 50010-2010 第6.2.6条: α₁ = 1.00 - (f_cu,k - 50) × (1.00 - 0.94) / 30
ALPHA1_BASE = {f"C{i*5}": 1.0 for i in range(5, 11)}  # C25-C50
for i in range(55, 85, 5):
    ALPHA1_BASE[f"C{i}"] = round(1.00 - (i - 50) * 0.06 / 30, 2)

# 钢筋抗拉强度设计值 fy (MPa)
REBAR_FY = {
    "HPB300": 270,
    "HRB400": 360,
    "HRB500": 435,
}

# 钢筋弹性模量 Es (×10⁵ MPa)
REBAR_ES = {
    "HPB300": 2.10,
    "HRB400": 2.00,
    "HRB500": 2.00,
}

# 相对界限受压区高度 ξb (C50及以下的参考值，仅供参考)
# C55及以上应使用 get_xi_b() 动态计算
# 公式: ξb = β₁ / (1 + fy / (Es × εcu))
XI_B = {
    "HPB300": 0.576,
    "HRB400": 0.518,
    "HRB500": 0.482,
}

# 常用钢筋公称直径及面积表 (mm²)
# 直径 → 单根面积
REBAR_AREA = {
    6: 28.3, 8: 50.3, 10: 78.5, 12: 113.1,
    14: 153.9, 16: 201.1, 18: 254.5, 20: 314.2,
    22: 380.1, 25: 490.9, 28: 615.8, 32: 804.2,
    36: 1017.9, 40: 1256.6,
}

# 最小配筋率 ρ_min: max(0.2%, 0.45 * ft / fy)
# 最大配筋率 ρ_max (单筋, 受压区达到 ξb): ρ_max = ξb * α₁ * fc / fy


def get_alpha1(concrete_grade: str) -> float:
    """获取受压区混凝土应力图形系数 α₁"""
    if concrete_grade in ALPHA1_BASE:
        return ALPHA1_BASE[concrete_grade]
    # C55以上线性插值
    num = int(concrete_grade[1:])
    if 50 < num < 55:
        return 1.0
    if 55 <= num <= 80:
        lower = (num // 5) * 5
        upper = min(lower + 5, 80)
        alpha_lower = ALPHA1_BASE[f"C{lower}"]
        alpha_upper = ALPHA1_BASE[f"C{upper}"]
        return alpha_lower + (alpha_upper - alpha_lower) * (num - lower) / (upper - lower)
    return 1.0  # fallback


def get_beta1(concrete_grade: str) -> float:
    """获取等效矩形应力图系数 β₁"""
    num = int(concrete_grade[1:])
    if num <= 50:
        return 0.8
    return max(0.74, 0.8 - (num - 50) * 0.002)  # 每增加5MPa减0.01, 最少0.74


def get_epsilon_cu(concrete_grade: str) -> float:
    """获取混凝土极限压应变 εcu

    GB 50010-2010 第6.2.1条:
    εcu = 0.0033 - (f_cu,k - 50) × 10^(-5)
    """
    f_cuk = int(concrete_grade[1:])
    if f_cuk <= 50:
        return 0.0033
    return 0.0033 - (f_cuk - 50) * 1e-5


def get_xi_b(concrete_grade: str, rebar_grade: str) -> float:
    """获取相对界限受压区高度 ξb (动态计算)

    公式: ξb = β₁ / (1 + fy / (Es × εcu))

    C50及以下与硬编码表值一致:
      HPB300: 0.576, HRB400: 0.518, HRB500: 0.482
    C55+ 时 ξb 因 β₁ 和 εcu 减小而降低。
    """
    beta1 = get_beta1(concrete_grade)
    epsilon_cu = get_epsilon_cu(concrete_grade)
    fy = REBAR_FY[rebar_grade]
    Es = REBAR_ES[rebar_grade] * 1e5  # 转换为 MPa (数据库中存的是 ×10⁵ MPa)
    return beta1 / (1 + fy / (Es * epsilon_cu))


@dataclass
class BearingCapacityInput:
    """正截面承载力计算输入参数"""

    b: float  # 截面宽度 (mm)
    h: float  # 截面高度 (mm)
    concrete_grade: str  # 混凝土强度等级, e.g. "C30"
    rebar_grade: str  # 钢筋牌号, e.g. "HRB400"
    a_s: float = 40.0  # 受拉钢筋合力点至受拉边缘距离 (mm)
    a_s_prime: float = 40.0  # 受压钢筋合力点至受压边缘距离 (双筋时使用)
    as_type: Literal["single", "double"] = "single"  # 单筋/双筋截面
    as_given: Optional[float] = None  # 已知受拉钢筋面积 (mm²), 校核模式
    as_prime_given: Optional[float] = None  # 已知受压钢筋面积 (mm²)


@dataclass
class BearingCapacityResult:
    """正截面承载力计算结果"""

    # 截面参数
    h0: float  # 截面有效高度 (mm)
    fc: float  # 混凝土抗压强度设计值 (MPa)
    fy: float  # 钢筋抗拉强度设计值 (MPa)
    alpha1: float  # 受压区混凝土应力图形系数

    # 界限
    xi_b: float  # 相对界限受压区高度
    rho_min: float  # 最小配筋率
    rho_max: float  # 最大配筋率 (单筋)

    # 计算结果 - 校核模式 (给定配筋求承载力)
    x: float  # 受压区高度 (mm)
    xi: float  # 相对受压区高度 ξ = x/h₀
    as_req: float  # 所需受拉钢筋面积 (mm²)
    mu: float  # 极限弯矩 (kN·m)

    # 判定
    status: str  # "ok" | "over_reinforced" | "under_reinforced" | "invalid"
    message: str  # 中文判定信息

    # 计算过程
    steps: list  # 计算步骤记录

    # 设计模式 — 三档配筋方案 (仅设计模式有值，校核模式为 None)
    design_points: list = None  # [{label, rho, As, x, xi, Mu, note}, ...]


def _calc_single_reinforced(inp: BearingCapacityInput, fc: float, fy: float,
                            alpha1: float, xi_b: float, rho_min: float,
                            h0: float) -> BearingCapacityResult:
    """单筋矩形截面正截面承载力计算"""
    b = inp.b
    steps = []

    # 若已知钢筋面积（校核模式），直接计算承载力
    if inp.as_given is not None:
        As = inp.as_given
        steps.append(f"已知受拉钢筋面积 As = {As:.1f} mm²")
        steps.append(f"由力平衡: α₁·fc·b·x = fy·As")
        x = fy * As / (alpha1 * fc * b)
        steps.append(f"  x = fy·As/(α₁·fc·b) = {fy}×{As:.1f}/({alpha1}×{fc}×{b:.0f}) = {x:.2f} mm")
        xi = x / h0
        steps.append(f"  ξ = x/h₀ = {x:.2f}/{h0:.0f} = {xi:.4f}")

        # 计算极限弯矩
        mu_n_mm = alpha1 * fc * b * x * (h0 - x / 2)  # N·mm
        mu = mu_n_mm / 1e6  # 转为 kN·m
        steps.append(f"由力矩平衡: Mu = α₁·fc·b·x·(h₀-x/2)")
        steps.append(f"  Mu = {alpha1}×{fc}×{b:.0f}×{x:.2f}×({h0:.0f}-{x:.2f}/2)")
        steps.append(f"     = {mu:.2f} kN·m")

        # 判定
        if xi > xi_b:
            status = "over_reinforced"
            message = f"超筋！ξ = {xi:.4f} > ξb = {xi_b:.4f}，应增大截面或采用双筋截面"
        elif As / (b * inp.h) < rho_min:
            status = "under_reinforced"
            message = f"少筋！配筋率 ρ = {As/(b*inp.h):.4f} < ρ_min = {rho_min:.4f}"
        else:
            status = "ok"
            message = f"适筋梁，满足规范要求"

        return BearingCapacityResult(
            h0=h0, fc=fc, fy=fy, alpha1=alpha1,
            xi_b=round(xi_b, 3), rho_min=round(rho_min, 4),
            rho_max=round(xi_b * alpha1 * fc / fy, 4),
            x=round(x, 3), xi=round(xi, 3),
            as_req=As, mu=round(mu, 3),
            status=status, message=message, steps=steps,
        )

    # =========================================================================
    # 设计模式：给定截面，输出最小/最大两档配筋方案
    # =========================================================================
    rho_max = xi_b * alpha1 * fc / fy
    As_max = rho_max * b * h0
    x_max = xi_b * h0
    Mu_max = alpha1 * fc * b * x_max * (h0 - x_max / 2) / 1e6  # kN·m

    steps.append(f"=== 单筋矩形截面设计 ===")
    steps.append(f"截面: b×h = {b:.0f}×{inp.h:.0f} mm")
    steps.append(f"有效高度 h₀ = h - a_s = {inp.h:.0f} - {inp.a_s:.0f} = {h0:.0f} mm")
    steps.append(f"材料: {inp.concrete_grade} (fc={fc} MPa), {inp.rebar_grade} (fy={fy} MPa)")
    steps.append(f"α₁ = {alpha1}, β₁ = {get_beta1(inp.concrete_grade)}, ξb = {xi_b:.4f}")
    steps.append(f"最小配筋率 ρ_min = max(0.002, 0.45·ft/fy) = max(0.002, 0.45×{CONCRETE_FT[inp.concrete_grade]}/{fy}) = {rho_min:.4f}")
    steps.append(f"最大(界限)配筋率 ρ_max = ξb·α₁·fc/fy = {xi_b:.4f}×{alpha1}×{fc}/{fy} = {rho_max:.4f}")

    def _design_point(label: str, rho: float, As: float, note: str) -> dict:
        """计算单个设计点的受压区高度和承载力"""
        x_i = fy * As / (alpha1 * fc * b)
        xi_i = x_i / h0
        Mu_i = alpha1 * fc * b * x_i * (h0 - x_i / 2) / 1e6
        return {
            "label": label,
            "rho": round(rho, 4),
            "As": round(As, 1),
            "x": round(x_i, 3),
            "xi": round(xi_i, 3),
            "Mu": round(Mu_i, 3),
            "note": note,
        }

    # 1. 最小配筋
    As_min = rho_min * b * inp.h
    pt_min = _design_point("最小配筋", rho_min, As_min,
                           "按规范最小配筋率，承载力低，实际工程一般不采用")

    # 2. 最大配筋（界限配筋）
    pt_max = _design_point("最大配筋(界限)", rho_max, As_max,
                           "单筋截面承载力上限，超过需改为双筋截面")

    design_points = [pt_min, pt_max]

    steps.append(f"\n{'='*50}")
    steps.append(f"设计结果:")
    steps.append(f"{'='*50}")
    for pt in design_points:
        steps.append(f"\n  ◆ {pt['label']} — {pt['note']}")
        steps.append(f"    配筋率  ρ = {pt['rho']:.4f}")
        steps.append(f"    钢筋面积 As = {pt['As']:.1f} mm²")
        steps.append(f"    受压区高度 x = {pt['x']:.3f} mm")
        steps.append(f"    相对受压区高度 ξ = {pt['xi']:.3f}")
        steps.append(f"    极限弯矩 Mu = {pt['Mu']:.3f} kN·m")

    status = "ok"
    message = f"单筋截面设计：最小配筋 {pt_min['As']:.1f} mm² (Mu={pt_min['Mu']:.3f} kN·m) / 最大配筋 {pt_max['As']:.1f} mm² (Mu={pt_max['Mu']:.3f} kN·m)"

    return BearingCapacityResult(
        h0=h0, fc=fc, fy=fy, alpha1=alpha1,
        xi_b=round(xi_b, 3), rho_min=round(rho_min, 4),
        rho_max=round(rho_max, 4),
        x=round(x_max, 3), xi=round(xi_b, 3),
        as_req=round(As_max, 1), mu=round(Mu_max, 3),
        design_points=design_points,
        status=status, message=message, steps=steps,
    )


def _calc_double_reinforced(inp: BearingCapacityInput, fc: float, fy: float,
                            alpha1: float, xi_b: float, rho_min: float,
                            h0: float) -> BearingCapacityResult:
    """双筋矩形截面正截面承载力计算"""
    b = inp.b
    a_s_prime = inp.a_s_prime
    steps = []

    # 如果给了既有配筋，校核模式
    if inp.as_given is not None and inp.as_prime_given is not None:
        As = inp.as_given
        As_prime = inp.as_prime_given
        steps.append(f"=== 双筋截面校核 ===")
        steps.append(f"受拉钢筋 As = {As:.1f} mm², 受压钢筋 As' = {As_prime:.1f} mm²")

        # 判断受压钢筋是否屈服
        x = (fy * As - fy * As_prime) / (alpha1 * fc * b)  # 假定受压钢筋屈服
        xi = x / h0

        # 检查受压钢筋是否屈服: x ≥ 2a_s'
        if x < 2 * a_s_prime:
            steps.append(f"受压钢筋未屈服 (x={x:.2f} < 2a_s'={2*a_s_prime:.0f})")
            steps.append(f"取 x = 2a_s', 对受压钢筋合力点取矩:")
            mu_n_mm = fy * As * (h0 - a_s_prime)
            mu = mu_n_mm / 1e6
            steps.append(f"  Mu = fy·As·(h₀-a_s') = {fy}×{As:.1f}×({h0:.0f}-{a_s_prime:.0f})")
            steps.append(f"     = {mu:.2f} kN·m")
        elif xi > xi_b:
            steps.append(f"超筋！ξ = {xi:.4f} > ξb = {xi_b:.4f}")
            steps.append(f"取 ξ = ξb 计算:")
            x = xi_b * h0
            mu_n_mm = alpha1 * fc * b * x * (h0 - x / 2) + fy * As_prime * (h0 - a_s_prime)
            mu = mu_n_mm / 1e6
            status = "over_reinforced"
            message = f"超筋！承载力按 ξ=ξb 取为 {mu:.2f} kN·m"
        else:
            mu_n_mm = alpha1 * fc * b * x * (h0 - x / 2) + fy * As_prime * (h0 - a_s_prime)
            mu = mu_n_mm / 1e6
            steps.append(f"  x = (fy·As - fy'·As')/(α₁·fc·b)")
            steps.append(f"    = ({fy}×{As:.1f} - {fy}×{As_prime:.1f})/({alpha1}×{fc}×{b:.0f})")
            steps.append(f"    = {x:.2f} mm")
            steps.append(f"  Mu = α₁·fc·b·x·(h₀-x/2) + fy'·As'·(h₀-a_s')")
            steps.append(f"     = {mu:.3f} kN·m")
            mu = round(mu, 3)

            if As / (b * inp.h) < rho_min:
                status = "under_reinforced"
                message = f"少筋！受拉配筋率不满足最小要求"
            else:
                status = "ok"
                message = f"双筋截面，承载力 Mu = {mu:.2f} kN·m"

        return BearingCapacityResult(
            h0=h0, fc=fc, fy=fy, alpha1=alpha1,
            xi_b=round(xi_b, 3), rho_min=round(rho_min, 4),
            rho_max=round(xi_b * alpha1 * fc / fy, 4),
            x=round(x, 3), xi=round(xi, 3),
            as_req=As, mu=round(mu, 3),
            status=status, message=message, steps=steps,
        )

    # =========================================================================
    # 设计模式（双筋）：未提供弯矩时，展示双筋截面设计参考
    # =========================================================================
    rho_max = xi_b * alpha1 * fc / fy
    As1_max = rho_max * b * h0  # 单筋部分最大受拉钢筋
    x_max = xi_b * h0
    # 单筋最大承载力
    Mu_single_max = alpha1 * fc * b * x_max * (h0 - x_max / 2) / 1e6

    steps.append(f"=== 双筋矩形截面设计参考 ===")
    steps.append(f"截面: b×h = {b:.0f}×{inp.h:.0f} mm, h₀ = {h0:.0f} mm, a_s' = {inp.a_s_prime:.0f} mm")
    steps.append(f"材料: {inp.concrete_grade} (fc={fc}), {inp.rebar_grade} (fy={fy})")
    steps.append(f"ξb = {xi_b:.4f}, ρ_max(单筋) = {rho_max:.4f}")
    steps.append(f"")
    steps.append(f"单筋截面最大承载力 Mu_max = {Mu_single_max:.3f} kN·m")
    steps.append(f"当设计弯矩 M > {Mu_single_max:.3f} kN·m 时需要双筋截面。")
    steps.append(f"")
    steps.append(f"双筋设计方法（取 ξ = ξb, 受压钢筋屈服）:")
    steps.append(f"  受压钢筋面积: As' = (M - Mu_max) × 10⁶ / [fy' × (h₀ - a_s')]")
    steps.append(f"  受拉钢筋面积: As = As1_max + As'")
    steps.append(f"                 = {As1_max:.1f} + As'")
    steps.append(f"")
    steps.append(f"示例 — 不同弯矩需求下的配筋方案:")
    hdr_m = "M (kN·m)"
    hdr_ap = "As' (mm²)"
    hdr_as = "As (mm²)"
    hdr_note = "判定"
    steps.append(f"  {hdr_m:>12s}  {hdr_ap:>12s}  {hdr_as:>12s}  {hdr_note:>10s}")
    steps.append(f"  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}")

    design_points = []
    # 展示 Mu_single_max 及几个超出的弯矩点
    M_list = [Mu_single_max]
    step_M = max(50, round(Mu_single_max * 0.15 / 50) * 50)  # 约15%增幅取整
    for i in range(1, 4):
        M_list.append(Mu_single_max + i * step_M)
    # 再加一个较大的弯矩点
    if M_list[-1] < Mu_single_max * 2:
        M_list.append(Mu_single_max * 2)

    for M_d in M_list:
        if M_d <= Mu_single_max:
            As_prime = 0.0
            As_total = As1_max
            note = "单筋足矣"
        else:
            As_prime = (M_d - Mu_single_max) * 1e6 / (fy * (h0 - inp.a_s_prime))
            As_total = As1_max + As_prime
            note = "需双筋"
        steps.append(f"  {M_d:>12.3f}  {As_prime:>12.1f}  {As_total:>12.1f}  {note:>10s}")

        if M_d > Mu_single_max:
            design_points.append({
                "label": f"M={M_d:.1f} kN·m",
                "rho": round(As_total / (b * inp.h), 4),
                "As": round(As_total, 1),
                "As_prime": round(As_prime, 1),
                "M": round(M_d, 3),
                "Mu_single_max": round(Mu_single_max, 3),
                "note": note,
            })

    steps.append(f"")
    steps.append(f"提示: 如需精确计算，请在「配筋计算」模块输入设计弯矩 M。")

    status = "ok"
    message = f"双筋截面设计参考：单筋上限 {Mu_single_max:.3f} kN·m，超出部分需配置受压钢筋"

    return BearingCapacityResult(
        h0=h0, fc=fc, fy=fy, alpha1=alpha1,
        xi_b=round(xi_b, 3), rho_min=round(rho_min, 4),
        rho_max=round(rho_max, 4),
        x=round(x_max, 3), xi=round(xi_b, 3),
        as_req=round(As1_max, 1), mu=round(Mu_single_max, 3),
        design_points=design_points if design_points else None,
        status=status, message=message, steps=steps,
    )


def calculate_bearing_capacity(inp: BearingCapacityInput) -> BearingCapacityResult:
    """
    计算矩形截面正截面承载力

    Args:
        inp: BearingCapacityInput, 包含截面尺寸、材料强度等参数

    Returns:
        BearingCapacityResult, 包含承载力、配筋、判定等结果
    """
    # 参数查表
    fc = CONCRETE_FC.get(inp.concrete_grade)
    if fc is None:
        raise ValueError(f"不支持的混凝土强度等级: {inp.concrete_grade}，可选: {list(CONCRETE_FC.keys())}")

    fy = REBAR_FY.get(inp.rebar_grade)
    if fy is None:
        raise ValueError(f"不支持的钢筋牌号: {inp.rebar_grade}，可选: {list(REBAR_FY.keys())}")

    alpha1 = get_alpha1(inp.concrete_grade)
    xi_b = get_xi_b(inp.concrete_grade, inp.rebar_grade)
    ft = CONCRETE_FT.get(inp.concrete_grade, 1.43)
    rho_min = max(0.002, 0.45 * ft / fy)
    h0 = inp.h - inp.a_s

    if inp.as_type == "double":
        return _calc_double_reinforced(inp, fc, fy, alpha1, xi_b, rho_min, h0)
    else:
        return _calc_single_reinforced(inp, fc, fy, alpha1, xi_b, rho_min, h0)
