"""GB 50007—2011 天然地基承载力与矩形基础底面压力验算。"""

import math
from dataclasses import dataclass
from typing import Optional


SOIL_CORRECTION_PRESETS = {
    "silt_muck_fill_soft_clay": ("淤泥、人工填土或软黏性土", 0.0, 1.0),
    "red_clay_wet": ("红黏土（含水比 αw＞0.8）", 0.0, 1.2),
    "red_clay_dry": ("红黏土（含水比 αw≤0.8）", 0.15, 1.4),
    "compacted_silt": ("大面积压实粉土", 0.0, 1.5),
    "compacted_gravel": ("大面积压实级配砂石", 0.0, 2.0),
    "silt_clay_ge10": ("粉土（黏粒含量≥10%）", 0.3, 1.5),
    "silt_clay_lt10": ("粉土（黏粒含量＜10%）", 0.5, 2.0),
    "cohesive_firm": ("e、IL 均＜0.85 的黏性土", 0.3, 1.6),
    "fine_sand": ("粉砂、细砂（不含很湿/饱和稍密）", 2.0, 3.0),
    "coarse_soil": ("中粗砂、砾砂及碎石土", 3.0, 4.4),
}


@dataclass
class FoundationBearingInput:
    b: float
    l: float
    d: float
    fak: float
    gamma: float
    gamma_m: float
    Fk: float
    Mx: float = 0.0
    My: float = 0.0
    Gk: Optional[float] = None
    foundation_weight_pressure: float = 20.0
    soil_category: str = "cohesive_firm"
    eta_b: Optional[float] = None
    eta_d: Optional[float] = None


def _positive(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"请填写有效的{label}")
    return number


def _nonnegative(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label}不能小于 0")
    return number


def calculate_foundation_bearing(inp: FoundationBearingInput) -> dict:
    b = _positive(inp.b, "基础宽度 b")
    length = _positive(inp.l, "基础长度 l")
    d = _nonnegative(inp.d, "基础埋深 d")
    fak = _positive(inp.fak, "地基承载力特征值 fak")
    gamma = _positive(inp.gamma, "基底以下土重度 γ")
    gamma_m = _positive(inp.gamma_m, "基底以上土平均重度 γm")
    fk = _nonnegative(inp.Fk, "上部竖向力 Fk")
    mx, my = float(inp.Mx), float(inp.My)
    if not math.isfinite(mx) or not math.isfinite(my):
        raise ValueError("基础底面弯矩必须为有效数字")

    if inp.soil_category == "custom":
        if inp.eta_b is None or inp.eta_d is None:
            raise ValueError("自定义土类必须填写 ηb 和 ηd")
        soil_label = "自定义修正系数"
        eta_b = _nonnegative(inp.eta_b, "宽度修正系数 ηb")
        eta_d = _nonnegative(inp.eta_d, "深度修正系数 ηd")
    else:
        if inp.soil_category not in SOIL_CORRECTION_PRESETS:
            raise ValueError("不支持的持力层土类别")
        soil_label, eta_b, eta_d = SOIL_CORRECTION_PRESETS[inp.soil_category]

    area = b * length
    if inp.Gk is None:
        foundation_weight_pressure = _positive(inp.foundation_weight_pressure, "单位面积基础及覆土重")
        gk = foundation_weight_pressure * area
        weight_source = "auto"
    else:
        foundation_weight_pressure = None
        gk = _nonnegative(inp.Gk, "基础及覆土重 Gk")
        weight_source = "manual"
    vertical = fk + gk
    if vertical <= 0:
        raise ValueError("竖向合力 Fk＋Gk 必须大于 0")

    b_corr = min(6.0, max(3.0, min(b, length)))
    d_corr = max(0.5, d)
    width_increment = eta_b * gamma * (b_corr - 3.0)
    depth_increment = eta_d * gamma_m * (d_corr - 0.5)
    fa = fak + width_increment + depth_increment
    wx = b * length ** 2 / 6.0
    wy = length * b ** 2 / 6.0
    pk = vertical / area
    tx, ty = abs(mx) / wx, abs(my) / wy
    pmax_linear = pk + tx + ty
    pmin_linear = pk - tx - ty

    tolerance = 1e-10
    has_mx, has_my = abs(mx) > tolerance, abs(my) > tolerance
    biaxial = has_mx and has_my
    full_contact = pmin_linear >= -tolerance
    supported, stable = True, True
    pressure_mode = "linear_full_contact" if has_mx or has_my else "uniform"
    pmax, pmin = pmax_linear, max(pmin_linear, 0.0)
    contact_width = b if has_my else length
    eccentricity = 0.0

    if not full_contact:
        if biaxial:
            supported = False
            pressure_mode = "biaxial_separation_review"
            pmax, pmin, contact_width = None, pmin_linear, None
        else:
            moment = max(abs(mx), abs(my))
            direction = b if has_my else length
            perpendicular = length if has_my else b
            eccentricity = moment / vertical
            a = direction / 2.0 - eccentricity
            pressure_mode = "uniaxial_triangular_contact"
            if a <= 0:
                supported, stable = False, False
                pressure_mode = "resultant_outside_base"
                pmax, pmin, contact_width = None, None, 0.0
            else:
                pmax = 2.0 * vertical / (3.0 * perpendicular * a)
                pmin = 0.0
                contact_width = 3.0 * a

    mean_pass = pk <= fa + tolerance
    edge_pass = pmax <= 1.2 * fa + tolerance if supported and stable and pmax is not None else None
    overall_pass = mean_pass and edge_pass is True and stable and supported
    status = "pass" if overall_pass else "fail"
    if not supported and stable:
        status = "review"
    if not stable:
        status = "unstable"

    corners = {
        "top_left": pk + mx / wx - my / wy,
        "top_right": pk + mx / wx + my / wy,
        "bottom_left": pk - mx / wx - my / wy,
        "bottom_right": pk - mx / wx + my / wy,
    }
    rounded = lambda value: None if value is None else round(value + 1e-12, 3)
    return {
        "soil_category": inp.soil_category,
        "soil_label": soil_label,
        "eta_b": rounded(eta_b),
        "eta_d": rounded(eta_d),
        "b_correction": rounded(b_corr),
        "d_correction": rounded(d_corr),
        "area": rounded(area),
        "Wx": rounded(wx),
        "Wy": rounded(wy),
        "Gk": rounded(gk),
        "N": rounded(vertical),
        "fa": rounded(fa),
        "width_increment": rounded(width_increment),
        "depth_increment": rounded(depth_increment),
        "pk": rounded(pk),
        "pmax": rounded(pmax),
        "pmin": rounded(pmin),
        "pmax_linear": rounded(pmax_linear),
        "pmin_linear": rounded(pmin_linear),
        "eccentricity": rounded(eccentricity),
        "contact_width": rounded(contact_width),
        "pressure_mode": pressure_mode,
        "full_contact": full_contact,
        "supported": supported,
        "stable": stable,
        "mean_pass": mean_pass,
        "edge_pass": edge_pass,
        "overall_pass": overall_pass,
        "mean_utilization": rounded(pk / fa),
        "edge_utilization": rounded(pmax / (1.2 * fa)) if pmax is not None else None,
        "corners": {key: rounded(value) for key, value in corners.items()},
        "weight_source": weight_source,
        "foundation_weight_pressure": foundation_weight_pressure,
        "status": status,
    }
