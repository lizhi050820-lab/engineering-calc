"""静定梁在多项集中力、集中弯矩和局部均布荷载下的内力速算。"""

from dataclasses import dataclass, field
from typing import Literal, Optional


BeamType = Literal["simply_supported", "cantilever", "overhanging"]
LoadType = Literal[
    "combined", "mid_point", "point", "uniform", "end_point",
    "end_moment", "overhang_end_point", "main_uniform",
]
BasicLoadType = Literal["point", "udl", "moment"]
MomentDirection = Literal["clockwise", "counterclockwise"]


@dataclass
class BeamLoadInput:
    type: BasicLoadType
    value: float
    x: Optional[float] = None
    x1: Optional[float] = None
    x2: Optional[float] = None
    direction: Optional[MomentDirection] = None


@dataclass
class BeamForceInput:
    beam_type: BeamType
    load_type: LoadType
    L: float
    loads: list[BeamLoadInput] = field(default_factory=list)
    P: Optional[float] = None
    q: Optional[float] = None
    M: Optional[float] = None
    a: Optional[float] = None
    c: Optional[float] = None
    support_a: Optional[float] = None
    support_b: Optional[float] = None
    fixed_end: Optional[Literal["left", "right"]] = None


@dataclass
class BeamForceResult:
    beam_type: str
    load_type: str
    L: float
    RA: float = 0.0
    RB: Optional[float] = None
    fixed_moment: Optional[float] = None
    Vmax: float = 0.0
    Mmax: float = 0.0
    x_Mmax: float = 0.0
    M_positive: float = 0.0
    x_M_positive: float = 0.0
    M_negative: float = 0.0
    x_M_negative: float = 0.0
    key_values: dict = field(default_factory=dict)
    diagram: dict = field(default_factory=dict)
    steps: list = field(default_factory=list)
    status: str = "ok"
    message: str = ""


def _r3(value: float) -> float:
    rounded = round(value, 3)
    return 0.0 if abs(rounded) < 0.0005 else rounded


def _require(value: Optional[float], name: str) -> float:
    if value is None or value <= 0:
        raise ValueError(f"请填写有效的{name}")
    return float(value)


def _legacy_loads(inp: BeamForceInput, total_length: float) -> list[BeamLoadInput]:
    """把旧版单选工况转换成通用荷载，保证旧页面与历史调用仍可使用。"""
    if inp.load_type == "mid_point":
        return [BeamLoadInput("point", _require(inp.P, "集中力 P"), x=inp.L / 2)]
    if inp.load_type == "point":
        return [BeamLoadInput("point", _require(inp.P, "集中力 P"), x=_require(inp.a, "荷载位置 a"))]
    if inp.load_type == "uniform":
        return [BeamLoadInput("udl", _require(inp.q, "均布荷载 q"), x1=0, x2=inp.L)]
    if inp.load_type == "end_point":
        return [BeamLoadInput("point", _require(inp.P, "集中力 P"), x=inp.L)]
    if inp.load_type == "end_moment":
        return [BeamLoadInput("moment", _require(inp.M, "集中弯矩 M"), x=inp.L, direction="clockwise")]
    if inp.load_type == "overhang_end_point":
        return [BeamLoadInput("point", _require(inp.P, "集中力 P"), x=total_length)]
    if inp.load_type == "main_uniform":
        return [BeamLoadInput("udl", _require(inp.q, "均布荷载 q"), x1=0, x2=inp.L)]
    raise ValueError("请至少添加一项荷载")


