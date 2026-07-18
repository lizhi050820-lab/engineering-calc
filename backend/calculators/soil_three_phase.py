"""
土力学三相比例指标计算

依据：《土力学》土的物理性质 — 三相草图法

土的物理性质指标共9个，分为两类:
  试验指标（3个）：重度 γ、土粒比重 G_s、含水量 w
  换算指标（6个）：孔隙比 e、孔隙率 n、饱和度 S_r、
                  干重度 γ_d、饱和重度 γ_sat、有效重度 γ'

核心方法: 令 V_s = 1，在三相草图上按定义推导

计算策略: 约束传播 — 用户输入任意已知量（≥3个），
          系统迭代推导所有未知量，每条结果标注所用公式
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class SoilThreePhaseInput:
    """三相指标输入 — 全部可选，用户填多少算多少"""
    # 试验指标
    Gs: Optional[float] = None    # 土粒比重（相对密度），无量纲
    w: Optional[float] = None     # 含水量（小数），如 0.15 = 15%
    gamma: Optional[float] = None # 天然重度 (kN/m³)

    # 换算指标
    gamma_d: Optional[float] = None    # 干重度 (kN/m³)
    gamma_sat: Optional[float] = None  # 饱和重度 (kN/m³)
    gamma_prime: Optional[float] = None # 有效重度/浮重度 (kN/m³)
    e: Optional[float] = None          # 孔隙比，无量纲
    n: Optional[float] = None          # 孔隙率（小数）
    Sr: Optional[float] = None         # 饱和度（小数），1.0 = 完全饱和

    # 密度（备选输入方式）
    rho: Optional[float] = None        # 天然密度 (g/cm³)
    rho_d: Optional[float] = None      # 干密度 (g/cm³)
    rho_sat: Optional[float] = None    # 饱和密度 (g/cm³)

    # 水的重度，默认 9.81 kN/m³（考试常用 10）
    gamma_w: float = 9.81
    g: float = 9.81                    # 重力加速度 (m/s²)


@dataclass
class DerivedValue:
    """单个推导结果"""
    symbol: str       # 符号，如 "e", "γ_d"
    value: float
    formula: str      # 所用公式，如 "e = Gs·γw/γd − 1"
    unit: str = ""


@dataclass
class SoilThreePhaseResult:
    """三相指标计算结果"""
    # 所有最终值（None 表示无法推导）
    Gs: Optional[float] = None
    w: Optional[float] = None
    gamma: Optional[float] = None
    gamma_d: Optional[float] = None
    gamma_sat: Optional[float] = None
    gamma_prime: Optional[float] = None
    e: Optional[float] = None
    n: Optional[float] = None
    Sr: Optional[float] = None
    rho: Optional[float] = None
    rho_d: Optional[float] = None
    rho_sat: Optional[float] = None

    gamma_w: float = 9.81
    g: float = 9.81
    derivations: list = field(default_factory=list)  # List[DerivedValue]
    missing: list = field(default_factory=list)       # 未能推出的符号
    status: str = "ok"
    message: str = ""


# =============================================================================
# 约束推导引擎
# =============================================================================

# 符号中文名对照表（用于报告和公式展示）
SYMBOL_NAMES = {
    "Gs": "土粒比重 G_s",
    "w": "含水量 w",
    "γ": "天然重度 γ",
    "γ_d": "干重度 γ_d",
    "γ_sat": "饱和重度 γ_sat",
    "γ'": "有效重度 γ′",
    "e": "孔隙比 e",
    "n": "孔隙率 n",
    "S_r": "饱和度 S_r",
    "ρ": "天然密度 ρ",
    "ρ_d": "干密度 ρ_d",
    "ρ_sat": "饱和密度 ρ_sat",
}

SYMBOL_UNITS = {
    "Gs": "", "w": "", "e": "", "n": "", "S_r": "",
    "γ": "kN/m³", "γ_d": "kN/m³", "γ_sat": "kN/m³", "γ'": "kN/m³",
    "ρ": "g/cm³", "ρ_d": "g/cm³", "ρ_sat": "g/cm³",
}


def _solve(known: Dict[str, float], gamma_w: float, g: float) -> Tuple[dict, List[DerivedValue]]:
    """
    迭代约束传播求解所有未知指标

    参数
    ----
    known: 已知值字典（全部使用 ASCII-safe key），
           如 {"Gs": 2.70, "w": 0.15, "gamma": 18.5}
    gamma_w: 水的重度
    g: 重力加速度

    返回
    ----
    (final_values, derivations)
    所有 key 均为 ASCII-safe 名
    """
    vals = dict(known)  # 当前已知的所有值
    derivations: List[DerivedValue] = []

    # 用于记录迭代次数，防止死循环
    changed = True
    max_iter = 20
    iteration = 0

    while changed and iteration < max_iter:
        changed = False
        iteration += 1

        # ---- 重度 <-> 密度 互转 ----
        if "rho" in vals and "gamma" not in vals:
            vals["gamma"] = vals["rho"] * g
            derivations.append(DerivedValue("gamma", vals["gamma"], "gamma = rho * g", "kN/m3"))
            changed = True
        if "rho" not in vals and "gamma" in vals:
            vals["rho"] = vals["gamma"] / g
            derivations.append(DerivedValue("rho", vals["rho"], "rho = gamma / g", "g/cm3"))
            changed = True

        if "rho_d" in vals and "gamma_d" not in vals:
            vals["gamma_d"] = vals["rho_d"] * g
            derivations.append(DerivedValue("gamma_d", vals["gamma_d"], "gamma_d = rho_d * g", "kN/m3"))
            changed = True
        if "rho_d" not in vals and "gamma_d" in vals:
            vals["rho_d"] = vals["gamma_d"] / g
            derivations.append(DerivedValue("rho_d", vals["rho_d"], "rho_d = gamma_d / g", "g/cm3"))
            changed = True

        if "rho_sat" in vals and "gamma_sat" not in vals:
            vals["gamma_sat"] = vals["rho_sat"] * g
            derivations.append(DerivedValue("gamma_sat", vals["gamma_sat"], "gamma_sat = rho_sat * g", "kN/m3"))
            changed = True
        if "rho_sat" not in vals and "gamma_sat" in vals:
            vals["rho_sat"] = vals["gamma_sat"] / g
            derivations.append(DerivedValue("rho_sat", vals["rho_sat"], "rho_sat = gamma_sat / g", "g/cm3"))
            changed = True

        # ---- 基本关联公式 ----

        # (1) gamma_d = gamma / (1+w)  或  gamma = gamma_d * (1+w)
        if "gamma" in vals and "w" in vals and "gamma_d" not in vals:
            vals["gamma_d"] = vals["gamma"] / (1 + vals["w"])
            derivations.append(DerivedValue(
                "gamma_d", vals["gamma_d"],
                f"gamma_d = gamma/(1+w) = {vals['gamma']:.2f}/(1+{vals['w']:.4f})",
                "kN/m3"))
            changed = True
        if "gamma_d" in vals and "w" in vals and "gamma" not in vals:
            vals["gamma"] = vals["gamma_d"] * (1 + vals["w"])
            derivations.append(DerivedValue(
                "gamma", vals["gamma"],
                f"gamma = gamma_d*(1+w) = {vals['gamma_d']:.2f}*(1+{vals['w']:.4f})",
                "kN/m3"))
            changed = True

        # (2) gamma_d = Gs*gamma_w / (1+e)  或  e = Gs*gamma_w/gamma_d - 1
        if "Gs" in vals and "e" in vals and "gamma_d" not in vals:
            vals["gamma_d"] = vals["Gs"] * gamma_w / (1 + vals["e"])
            derivations.append(DerivedValue(
                "gamma_d", vals["gamma_d"],
                f"gamma_d = Gs*gamma_w/(1+e) = {vals['Gs']:.2f}*{gamma_w}/(1+{vals['e']:.4f})",
                "kN/m3"))
            changed = True
        if "Gs" in vals and "gamma_d" in vals and "e" not in vals:
            e_val = vals["Gs"] * gamma_w / vals["gamma_d"] - 1
            if e_val >= 0:
                vals["e"] = e_val
                derivations.append(DerivedValue(
                    "e", vals["e"],
                    f"e = Gs*gamma_w/gamma_d - 1 = {vals['Gs']:.2f}*{gamma_w}/{vals['gamma_d']:.2f} - 1",
                    ""))
                changed = True

        # (3) n = e/(1+e)  或  e = n/(1-n)
        if "e" in vals and "n" not in vals:
            vals["n"] = vals["e"] / (1 + vals["e"])
            derivations.append(DerivedValue(
                "n", vals["n"],
                f"n = e/(1+e) = {vals['e']:.4f}/(1+{vals['e']:.4f})",
                ""))
            changed = True
        if "n" in vals and "e" not in vals:
            if vals["n"] < 1.0:
                vals["e"] = vals["n"] / (1 - vals["n"])
                derivations.append(DerivedValue(
                    "e", vals["e"],
                    f"e = n/(1-n) = {vals['n']:.4f}/(1-{vals['n']:.4f})",
                    ""))
                changed = True

        # (4) Sr = w*Gs/e  或  w = Sr*e/Gs  或  e = w*Gs/Sr
        if "w" in vals and "Gs" in vals and "e" in vals and "Sr" not in vals:
            vals["Sr"] = vals["w"] * vals["Gs"] / vals["e"]
            derivations.append(DerivedValue(
                "Sr", vals["Sr"],
                f"Sr = w*Gs/e = {vals['w']:.4f}*{vals['Gs']:.2f}/{vals['e']:.4f}",
                ""))
            changed = True
        if "Sr" in vals and "Gs" in vals and "e" in vals and "w" not in vals:
            vals["w"] = vals["Sr"] * vals["e"] / vals["Gs"]
            derivations.append(DerivedValue(
                "w", vals["w"],
                f"w = Sr*e/Gs = {vals['Sr']:.4f}*{vals['e']:.4f}/{vals['Gs']:.2f}",
                ""))
            changed = True
        if "w" in vals and "Gs" in vals and "Sr" in vals and "e" not in vals:
            if vals["Sr"] > 0:
                vals["e"] = vals["w"] * vals["Gs"] / vals["Sr"]
                derivations.append(DerivedValue(
                    "e", vals["e"],
                    f"e = w*Gs/Sr = {vals['w']:.4f}*{vals['Gs']:.2f}/{vals['Sr']:.4f}",
                    ""))
                changed = True

        # (5) gamma_sat = (Gs + e)*gamma_w / (1+e)
        if "Gs" in vals and "e" in vals and "gamma_sat" not in vals:
            vals["gamma_sat"] = (vals["Gs"] + vals["e"]) * gamma_w / (1 + vals["e"])
            derivations.append(DerivedValue(
                "gamma_sat", vals["gamma_sat"],
                f"gamma_sat = (Gs+e)*gamma_w/(1+e) = ({vals['Gs']:.2f}+{vals['e']:.4f})*{gamma_w}/(1+{vals['e']:.4f})",
                "kN/m3"))
            changed = True

        # (6) gamma_prime = gamma_sat - gamma_w
        if "gamma_sat" in vals and "gamma_prime" not in vals:
            vals["gamma_prime"] = vals["gamma_sat"] - gamma_w
            derivations.append(DerivedValue(
                "gamma_prime", vals["gamma_prime"],
                f"gamma_prime = gamma_sat - gamma_w = {vals['gamma_sat']:.2f} - {gamma_w}",
                "kN/m3"))
            changed = True
        if "gamma_prime" in vals and "gamma_sat" not in vals:
            vals["gamma_sat"] = vals["gamma_prime"] + gamma_w
            derivations.append(DerivedValue(
                "gamma_sat", vals["gamma_sat"],
                f"gamma_sat = gamma_prime + gamma_w = {vals['gamma_prime']:.2f} + {gamma_w}",
                "kN/m3"))
            changed = True

        # (7) gamma = Gs*gamma_w*(1+w)/(1+e)
        if "Gs" in vals and "w" in vals and "e" in vals and "gamma" not in vals:
            vals["gamma"] = vals["Gs"] * gamma_w * (1 + vals["w"]) / (1 + vals["e"])
            derivations.append(DerivedValue(
                "gamma", vals["gamma"],
                f"gamma = Gs*gamma_w*(1+w)/(1+e) = {vals['Gs']:.2f}*{gamma_w}*(1+{vals['w']:.4f})/(1+{vals['e']:.4f})",
                "kN/m3"))
            changed = True

    # ---- 后处理 ----
    final = {}
    for k in ["Gs", "w", "gamma", "gamma_d", "gamma_sat", "gamma_prime",
              "e", "n", "Sr", "rho", "rho_d", "rho_sat"]:
        final[k] = vals.get(k)

    return final, derivations


# =============================================================================
# 公共接口
# =============================================================================

def calculate_soil_three_phase(inp: SoilThreePhaseInput) -> SoilThreePhaseResult:
    """
    计算土的三相比例指标

    输入任意已知量（通常 ≥3 个），系统自动推导其余指标。
    考试中最常见的输入组合: Gs, w, γ
    """

    # 收集已知值（ASCII-safe keys）
    known: Dict[str, float] = {}
    raw_names = [
        ("Gs", inp.Gs), ("w", inp.w),
        ("gamma", inp.gamma), ("gamma_d", inp.gamma_d),
        ("gamma_sat", inp.gamma_sat), ("gamma_prime", inp.gamma_prime),
        ("e", inp.e), ("n", inp.n), ("Sr", inp.Sr),
        ("rho", inp.rho), ("rho_d", inp.rho_d), ("rho_sat", inp.rho_sat),
    ]

    for sym, val in raw_names:
        if val is not None:
            known[sym] = val

    # 基本校验
    if len(known) < 2:
        raise ValueError(
            f"至少需要输入 2-3 个已知指标才能推导其余量，"
            f"当前仅输入了 {len(known)} 个: {list(known.keys())}"
        )

    if inp.Gs is None:
        raise ValueError(
            "土粒比重 G_s 是核心参数，必须提供。"
            "常见值: 砂土 2.65~2.69, 粉土 2.70~2.71, 黏土 2.72~2.75"
        )

    # 饱和度校验
    if "Sr" in known and (known["Sr"] < 0 or known["Sr"] > 1.0):
        raise ValueError(f"饱和度 S_r 应在 0~1 之间，当前值: {known['Sr']}")

    # 孔隙率校验
    if "n" in known and (known["n"] <= 0 or known["n"] >= 1.0):
        raise ValueError(f"孔隙率 n 应在 0~1 之间，当前值: {known['n']}")

    # 含水量一般不超过 1.0（100%）
    if "w" in known and known["w"] > 1.5:
        raise ValueError(f"含水量 w 异常偏高 ({known['w']:.2f})，请确认输入是否为小数（如 15% 应输入 0.15）")

    # 执行求解
    final, derivations = _solve(known, inp.gamma_w, inp.g)

    # 推导结果同样必须满足基本物理范围，不能只校验用户直接输入的值。
    if final.get("Sr") is not None and not 0 <= final["Sr"] <= 1:
        raise ValueError(f"推导得到的饱和度 S_r={final['Sr']:.4f} 超出 0~1，请检查已知参数是否相容")
    if final.get("n") is not None and not 0 < final["n"] < 1:
        raise ValueError(f"推导得到的孔隙率 n={final['n']:.4f} 超出 0~1，请检查已知参数是否相容")
    if final.get("e") is not None and final["e"] < 0:
        raise ValueError(f"推导得到的孔隙比 e={final['e']:.4f} 小于 0，请检查已知参数是否相容")

    # 识别缺失指标
    all_syms = ["Gs", "w", "gamma", "gamma_d", "gamma_sat", "gamma_prime",
                "e", "n", "Sr", "rho", "rho_d", "rho_sat"]
    missing = [s for s in all_syms if final.get(s) is None]

    # 精度处理
    for k in final:
        if final[k] is not None:
            final[k] = round(final[k], 4)

    for d in derivations:
        d.value = round(d.value, 4)

    # 构建消息
    if missing:
        msg = f"推导完成，{len(missing)} 个指标无法确定: {', '.join(missing)}。请补充更多已知条件。"
    else:
        msg = "三相指标全部推导完成 ✓"

    return SoilThreePhaseResult(
        Gs=final.get("Gs"),
        w=final.get("w"),
        gamma=final.get("gamma"),
        gamma_d=final.get("gamma_d"),
        gamma_sat=final.get("gamma_sat"),
        gamma_prime=final.get("gamma_prime"),
        e=final.get("e"),
        n=final.get("n"),
        Sr=final.get("Sr"),
        rho=final.get("rho"),
        rho_d=final.get("rho_d"),
        rho_sat=final.get("rho_sat"),
        gamma_w=inp.gamma_w,
        g=inp.g,
        derivations=derivations,
        missing=missing,
        message=msg,
    )
