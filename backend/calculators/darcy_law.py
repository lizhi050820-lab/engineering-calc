"""
达西定律与渗透计算

依据：《土力学》第二章 — 土的渗透性

核心公式:
  达西定律:    v = k * i,  Q = k * i * A
  常水头试验:  k = Q*L / (A*Δh*t)
  变水头试验:  k = a*L/(A*t) * ln(h1/h2)
  渗透力:      j = γw * i,  J = j * V
  临界梯度:    i_cr = γ'/γw = (Gs-1)/(1+e)
  安全系数:    Fs = i_cr / i

策略: 约束传播 — 用户输入任意已知量，系统迭代推导未知量
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import math


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class DarcyLawInput:
    """达西定律计算输入 — 全部可选"""
    # 渗透基本参数
    k: Optional[float] = None       # 渗透系数 (cm/s)
    i: Optional[float] = None       # 水力梯度，无量纲
    delta_h: Optional[float] = None # 水头差 (m)
    L: Optional[float] = None       # 渗径长度 (m)

    # 流量参数
    Q: Optional[float] = None       # 渗流量 (m³/s)
    v: Optional[float] = None       # 渗透速度 (m/s)
    A: Optional[float] = None       # 截面积 (m²)
    t: Optional[float] = None       # 时间 (s)

    # 变水头试验参数
    a: Optional[float] = None       # 细管截面积 (cm²)
    h1: Optional[float] = None      # 初始水头 (cm)
    h2: Optional[float] = None      # 终止水头 (cm)

    # 渗透力参数
    j: Optional[float] = None       # 单位渗透力 (kN/m³)
    J: Optional[float] = None       # 总渗透力 (kN)
    V: Optional[float] = None       # 土体体积 (m³)

    # 临界水力梯度参数
    i_cr: Optional[float] = None    # 临界水力梯度
    gamma_prime: Optional[float] = None  # 有效重度 (kN/m³)
    Gs: Optional[float] = None      # 土粒比重
    e: Optional[float] = None       # 孔隙比
    Fs: Optional[float] = None      # 安全系数

    # 通用
    gamma_w: float = 9.81           # 水的重度 (kN/m³)


@dataclass
class DerivedValue:
    """单个推导结果"""
    symbol: str
    value: float
    formula: str
    unit: str = ""


@dataclass
class DarcyLawResult:
    """达西定律计算结果"""
    k: Optional[float] = None
    i: Optional[float] = None
    delta_h: Optional[float] = None
    L: Optional[float] = None
    Q: Optional[float] = None
    v: Optional[float] = None
    A: Optional[float] = None
    t: Optional[float] = None
    a: Optional[float] = None
    h1: Optional[float] = None
    h2: Optional[float] = None
    j: Optional[float] = None
    J: Optional[float] = None
    V: Optional[float] = None
    i_cr: Optional[float] = None
    gamma_prime: Optional[float] = None
    Gs: Optional[float] = None
    e: Optional[float] = None
    Fs: Optional[float] = None
    gamma_w: float = 9.81

    derivations: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    # 流土判定
    quicksand_risk: Optional[str] = None  # "安全" / "临界" / "危险"
    status: str = "ok"
    message: str = ""


# =============================================================================
# 约束推导引擎
# =============================================================================

def _solve(known: Dict[str, float], gamma_w: float) -> Tuple[dict, List[DerivedValue]]:
    """迭代约束传播"""
    vals = dict(known)
    derivations: List[DerivedValue] = []

    changed = True
    iteration = 0

    while changed and iteration < 30:
        changed = False
        iteration += 1

        # ---- (1) i = delta_h / L ----
        if "delta_h" in vals and "L" in vals and "i" not in vals:
            if vals["L"] > 0:
                vals["i"] = vals["delta_h"] / vals["L"]
                derivations.append(DerivedValue("i", vals["i"],
                    f"i = Δh/L = {vals['delta_h']:.4f}/{vals['L']:.4f}", ""))
                changed = True
        if "i" in vals and "L" in vals and "delta_h" not in vals:
            vals["delta_h"] = vals["i"] * vals["L"]
            derivations.append(DerivedValue("delta_h", vals["delta_h"],
                f"Δh = i·L = {vals['i']:.4f}×{vals['L']:.4f}", "m"))
            changed = True
        if "i" in vals and "delta_h" in vals and "L" not in vals:
            if vals["i"] > 0:
                vals["L"] = vals["delta_h"] / vals["i"]
                derivations.append(DerivedValue("L", vals["L"],
                    f"L = Δh/i = {vals['delta_h']:.4f}/{vals['i']:.4f}", "m"))
                changed = True

        # ---- (2) v = k * i ----
        if "k" in vals and "i" in vals and "v" not in vals:
            vals["v"] = vals["k"] * vals["i"]
            derivations.append(DerivedValue("v", vals["v"],
                f"v = k·i = {vals['k']:.6f}×{vals['i']:.4f}", "m/s"))
            changed = True
        if "v" in vals and "i" in vals and "k" not in vals:
            if vals["i"] > 0:
                vals["k"] = vals["v"] / vals["i"]
                derivations.append(DerivedValue("k", vals["k"],
                    f"k = v/i = {vals['v']:.6f}/{vals['i']:.4f}", "m/s"))
                changed = True
        if "v" in vals and "k" in vals and "i" not in vals:
            if vals["k"] > 0:
                vals["i"] = vals["v"] / vals["k"]
                derivations.append(DerivedValue("i", vals["i"],
                    f"i = v/k = {vals['v']:.6f}/{vals['k']:.6f}", ""))
                changed = True

        # ---- (3) Q = v * A ----
        if "v" in vals and "A" in vals and "Q" not in vals:
            vals["Q"] = vals["v"] * vals["A"]
            derivations.append(DerivedValue("Q", vals["Q"],
                f"Q = v·A = {vals['v']:.6f}×{vals['A']:.4f}", "m³/s"))
            changed = True
        if "Q" in vals and "A" in vals and "v" not in vals:
            if vals["A"] > 0:
                vals["v"] = vals["Q"] / vals["A"]
                derivations.append(DerivedValue("v", vals["v"],
                    f"v = Q/A = {vals['Q']:.6f}/{vals['A']:.4f}", "m/s"))
                changed = True
        if "Q" in vals and "v" in vals and "A" not in vals:
            if vals["v"] > 0:
                vals["A"] = vals["Q"] / vals["v"]
                derivations.append(DerivedValue("A", vals["A"],
                    f"A = Q/v = {vals['Q']:.6f}/{vals['v']:.6f}", "m²"))
                changed = True

        # ---- (4) Q = k * i * A * t  (total flow with time) ----
        if "k" in vals and "i" in vals and "A" in vals and "t" in vals and "Q" not in vals:
            vals["Q"] = vals["k"] * vals["i"] * vals["A"] * vals["t"]
            derivations.append(DerivedValue("Q", vals["Q"],
                f"Q = k·i·A·t = {vals['k']:.6f}×{vals['i']:.4f}×{vals['A']:.4f}×{vals['t']:.1f}", "m³"))
            changed = True

        # ---- (5) 常水头试验: k = Q*L / (A*Δh*t) ----
        if all(k in vals for k in ["Q","L","A","delta_h","t"]) and "k" not in vals:
            denom = vals["A"] * vals["delta_h"] * vals["t"]
            if denom > 0:
                vals["k"] = vals["Q"] * vals["L"] / denom
                derivations.append(DerivedValue("k", vals["k"],
                    f"k = Q·L/(A·Δh·t) = {vals['Q']:.6f}×{vals['L']:.4f}/({vals['A']:.4f}×{vals['delta_h']:.4f}×{vals['t']:.1f})", "m/s"))
                changed = True

        # ---- (6) 变水头试验: k = a*L/(A*t) * ln(h1/h2) ----
        if all(k in vals for k in ["a","L","A","t","h1","h2"]) and "k" not in vals:
            if vals["A"] > 0 and vals["t"] > 0 and vals["h2"] > 0:
                ratio = vals["h1"] / vals["h2"]
                if ratio > 0:
                    vals["k"] = (vals["a"] * vals["L"]) / (vals["A"] * vals["t"]) * math.log(ratio)
                    derivations.append(DerivedValue("k", vals["k"],
                        f"k = a·L/(A·t)·ln(h1/h2) = {vals['a']:.4f}×{vals['L']:.4f}/({vals['A']:.4f}×{vals['t']:.1f})×ln({vals['h1']:.1f}/{vals['h2']:.1f})", "m/s"))
                    changed = True

        # ---- (7) j = gamma_w * i ----
        if "i" in vals and "j" not in vals:
            vals["j"] = gamma_w * vals["i"]
            derivations.append(DerivedValue("j", vals["j"],
                f"j = γw·i = {gamma_w}×{vals['i']:.4f}", "kN/m³"))
            changed = True
        if "j" in vals and "i" not in vals:
            if gamma_w > 0:
                vals["i"] = vals["j"] / gamma_w
                derivations.append(DerivedValue("i", vals["i"],
                    f"i = j/γw = {vals['j']:.4f}/{gamma_w}", ""))
                changed = True

        # ---- (8) J = j * V ----
        if "j" in vals and "V" in vals and "J" not in vals:
            vals["J"] = vals["j"] * vals["V"]
            derivations.append(DerivedValue("J", vals["J"],
                f"J = j·V = {vals['j']:.4f}×{vals['V']:.4f}", "kN"))
            changed = True
        if "J" in vals and "V" in vals and "j" not in vals:
            if vals["V"] > 0:
                vals["j"] = vals["J"] / vals["V"]
                derivations.append(DerivedValue("j", vals["j"],
                    f"j = J/V = {vals['J']:.4f}/{vals['V']:.4f}", "kN/m³"))
                changed = True
        if "J" in vals and "j" in vals and "V" not in vals:
            if vals["j"] > 0:
                vals["V"] = vals["J"] / vals["j"]
                derivations.append(DerivedValue("V", vals["V"],
                    f"V = J/j = {vals['J']:.4f}/{vals['j']:.4f}", "m³"))
                changed = True

        # ---- (9) i_cr = gamma_prime / gamma_w ----
        if "gamma_prime" in vals and "i_cr" not in vals:
            vals["i_cr"] = vals["gamma_prime"] / gamma_w
            derivations.append(DerivedValue("i_cr", vals["i_cr"],
                f"i_cr = γ′/γw = {vals['gamma_prime']:.4f}/{gamma_w}", ""))
            changed = True
        if "i_cr" in vals and "gamma_prime" not in vals:
            vals["gamma_prime"] = vals["i_cr"] * gamma_w
            derivations.append(DerivedValue("gamma_prime", vals["gamma_prime"],
                f"γ′ = i_cr·γw = {vals['i_cr']:.4f}×{gamma_w}", "kN/m³"))
            changed = True

        # ---- (10) i_cr = (Gs-1)/(1+e) ----
        if "Gs" in vals and "e" in vals and "i_cr" not in vals:
            vals["i_cr"] = (vals["Gs"] - 1) / (1 + vals["e"])
            derivations.append(DerivedValue("i_cr", vals["i_cr"],
                f"i_cr = (Gs-1)/(1+e) = ({vals['Gs']:.2f}-1)/(1+{vals['e']:.4f})", ""))
            changed = True
        if "i_cr" in vals and "e" in vals and "Gs" not in vals:
            vals["Gs"] = vals["i_cr"] * (1 + vals["e"]) + 1
            derivations.append(DerivedValue("Gs", vals["Gs"],
                f"Gs = i_cr·(1+e)+1 = {vals['i_cr']:.4f}×(1+{vals['e']:.4f})+1", ""))
            changed = True
        if "Gs" in vals and "i_cr" in vals and "e" not in vals:
            if vals["i_cr"] > 0:
                vals["e"] = (vals["Gs"] - 1) / vals["i_cr"] - 1
                if vals["e"] >= 0:
                    derivations.append(DerivedValue("e", vals["e"],
                        f"e = (Gs-1)/i_cr - 1 = ({vals['Gs']:.2f}-1)/{vals['i_cr']:.4f} - 1", ""))
                    changed = True

        # ---- (11) Fs = i_cr / i ----
        if "i_cr" in vals and "i" in vals and "Fs" not in vals:
            if vals["i"] > 0:
                vals["Fs"] = vals["i_cr"] / vals["i"]
                derivations.append(DerivedValue("Fs", vals["Fs"],
                    f"Fs = i_cr/i = {vals['i_cr']:.4f}/{vals['i']:.4f}", ""))
                changed = True
        if "Fs" in vals and "i" in vals and "i_cr" not in vals:
            vals["i_cr"] = vals["Fs"] * vals["i"]
            derivations.append(DerivedValue("i_cr", vals["i_cr"],
                f"i_cr = Fs·i = {vals['Fs']:.2f}×{vals['i']:.4f}", ""))
            changed = True
        if "i_cr" in vals and "Fs" in vals and "i" not in vals:
            if vals["Fs"] > 0:
                vals["i"] = vals["i_cr"] / vals["Fs"]
                derivations.append(DerivedValue("i", vals["i"],
                    f"i = i_cr/Fs = {vals['i_cr']:.4f}/{vals['Fs']:.2f}", ""))
                changed = True

        # ---- (12) J = gamma_w * i * V ----
        if "i" in vals and "V" in vals and "J" not in vals:
            vals["J"] = gamma_w * vals["i"] * vals["V"]
            derivations.append(DerivedValue("J", vals["J"],
                f"J = γw·i·V = {gamma_w}×{vals['i']:.4f}×{vals['V']:.4f}", "kN"))
            changed = True

    # 精度处理
    for k in vals:
        if k not in ("i", "e", "Fs", "i_cr"):
            vals[k] = round(vals[k], 6)
        else:
            vals[k] = round(vals[k], 4)
    for d in derivations:
        d.value = round(d.value, 4)

    # 构建结果
    final = {}
    all_keys = ["k","i","delta_h","L","Q","v","A","t","a","h1","h2",
                "j","J","V","i_cr","gamma_prime","Gs","e","Fs"]
    for k in all_keys:
        final[k] = vals.get(k)

    return final, derivations


# =============================================================================
# 公共接口
# =============================================================================

def calculate_darcy_law(inp: DarcyLawInput) -> DarcyLawResult:
    """达西定律渗透计算"""

    # 收集已知值
    known: Dict[str, float] = {}
    raw = [
        ("k", inp.k), ("i", inp.i), ("delta_h", inp.delta_h), ("L", inp.L),
        ("Q", inp.Q), ("v", inp.v), ("A", inp.A), ("t", inp.t),
        ("a", inp.a), ("h1", inp.h1), ("h2", inp.h2),
        ("j", inp.j), ("J", inp.J), ("V", inp.V),
        ("i_cr", inp.i_cr), ("gamma_prime", inp.gamma_prime),
        ("Gs", inp.Gs), ("e", inp.e), ("Fs", inp.Fs),
    ]
    for sym, val in raw:
        if val is not None:
            known[sym] = val

    if len(known) < 2:
        raise ValueError(f"至少需要输入 2 个已知参数，当前仅 {len(known)} 个")

    # 执行求解
    final, derivations = _solve(known, inp.gamma_w)

    # 缺失指标
    all_keys = ["k","i","delta_h","L","Q","v","A","t","a","h1","h2",
                "j","J","V","i_cr","gamma_prime","Gs","e","Fs"]
    missing = [s for s in all_keys if final.get(s) is None]

    # 流土判别
    quicksand_risk = None
    if final.get("i") is not None and final.get("i_cr") is not None:
        if final["i"] >= final["i_cr"]:
            quicksand_risk = "danger"
        elif final["i"] >= 0.8 * final["i_cr"]:
            quicksand_risk = "warning"
        else:
            quicksand_risk = "safe"

    if missing:
        msg = f"推导完成，{len(missing)} 个未知参数无法确定"
    else:
        msg = "达西定律相关参数全部推导完成"

    return DarcyLawResult(
        k=final.get("k"), i=final.get("i"),
        delta_h=final.get("delta_h"), L=final.get("L"),
        Q=final.get("Q"), v=final.get("v"),
        A=final.get("A"), t=final.get("t"),
        a=final.get("a"), h1=final.get("h1"), h2=final.get("h2"),
        j=final.get("j"), J=final.get("J"), V=final.get("V"),
        i_cr=final.get("i_cr"), gamma_prime=final.get("gamma_prime"),
        Gs=final.get("Gs"), e=final.get("e"), Fs=final.get("Fs"),
        gamma_w=inp.gamma_w,
        derivations=derivations, missing=missing,
        quicksand_risk=quicksand_risk,
        message=msg,
    )
