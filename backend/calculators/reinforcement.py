"""
配筋计算模块（受弯构件）

依据：《混凝土结构设计规范》GB 50010-2010（2015年版）

功能：
  1. 设计模式：给定设计弯矩 M，计算所需钢筋面积 As
  2. 选筋推荐：根据计算面积推荐合理的钢筋配置方案
  3. 单筋/双筋自动判断
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Literal, Optional, List

from .bearing_capacity import (
    CONCRETE_FC, CONCRETE_FT, REBAR_FY, REBAR_ES, REBAR_AREA,
    get_alpha1, get_beta1, get_xi_b,
)


@dataclass
class ReinforcementInput:
    """配筋计算输入参数"""

    M: float  # 设计弯矩 (kN·m)
    b: float  # 截面宽度 (mm)
    h: float  # 截面高度 (mm)
    concrete_grade: str = "C30"  # 混凝土强度等级
    rebar_grade: str = "HRB400"  # 钢筋牌号
    a_s: float = 40.0  # 受拉区保护层 + 预估钢筋半径 (mm)
    a_s_prime: float = 40.0  # 受压区 (mm), 双筋时使用
    bar_diameter_range: List[int] = field(default_factory=lambda: [14, 16, 18, 20, 22, 25])  # 可选钢筋直径


@dataclass
class RebarScheme:
    """选筋方案"""

    description: str  # e.g. "4Φ20"
    count: int  # 根数
    diameter: int  # 直径 (mm)
    area: float  # 实际面积 (mm²)
    layout: str = ""  # 排列方式 "单排" / "双排"


@dataclass
class ReinforcementResult:
    """配筋计算结果"""

    # 参数
    h0: float
    fc: float
    fy: float
    alpha1: float
    xi_b: float
    rho_min: float

    # 计算过程
    alpha_s: float  # 截面抵抗矩系数
    xi: float  # 相对受压区高度
    gamma_s: float  # 内力臂系数

    # 结果
    as_req: float  # 所需钢筋面积 (mm²)
    as_min: float  # 最小配筋面积 (mm²)
    as_max: float  # 单筋最大配筋面积 (mm²)
    need_double: bool  # 是否需要双筋

    # 选筋推荐
    schemes: List[RebarScheme] = field(default_factory=list)

    # 如果双筋
    as_prime_req: float = 0.0  # 所需受压钢筋面积 (mm²)
    M2: float = 0.0  # 受压钢筋承担的弯矩 (kN·m)

    # 判定
    status: str = "ok"
    message: str = ""
    steps: list = field(default_factory=list)


def _calc_single_rebar(inp: ReinforcementInput, fc: float, fy: float,
                       alpha1: float, xi_b: float, rho_min: float,
                       h0: float, b: float, M_n_mm: float) -> ReinforcementResult:
    """单筋截面配筋计算"""
    steps = []

    steps.append("=== 单筋矩形截面配筋计算 ===")
    steps.append(f"截面有效高度 h₀ = h - a_s = {inp.h:.0f} - {inp.a_s:.0f} = {h0:.0f} mm")
    steps.append(f"设计弯矩 M = {inp.M} kN·m = {M_n_mm:.0f} N·mm")

    # 1. 计算截面抵抗矩系数 αs
    alpha_s = M_n_mm / (alpha1 * fc * b * h0 * h0)
    steps.append(f"\n1. 截面抵抗矩系数 αs = M / (α₁·fc·b·h₀²)")
    steps.append(f"   = {M_n_mm:.0f} / ({alpha1} × {fc} × {b:.0f} × {h0:.0f}²)")
    steps.append(f"   = {alpha_s:.4f}")

    # 2. 计算相对受压区高度 ξ。先按界限受压区判断，避免对负数开平方。
    alpha_s_max = xi_b * (1 - 0.5 * xi_b)
    if alpha_s > alpha_s_max:
        xi = xi_b
        steps.append(f"\n2. αs = {alpha_s:.4f} > αs,max = ξb(1-0.5ξb) = {alpha_s_max:.4f}")
        steps.append("   单筋截面无法满足，按 ξ = ξb 转入双筋设计。")
    else:
        xi = 1 - np.sqrt(1 - 2 * alpha_s)
        steps.append(f"\n2. 相对受压区高度 ξ = 1 - √(1 - 2αs)")
        steps.append(f"   = 1 - √(1 - 2 × {alpha_s:.4f})")
        steps.append(f"   = {xi:.4f}")

    if alpha_s > alpha_s_max or xi > xi_b:
        steps.append(f"   ξ = {xi:.4f} > ξb = {xi_b:.4f}，需要双筋截面！")
        # 按 ξ = ξb 计算单筋部分最大弯矩
        M1_max = alpha1 * fc * b * h0 * h0 * alpha_s_max / 1e6  # kN·m
        M2 = inp.M - M1_max
        steps.append(f"   按 ξ=ξb 计算单筋部分: M1_max = {M1_max:.2f} kN·m")
        steps.append(f"   剩余弯矩 M2 = M - M1_max = {inp.M:.2f} - {M1_max:.2f} = {M2:.2f} kN·m")
        steps.append(f"   需受压钢筋面积 As' = M2 / (fy'·(h₀-a_s'))")

        As_prime = M2 * 1e6 / (fy * (h0 - inp.a_s_prime))
        As1 = xi_b * alpha1 * fc * b * h0 / fy
        As = As1 + As_prime

        steps.append(f"   As' = {M2*1e6:.0f} / ({fy} × ({h0:.0f} - {inp.a_s_prime:.0f}))")
        steps.append(f"       = {As_prime:.1f} mm²")
        steps.append(f"   受拉钢筋 As = As1 + As' = {As1:.1f} + {As_prime:.1f} = {As:.1f} mm²")

        return ReinforcementResult(
            h0=h0, fc=fc, fy=fy, alpha1=alpha1, xi_b=xi_b, rho_min=rho_min,
            alpha_s=round(alpha_s, 4), xi=round(xi, 4),
            gamma_s=1 - 0.5 * xi_b,
            as_req=round(As, 1), as_min=round(rho_min * b * inp.h, 1),
            as_max=round(xi_b * alpha1 * fc * b * h0 / fy, 1),
            need_double=True, as_prime_req=round(As_prime, 1), M2=round(M2, 2),
            status="need_double",
            message=f"需要双筋截面！As = {As:.1f} mm², As' = {As_prime:.1f} mm²",
            steps=steps,
        )

    # 3. 适筋截面 — 计算 γs 和 As
    gamma_s = 1 - 0.5 * xi
    steps.append(f"\n3. 内力臂系数 γs = 1 - 0.5ξ = 1 - 0.5 × {xi:.4f} = {gamma_s:.4f}")

    As = M_n_mm / (fy * gamma_s * h0)
    steps.append(f"\n4. 所需钢筋面积 As = M / (fy·γs·h₀)")
    steps.append(f"   = {M_n_mm:.0f} / ({fy} × {gamma_s:.4f} × {h0:.0f})")
    steps.append(f"   = {As:.1f} mm²")

    As_min = rho_min * b * inp.h
    As_max = xi_b * alpha1 * fc * b * h0 / fy

    steps.append(f"\n5. 构造要求检查:")
    steps.append(f"   最小配筋面积 As_min = ρ_min·b·h = {rho_min:.4f} × {b:.0f} × {inp.h:.0f} = {As_min:.1f} mm²")
    steps.append(f"   最大配筋面积 As_max = ξb·α₁·fc·b·h₀/fy = {As_max:.1f} mm²")

    if As < As_min:
        As = As_min
        steps.append(f"   As < As_min，取 As = As_min = {As_min:.1f} mm²")
        status = "min_reinforcement"
        message = f"计算配筋小于最小要求，按构造配筋 As = {As_min:.1f} mm²"
    else:
        status = "ok"
        message = f"所需钢筋面积 As = {As:.1f} mm²"

    steps.append(f"\n6. 配筋率验算: ρ = {As/(b*inp.h):.4f} (ρ_min={rho_min:.4f}, ρ_max={As_max/(b*inp.h):.4f})")

    return ReinforcementResult(
        h0=h0, fc=fc, fy=fy, alpha1=alpha1, xi_b=xi_b, rho_min=rho_min,
        alpha_s=round(alpha_s, 4), xi=round(xi, 4), gamma_s=round(gamma_s, 4),
        as_req=round(As, 1), as_min=round(As_min, 1), as_max=round(As_max, 1),
        need_double=False,
        status=status, message=message, steps=steps,
    )


def _generate_schemes(As_req: float, diameters: List[int], rebar_grade: str) -> List[RebarScheme]:
    """根据所需面积生成选筋方案"""
    schemes = []

    for d in diameters:
        single_area = REBAR_AREA.get(d)
        if single_area is None:
            continue
        # 至少 2 根, 最多按一排摆放 (估算: b=300 时约能放 b/(1.5*d) 根)
        max_count = 10
        for n in range(2, max_count + 1):
            area = n * single_area
            if area >= As_req and area <= As_req * 1.30:  # 不得小于计算所需面积
                layout = "单排" if n <= 5 else "双排"
                schemes.append(RebarScheme(
                    description=f"{n}Φ{d}",
                    count=n, diameter=d, area=round(area, 1),
                    layout=layout,
                ))
                break  # 只取最接近的

    # 按面积排序
    schemes.sort(key=lambda s: abs(s.area - As_req))
    return schemes[:5]  # 最多返回5个方案


def calculate_reinforcement(inp: ReinforcementInput) -> ReinforcementResult:
    """
    受弯构件配筋计算

    Args:
        inp: ReinforcementInput, 包含设计弯矩、截面尺寸、材料参数

    Returns:
        ReinforcementResult, 包含所需钢筋面积、选筋方案、计算过程
    """
    # 参数查表
    fc = CONCRETE_FC.get(inp.concrete_grade)
    if fc is None:
        raise ValueError(f"不支持的混凝土强度等级: {inp.concrete_grade}")

    fy = REBAR_FY.get(inp.rebar_grade)
    if fy is None:
        raise ValueError(f"不支持的钢筋牌号: {inp.rebar_grade}")

    alpha1 = get_alpha1(inp.concrete_grade)
    xi_b = get_xi_b(inp.concrete_grade, inp.rebar_grade)
    ft = CONCRETE_FT.get(inp.concrete_grade, 1.43)
    rho_min = max(0.002, 0.45 * ft / fy)
    h0 = inp.h - inp.a_s
    b = inp.b
    M_n_mm = inp.M * 1e6  # kN·m → N·mm

    # 单筋配筋计算
    result = _calc_single_rebar(inp, fc, fy, alpha1, xi_b, rho_min, h0, b, M_n_mm)

    # 生成选筋方案
    schemes = _generate_schemes(result.as_req if result.as_req > 0 else max(result.as_min, 100),
                                 inp.bar_diameter_range, inp.rebar_grade)
    result.schemes = schemes

    # 如果双筋，也生成受压钢筋方案
    if result.need_double and result.as_prime_req > 0:
        prime_schemes = _generate_schemes(result.as_prime_req, inp.bar_diameter_range, inp.rebar_grade)
        result.steps.append(f"\n7. 受压钢筋选筋方案:")
        for s in prime_schemes[:3]:
            result.steps.append(f"   {s.description} (面积 {s.area:.1f} mm²)")

    result.steps.append(f"\n8. 受拉钢筋选筋方案:")
    for i, s in enumerate(schemes, 1):
        result.steps.append(f"  方案{i}: {s.description} — {s.count}根直径{s.diameter}mm, "
                           f"面积 {s.area:.1f} mm² ({s.layout})")

    return result