def _normalise_loads(inp: BeamForceInput, total_length: float) -> list[BeamLoadInput]:
    raw_loads = inp.loads or _legacy_loads(inp, total_length)
    if len(raw_loads) > 20:
        raise ValueError("单次最多添加 20 项荷载")

    loads: list[BeamLoadInput] = []
    for index, raw in enumerate(raw_loads, 1):
        load = raw if isinstance(raw, BeamLoadInput) else BeamLoadInput(**raw)
        value = _require(load.value, f"第 {index} 项荷载值")
        if load.type in ("point", "moment"):
            if load.x is None or not 0 <= load.x <= total_length:
                raise ValueError(f"第 {index} 项荷载位置 x 应满足 0 ≤ x ≤ {total_length:.3f} m")
            direction = load.direction
            if load.type == "moment" and direction not in ("clockwise", "counterclockwise"):
                raise ValueError(f"请选择第 {index} 项集中弯矩的方向")
            loads.append(BeamLoadInput(load.type, value, x=float(load.x), direction=direction))
        elif load.type == "udl":
            if load.x1 is None or load.x2 is None:
                raise ValueError(f"请填写第 {index} 项均布荷载的起点和终点")
            if not 0 <= load.x1 < load.x2 <= total_length:
                raise ValueError(
                    f"第 {index} 项均布荷载范围应满足 0 ≤ x₁ < x₂ ≤ {total_length:.3f} m"
                )
            loads.append(BeamLoadInput("udl", value, x1=float(load.x1), x2=float(load.x2)))
        else:
            raise ValueError(f"第 {index} 项荷载类型不受支持")
    return loads


def _signed_couple(load: BeamLoadInput) -> float:
    """外加力偶：逆时针为正，顺时针为负。"""
    return load.value if load.direction == "counterclockwise" else -load.value


