"""钢结构螺栓连接承载力计算。"""

from dataclasses import dataclass
from math import pi
from typing import Literal

BOLT_FUB = {"4.6": 400.0, "4.8": 400.0, "5.6": 500.0, "8.8": 800.0, "10.9": 1000.0}
BOLT_FVB = {"4.6": 140.0, "4.8": 140.0, "5.6": 190.0, "8.8": 320.0}
# 普通螺栓连接钢材承压强度设计值（MPa）
STEEL_FCB = {"Q235": 305.0, "Q355": 385.0, "Q390": 400.0, "Q420": 425.0}
HOLE_FACTORS = {"standard": 1.0, "oversize": 0.85, "slotted": 0.70}
HIGH_STRENGTH_PRETENSION = {
    "8.8": {16: 80.0, 20: 125.0, 22: 150.0, 24: 175.0, 27: 230.0, 30: 280.0},
    "10.9": {16: 100.0, 20: 155.0, 22: 190.0, 24: 225.0, 27: 290.0, 30: 355.0},
}

@dataclass
class BoltConnectionInput:
    bolt_type: Literal["ordinary", "high_strength"]
    diameter: float
    bolt_count: int
    shear_planes: int = 1
    bolt_grade: str = "4.6"
    steel_grade: str = "Q235"
    connected_thickness: float = 10.0
    load: float | None = None
    slip_coefficient: float = 0.45
    friction_surfaces: int = 1
    hole_type: Literal["standard", "oversize", "slotted"] = "standard"

def calculate_bolt_connection(inp: BoltConnectionInput) -> dict:
    if inp.diameter <= 0 or inp.bolt_count < 1 or inp.shear_planes < 1:
        raise ValueError("螺栓直径、数量和受剪面数必须大于 0")
    if inp.connected_thickness <= 0:
        raise ValueError("同一受力方向承压构件总厚度必须大于 0")
    if inp.load is not None and inp.load <= 0:
        raise ValueError("设计剪力必须大于 0")
    area = pi * inp.diameter ** 2 / 4
    if inp.bolt_type == "ordinary":
        if inp.bolt_grade not in BOLT_FVB or inp.steel_grade not in STEEL_FCB:
            raise ValueError("不支持所选螺栓性能等级或钢材牌号")
        fvb, fcb = BOLT_FVB[inp.bolt_grade], STEEL_FCB[inp.steel_grade]
        nv = inp.shear_planes * area * fvb / 1000
        nc = inp.diameter * inp.connected_thickness * fcb / 1000
        per_bolt, control = min(nv, nc), ("抗剪承载力" if nv <= nc else "承压承载力")
        steps = [f"螺栓杆截面积 A = πd²/4 = {area:.1f} mm²", f"单个螺栓抗剪承载力 Nᵛᵦ = nᵥAfᵥᵦ = {inp.shear_planes}×{area:.1f}×{fvb:.0f}×10⁻³ = {nv:.3f} kN", f"单个螺栓承压承载力 Nᶜᵦ = dΣtfᶜᵦ = {inp.diameter:g}×{inp.connected_thickness:g}×{fcb:.0f}×10⁻³ = {nc:.3f} kN", f"单个螺栓承载力 Nᵦ = min(Nᵛᵦ, Nᶜᵦ) = {per_bolt:.3f} kN"]
        details = {"area": round(area, 1), "fvb": fvb, "fcb": fcb, "shear_capacity": round(nv, 3), "bearing_capacity": round(nc, 3)}
    elif inp.bolt_type == "high_strength":
        diameter_key = int(inp.diameter)
        if inp.diameter != diameter_key or inp.bolt_grade not in HIGH_STRENGTH_PRETENSION or diameter_key not in HIGH_STRENGTH_PRETENSION[inp.bolt_grade]:
            raise ValueError("高强螺栓仅支持 M16、M20、M22、M24、M27、M30 预拉力查表")
        if not 0 < inp.slip_coefficient <= 1 or inp.friction_surfaces < 1:
            raise ValueError("请检查高强螺栓等级、抗滑移系数和摩擦面数")
        fub = BOLT_FUB[inp.bolt_grade]
        pretension = HIGH_STRENGTH_PRETENSION[inp.bolt_grade][diameter_key]
        hole_factor = HOLE_FACTORS[inp.hole_type]
        per_bolt = 0.9 * hole_factor * inp.friction_surfaces * inp.slip_coefficient * pretension
        control = "抗滑移承载力"
        steps = [f"螺栓杆截面积 A = πd²/4 = {area:.1f} mm²", f"查预拉力表：{inp.bolt_grade} 级 M{diameter_key} 高强螺栓，P = {pretension:.3f} kN", f"单个螺栓抗滑移承载力 Nᵥᵦ = 0.9kₛn𝒻μP = 0.9×{hole_factor:.2f}×{inp.friction_surfaces}×{inp.slip_coefficient:.2f}×{pretension:.3f} = {per_bolt:.3f} kN"]
        details = {"area": round(area, 1), "fub": fub, "pretension": round(pretension, 3), "hole_factor": hole_factor}
    else:
        raise ValueError("不支持的螺栓类型")
    total = per_bolt * inp.bolt_count
    utilization = inp.load / total if inp.load is not None else None
    steps.append(f"连接承载力 Nᵤ = nNᵦ = {inp.bolt_count}×{per_bolt:.3f} = {total:.3f} kN")
    if utilization is not None:
        steps.append(f"承载力利用率 η = V/Nᵤ = {inp.load:.3f}/{total:.3f} = {utilization:.3f}")
    return {"bolt_type": inp.bolt_type, "per_bolt_capacity": round(per_bolt, 3), "total_capacity": round(total, 3), "control": control, "utilization": round(utilization, 3) if utilization is not None else None, "passed": utilization <= 1 if utilization is not None else None, "details": details, "steps": steps}
