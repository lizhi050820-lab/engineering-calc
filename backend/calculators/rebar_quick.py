"""钢筋理论重量、间距根数和等面积代换独立参考实现。"""

from dataclasses import asdict, dataclass, field
import math
from typing import Literal, Optional


Operation = Literal["quantity", "weight_to_length", "spacing", "equivalent"]

STANDARD_REBARS = {
    6: (28.27, 0.222), 8: (50.27, 0.395), 10: (78.54, 0.617),
    12: (113.1, 0.888), 14: (153.9, 1.21), 16: (201.1, 1.58),
    18: (254.5, 2.0), 20: (314.2, 2.47), 22: (380.1, 2.98),
    25: (490.9, 3.85), 28: (615.8, 4.83), 32: (804.2, 6.31),
    36: (1018.0, 7.99), 40: (1257.0, 9.87), 50: (1964.0, 15.42),
}


@dataclass
class RebarQuickInput:
    operation: Operation = "quantity"
    diameter: Optional[float] = None
    bar_length: Optional[float] = None
    bar_count: Optional[int] = None
    total_weight: Optional[float] = None
    layout_length: Optional[float] = None
    max_spacing: Optional[float] = None
    source_diameter: Optional[float] = None
    source_count: Optional[int] = None
    target_diameter: Optional[float] = None


@dataclass
class RebarQuickResult:
    operation: str
    diameter: Optional[float] = None
    nominal_area: Optional[float] = None
    unit_weight: Optional[float] = None
    total_length: Optional[float] = None
    total_weight: Optional[float] = None
    weight_tonnes: Optional[float] = None
    bar_count: Optional[int] = None
    interval_count: Optional[int] = None
    actual_spacing: Optional[float] = None
    source_area: Optional[float] = None
    required_count: Optional[int] = None
    replacement_area: Optional[float] = None
    area_difference: Optional[float] = None
    area_change_percent: Optional[float] = None
    steps: list[str] = field(default_factory=list)
    status: str = "ok"


def _round(value: float, digits: int = 3) -> float:
    factor = 10 ** digits
    return math.floor((value + 1e-10) * factor + 0.5) / factor


def _positive(value: Optional[float], label: str) -> float:
    if value is None or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f"请填写有效的{label}")
    return float(value)


def _integer(value: Optional[int], label: str) -> int:
    number = _positive(value, label)
    if not number.is_integer():
        raise ValueError(f"{label}必须为正整数")
    return int(number)


def _bar(value: Optional[float], label: str = "钢筋直径") -> tuple[int, float, float]:
    diameter = _positive(value, label)
    if not diameter.is_integer() or int(diameter) not in STANDARD_REBARS:
        raise ValueError(f"{label}应选择 GB 1499—2024 表2中的标准规格")
    area, unit_weight = STANDARD_REBARS[int(diameter)]
    return int(diameter), area, unit_weight


def calculate_rebar_quick(inp: RebarQuickInput) -> dict:
    if inp.operation not in ("quantity", "weight_to_length", "spacing", "equivalent"):
        raise ValueError("请选择有效的钢筋速算类型")

    if inp.operation == "equivalent":
        source_d, source_area_one, _ = _bar(inp.source_diameter, "原钢筋直径")
        target_d, target_area_one, target_weight = _bar(inp.target_diameter, "替换钢筋直径")
        source_count = _integer(inp.source_count, "原钢筋根数")
        source_area = source_area_one * source_count
        required_count = math.ceil(source_area / target_area_one - 1e-12)
        replacement_area = target_area_one * required_count
        difference = replacement_area - source_area
        result = RebarQuickResult(
            operation=inp.operation, diameter=target_d,
            nominal_area=_round(target_area_one, 1), unit_weight=_round(target_weight),
            bar_count=source_count, source_area=_round(source_area, 1),
            required_count=required_count, replacement_area=_round(replacement_area, 1),
            area_difference=_round(difference, 1),
            area_change_percent=_round(difference / source_area * 100),
            steps=[
                f"原配筋面积 Aₛ₁ = {source_count}×{source_area_one} = {_round(source_area, 1)} mm²",
                f"替换根数向上取整，采用 {required_count} 根直径 {target_d} mm 钢筋",
            ],
        )
        return asdict(result)

    diameter, area, unit_weight = _bar(inp.diameter)
    result = RebarQuickResult(
        operation=inp.operation, diameter=diameter,
        nominal_area=_round(area, 1), unit_weight=_round(unit_weight),
    )
    if inp.operation == "quantity":
        length = _positive(inp.bar_length, "单根长度")
        count = _integer(inp.bar_count, "钢筋根数")
        total_length = length * count
        total_weight = total_length * unit_weight
        result.bar_count = count
        result.total_length = _round(total_length)
        result.total_weight = _round(total_weight)
        result.weight_tonnes = _round(total_weight / 1000)
        result.steps = [f"总长度 L = {length}×{count} = {_round(total_length)} m",
                        f"总重量 G = {unit_weight}×{_round(total_length)} = {_round(total_weight)} kg"]
    elif inp.operation == "weight_to_length":
        total_weight = _positive(inp.total_weight, "钢筋总重量")
        total_length = total_weight / unit_weight
        result.total_length = _round(total_length)
        result.total_weight = _round(total_weight)
        result.weight_tonnes = _round(total_weight / 1000)
        result.steps = [f"等效总长度 L = G/m₀ = {total_weight}/{unit_weight} = {_round(total_length)} m"]
    else:
        layout = _positive(inp.layout_length, "布置长度")
        spacing = _positive(inp.max_spacing, "最大间距")
        length = _positive(inp.bar_length, "单根钢筋长度")
        intervals = math.ceil(layout / spacing - 1e-12)
        count = intervals + 1
        actual_spacing = layout / intervals
        total_length = length * count
        total_weight = total_length * unit_weight
        result.interval_count = intervals
        result.bar_count = count
        result.actual_spacing = _round(actual_spacing)
        result.total_length = _round(total_length)
        result.total_weight = _round(total_weight)
        result.weight_tonnes = _round(total_weight / 1000)
        result.steps = [f"间隔数 nᵢ = ⌈{layout}/{spacing}⌉ = {intervals}",
                        f"钢筋根数 n = {intervals}+1 = {count}",
                        f"实际间距 s = {layout}/{intervals} = {_round(actual_spacing)} mm"]
    return asdict(result)