def calculate_beam_forces(inp: BeamForceInput) -> BeamForceResult:
    L = _require(inp.L, "梁长 L")
    if inp.beam_type not in ("simply_supported", "cantilever", "overhanging"):
        raise ValueError("不支持的梁型")

    c = 0.0
    if inp.beam_type == "overhanging":
        c = _require(inp.c, "右外伸长度 c")
        total_length = L + c
        support_a, support_b, fixed_x = 0.0, L, None
    elif inp.beam_type == "simply_supported":
        total_length = L
        support_a = 0.0 if inp.support_a is None else float(inp.support_a)
        support_b = L if inp.support_b is None else float(inp.support_b)
        fixed_x = None
        if not 0 <= support_a < support_b <= total_length:
            raise ValueError(
                f"两支座位置应满足 0 ≤ xA < xB ≤ {total_length:.3f} m"
            )
    else:
        total_length = L
        fixed_end = inp.fixed_end or "left"
        if fixed_end not in ("left", "right"):
            raise ValueError("固定端只能选择左端或右端")
        fixed_x = 0.0 if fixed_end == "left" else total_length
        support_a, support_b = fixed_x, None
    loads = _normalise_loads(inp, total_length)

    points = [load for load in loads if load.type == "point"]
    udls = [load for load in loads if load.type == "udl"]
    moments = [load for load in loads if load.type == "moment"]

    vertical_total = sum(load.value for load in points)
    vertical_moment = sum(load.value * load.x for load in points)
    for load in udls:
        resultant = load.value * (load.x2 - load.x1)
        centroid = (load.x1 + load.x2) / 2
        vertical_total += resultant
        vertical_moment += resultant * centroid
    couple_total = sum(_signed_couple(load) for load in moments)

    if inp.beam_type == "cantilever":
        RA = vertical_total
        RB = None
        fixed_moment = vertical_moment - vertical_total * fixed_x - couple_total
    else:
        support_span = support_b - support_a
        RB = (vertical_moment - vertical_total * support_a - couple_total) / support_span
        RA = vertical_total - RB
        fixed_moment = None

    def shear_at(x: float, side: str = "right") -> float:
        include_equal = side == "right"
        value = 0.0
        if x > support_a or (x == support_a and include_equal):
            value += RA
        if RB is not None and (x > support_b or (x == support_b and include_equal)):
            value += RB
        for load in points:
            if x > load.x or (x == load.x and include_equal):
                value -= load.value
        for load in udls:
            loaded_length = min(max(x - load.x1, 0.0), load.x2 - load.x1)
            value -= load.value * loaded_length
        return value

    def moment_at(x: float, side: str = "right") -> float:
        include_equal = side == "right"
        value = 0.0
        if fixed_moment is not None and (x > fixed_x or (x == fixed_x and include_equal)):
            value -= fixed_moment
        if x > support_a:
            value += RA * (x - support_a)
        if RB is not None and x > support_b:
            value += RB * (x - support_b)
        for load in points:
            if x > load.x:
                value -= load.value * (x - load.x)
        for load in udls:
            loaded_length = min(max(x - load.x1, 0.0), load.x2 - load.x1)
            if loaded_length > 0:
                centroid = load.x1 + loaded_length / 2
                value -= load.value * loaded_length * (x - centroid)
        for load in moments:
            if x > load.x or (x == load.x and include_equal):
                value -= _signed_couple(load)
        return value

    breakpoints = {0.0, total_length, support_a}
    if support_b is not None:
        breakpoints.add(support_b)
    breakpoints.update(load.x for load in points + moments)
    for load in udls:
        breakpoints.update((load.x1, load.x2))
    ordered = sorted(breakpoints)

    critical = set(ordered)
    for left, right in zip(ordered, ordered[1:]):
        if right - left < 1e-12:
            continue
        mid = (left + right) / 2
        active_q = sum(load.value for load in udls if load.x1 < mid < load.x2)
        if active_q > 0:
            root = mid + shear_at(mid) / active_q
            if left < root < right:
                critical.add(root)

    moment_candidates = []
    shear_candidates = []
    for x in sorted(critical):
        moment_candidates.extend([(moment_at(x, "left"), x), (moment_at(x, "right"), x)])
        shear_candidates.extend([shear_at(x, "left"), shear_at(x, "right")])

    positive_value, positive_x = max(moment_candidates, key=lambda item: item[0])
    negative_value, negative_x = min(moment_candidates, key=lambda item: item[0])
    absolute_value, absolute_x = max(moment_candidates, key=lambda item: abs(item[0]))
    vmax = max(abs(value) for value in shear_candidates)

    steps = [
        "=== 多荷载静定梁内力计算 ===",
        f"梁长范围：0～{total_length:.3f} m；共 {len(loads)} 项荷载。",
    ]
    if inp.beam_type in ("overhanging", "simply_supported"):
        left_overhang = support_a
        right_overhang = total_length - support_b
        steps.append(
            f"支座位置：A 点 xA = {support_a:.3f} m，B 点 xB = {support_b:.3f} m；"
            f"支座间距 s = {support_b-support_a:.3f} m。"
        )
        steps.append(
            f"左外伸长度 = {left_overhang:.3f} m，右外伸长度 = {right_overhang:.3f} m。"
        )
    else:
        fixed_name = "左端" if fixed_x == 0 else "右端"
        steps.append(f"固定端位于{fixed_name} x = {fixed_x:.3f} m。")

    for index, load in enumerate(loads, 1):
        if load.type == "point":
            steps.append(f"荷载 {index}：集中力 P = {load.value:.3f} kN，位置 x = {load.x:.3f} m。")
        elif load.type == "udl":
            width = load.x2 - load.x1
            resultant = load.value * width
            centroid = (load.x1 + load.x2) / 2
            steps.append(
                f"荷载 {index}：均布荷载 q = {load.value:.3f} kN/m，范围 {load.x1:.3f}～{load.x2:.3f} m；"
                f"等效集中力 W = q·(x₂-x₁) = {resultant:.3f} kN，作用于 x = {centroid:.3f} m。"
            )
        else:
            direction = "逆时针" if load.direction == "counterclockwise" else "顺时针"
            steps.append(f"荷载 {index}：集中弯矩 M = {load.value:.3f} kN·m（{direction}），位置 x = {load.x:.3f} m。")

    steps.append(f"竖向荷载合力 ΣF = {vertical_total:.3f} kN；各竖向荷载对梁左端的力矩和 Σ(F·x) = {vertical_moment:.3f} kN·m。")
    if inp.beam_type == "cantilever":
        steps += [
            f"由 ΣFy = 0：RA = ΣF = {RA:.3f} kN。",
            f"对固定端取矩：MF = Σ[F·(x-xF)] - ΣM = {fixed_moment:.3f} kN·m。",
        ]
    else:
        support_span = support_b - support_a
        load_moment_about_a = vertical_moment - vertical_total * support_a
        steps += [
            f"荷载对 A 支座的力矩和 Σ[F·(x-xA)] = {load_moment_about_a:.3f} kN·m。",
            f"由 ΣMA = 0：RB·s + ΣM - Σ[F·(x-xA)] = 0，得 RB = {RB:.3f} kN。",
            f"由 ΣFy = 0：RA = ΣF - RB = {RA:.3f} kN。",
        ]
    steps += [
        "按叠加原理建立 V(x) 与 M(x)：集中力使剪力图跳跃，集中弯矩使弯矩图跳跃，均布荷载区间内剪力线性变化。",
        "在所有荷载边界、支座位置及 V(x)=0 的区间点检查弯矩极值。",
        f"最大正弯矩 M⁺max = {positive_value:.3f} kN·m，x = {positive_x:.3f} m。",
        f"最大负弯矩 M⁻min = {negative_value:.3f} kN·m，x = {negative_x:.3f} m。",
        f"最大绝对剪力 |V|max = {vmax:.3f} kN；最大绝对弯矩 |M|max = {abs(absolute_value):.3f} kN·m。",
    ]

    sample_x = {total_length * i / 40 for i in range(41)} | critical
    shear_diagram = [{"x": _r3(x), "V": _r3(shear_at(x))} for x in sorted(sample_x)]
    moment_diagram = [{"x": _r3(x), "M": _r3(moment_at(x))} for x in sorted(sample_x)]
    diagram_loads = []
    for load in loads:
        item = {"type": load.type, "value": _r3(load.value)}
        if load.type == "udl":
            item.update({"x1": _r3(load.x1), "x2": _r3(load.x2)})
        else:
            item["x"] = _r3(load.x)
            if load.type == "moment":
                item["direction"] = load.direction
        diagram_loads.append(item)

    return BeamForceResult(
        beam_type=inp.beam_type,
        load_type="combined" if inp.loads else inp.load_type,
        L=_r3(L),
        RA=_r3(RA),
        RB=None if RB is None else _r3(RB),
        fixed_moment=None if fixed_moment is None else _r3(fixed_moment),
        Vmax=_r3(vmax),
        Mmax=_r3(abs(absolute_value)),
        x_Mmax=_r3(absolute_x),
        M_positive=_r3(positive_value),
        x_M_positive=_r3(positive_x),
        M_negative=_r3(negative_value),
        x_M_negative=_r3(negative_x),
        key_values={
            "total_length": _r3(total_length),
            "load_count": len(loads),
            "support_a": _r3(support_a),
            "support_b": None if support_b is None else _r3(support_b),
            "fixed_end": None if fixed_x is None else ("left" if fixed_x == 0 else "right"),
        },
        diagram={
            "beam": {
                "length": _r3(total_length),
                "support_a": _r3(support_a),
                "support_b": None if support_b is None else _r3(support_b),
                "fixed_end": None if fixed_x is None else ("left" if fixed_x == 0 else "right"),
            },
            "loads": diagram_loads,
            "reactions": {"RA": _r3(RA), "RB": None if RB is None else _r3(RB)},
            "shear": shear_diagram,
            "moment": moment_diagram,
        },
        steps=steps,
        message="多荷载梁内力计算完成",
    )
