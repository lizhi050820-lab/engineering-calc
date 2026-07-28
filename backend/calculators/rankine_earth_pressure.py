"""经典朗肯土压力计算：主动、被动、静止、分层土与地下水。"""

from dataclasses import dataclass
from math import pi, sin, sqrt, tan
from typing import Literal, Optional


Mode = Literal["active", "passive", "at_rest"]
WaterMethod = Literal["separate", "combined"]


@dataclass
class RankineLayer:
    h: float
    gamma: float
    phi: float
    c: float = 0.0
    gamma_sat: Optional[float] = None


@dataclass
class RankineEarthPressureInput:
    mode: Mode
    layers: list[RankineLayer]
    q: float = 0.0
    water_table: Optional[float] = None
    water_method: WaterMethod = "separate"
    gamma_w: float = 9.81


def _round(value: float, digits: int = 3) -> float:
    return round(value + 1e-12, digits)


def _coefficient(mode: Mode, phi: float) -> float:
    radians = phi * pi / 180
    if mode == "active":
        return tan(pi / 4 - radians / 2) ** 2
    if mode == "passive":
        return tan(pi / 4 + radians / 2) ** 2
    return 1 - sin(radians)


def _validate(inp: RankineEarthPressureInput) -> float:
    if inp.mode not in ("active", "passive", "at_rest"):
        raise ValueError("土压力类型必须为主动、被动或静止")
    if inp.water_method not in ("separate", "combined"):
        raise ValueError("地下水算法必须为水土分算或水土合算")
    if not 1 <= len(inp.layers) <= 8:
        raise ValueError("请设置 1～8 层土")
    if inp.q < 0 or inp.gamma_w <= 0:
        raise ValueError("均布荷载不得为负且水的重度必须大于0")
    height = 0.0
    for index, layer in enumerate(inp.layers, start=1):
        if layer.h <= 0 or layer.gamma <= 0:
            raise ValueError(f"第{index}层厚度和天然重度必须大于0")
        if not 0 <= layer.phi < 45 or layer.c < 0:
            raise ValueError(f"第{index}层应满足0≤φ<45°且c≥0")
        if layer.gamma_sat is None:
            layer.gamma_sat = layer.gamma
        height += layer.h
    if inp.water_table is not None:
        if not 0 <= inp.water_table <= height:
            raise ValueError(f"地下水位深度应在0～{height:.3f}m之间")
        for index, layer in enumerate(inp.layers, start=1):
            if layer.gamma_sat is None or layer.gamma_sat <= inp.gamma_w:
                raise ValueError(f"第{index}层饱和重度必须大于水的重度")
    return height


def _vertical_stress(inp: RankineEarthPressureInput, depth: float) -> float:
    stress, top = inp.q, 0.0
    for layer in inp.layers:
        bottom = top + layer.h
        length = max(0.0, min(depth, bottom) - top)
        if length > 0:
            if inp.water_table is None:
                stress += layer.gamma * length
            else:
                above = max(0.0, min(depth, bottom, inp.water_table) - top)
                below_start = max(top, inp.water_table)
                below = max(0.0, min(depth, bottom) - below_start)
                submerged = (layer.gamma_sat - inp.gamma_w
                             if inp.water_method == "separate" else layer.gamma_sat)
                stress += layer.gamma * above + submerged * below
        if depth <= bottom:
            break
        top = bottom
    return stress


def _pressure(inp: RankineEarthPressureInput, layer: RankineLayer, depth: float) -> dict:
    coefficient = _coefficient(inp.mode, layer.phi)
    vertical = _vertical_stress(inp, depth)
    if inp.mode == "active":
        soil = max(coefficient * vertical - 2 * layer.c * sqrt(coefficient), 0.0)
    elif inp.mode == "passive":
        soil = coefficient * vertical + 2 * layer.c * sqrt(coefficient)
    else:
        soil = coefficient * vertical
    water = (inp.gamma_w * max(depth - inp.water_table, 0.0)
             if inp.water_method == "separate" and inp.water_table is not None else 0.0)
    return {"K": coefficient, "vertical": vertical, "soil": soil,
            "water": water, "total": soil + water}


def _integrate(z1: float, z2: float, p1: float, p2: float, height: float) -> tuple[float, float]:
    length = z2 - z1
    resultant = (p1 + p2) * length / 2
    if resultant == 0:
        return 0.0, 0.0
    centroid = length * (p1 + 2 * p2) / (3 * (p1 + p2))
    return resultant, resultant * (height - z1 - centroid)


def calculate_rankine_earth_pressure(inp: RankineEarthPressureInput) -> dict:
    height = _validate(inp)
    segments, coefficients = [], []
    layer_top = 0.0
    for index, layer in enumerate(inp.layers, start=1):
        layer_bottom = layer_top + layer.h
        coefficients.append({"layer": index, "phi": layer.phi,
                             "K": _round(_coefficient(inp.mode, layer.phi), 4)})
        points = [layer_top, layer_bottom]
        if inp.water_table is not None and layer_top < inp.water_table < layer_bottom:
            points.append(inp.water_table)
        points.sort()
        for point_index in range(len(points) - 1):
            z1, z2 = points[point_index], points[point_index + 1]
            start, end = _pressure(inp, layer, z1), _pressure(inp, layer, z2)
            raw_start = start["K"] * start["vertical"] - 2 * layer.c * sqrt(start["K"])
            raw_end = end["K"] * end["vertical"] - 2 * layer.c * sqrt(end["K"])
            split = [z1, z2]
            if inp.mode == "active" and raw_start * raw_end < 0:
                split.append(z1 + (z2 - z1) * (-raw_start) / (raw_end - raw_start))
                split.sort()
            for split_index in range(len(split) - 1):
                a = _pressure(inp, layer, split[split_index])
                b = _pressure(inp, layer, split[split_index + 1])
                segments.append({
                    "layer": index, "z1": split[split_index], "z2": split[split_index + 1],
                    "p1": a["total"], "p2": b["total"],
                    "soil_p1": a["soil"], "soil_p2": b["soil"],
                    "water_p1": a["water"], "water_p2": b["water"],
                })
        layer_top = layer_bottom

    earth_resultant = water_resultant = total_resultant = 0.0
    earth_moment = water_moment = total_moment = 0.0
    for segment in segments:
        earth = _integrate(segment["z1"], segment["z2"], segment["soil_p1"], segment["soil_p2"], height)
        water = _integrate(segment["z1"], segment["z2"], segment["water_p1"], segment["water_p2"], height)
        total = _integrate(segment["z1"], segment["z2"], segment["p1"], segment["p2"], height)
        earth_resultant += earth[0]; earth_moment += earth[1]
        water_resultant += water[0]; water_moment += water[1]
        total_resultant += total[0]; total_moment += total[1]

    mode_names = {"active": "主动土压力", "passive": "被动土压力", "at_rest": "静止土压力"}
    steps = [
        f"计算类型：{mode_names[inp.mode]}，墙高 H = {height:.3f} m",
        *[f"第{item['layer']}层：φ = {item['phi']:.2f}°，K = {item['K']:.4f}"
          for item in coefficients],
        f"土压力合力 Eₛ = {earth_resultant:.3f} kN/m",
        f"水压力合力 Eᵥ = {water_resultant:.3f} kN/m",
        f"总侧压力 E = {total_resultant:.3f} kN/m，作用点距墙底 "
        f"{total_moment / total_resultant if total_resultant else 0:.3f} m",
    ]
    rounded_segments = [
        {key: _round(value) if isinstance(value, float) else value for key, value in item.items()}
        for item in segments
    ]
    return {
        "mode": inp.mode, "water_method": inp.water_method,
        "total_height": _round(height), "coefficients": coefficients,
        "earth_resultant": _round(earth_resultant),
        "water_resultant": _round(water_resultant),
        "total_resultant": _round(total_resultant),
        "action_height": _round(total_moment / total_resultant if total_resultant else 0),
        "earth_action_height": _round(earth_moment / earth_resultant if earth_resultant else 0),
        "water_action_height": _round(water_moment / water_resultant if water_resultant else 0),
        "max_pressure": _round(max(max(item["p1"], item["p2"]) for item in segments)),
        "segments": rounded_segments, "steps": steps,
    }
