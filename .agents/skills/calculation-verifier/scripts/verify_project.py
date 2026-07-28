#!/usr/bin/env python3
"""Deterministic differential verifier for engineering-calc."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
REPO = SKILL_DIR.parents[2]
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

from calculators.bearing_capacity import BearingCapacityInput, calculate_bearing_capacity  # noqa: E402
from calculators.reinforcement import ReinforcementInput, calculate_reinforcement  # noqa: E402
from calculators.shear_capacity import ShearCapacityInput, calculate_shear_capacity  # noqa: E402
from calculators.section_properties import SectionPropertiesInput, calculate_section_properties  # noqa: E402
from calculators.composite_section import CompositeBlock, calculate_composite_section  # noqa: E402
from calculators.soil_three_phase import SoilThreePhaseInput, calculate_soil_three_phase  # noqa: E402
from calculators.darcy_law import DarcyLawInput, calculate_darcy_law  # noqa: E402
from calculators.bolt_connection import BoltConnectionInput, calculate_bolt_connection  # noqa: E402
from calculators.beam_internal_forces import (  # noqa: E402
    BeamForceInput, BeamLoadInput, calculate_beam_forces,
)
from calculators.rankine_earth_pressure import (  # noqa: E402
    RankineEarthPressureInput, RankineLayer, calculate_rankine_earth_pressure,
)
from calculators.foundation_bearing import FoundationBearingInput, calculate_foundation_bearing  # noqa: E402
from calculators.rebar_quick import RebarQuickInput, calculate_rebar_quick  # noqa: E402


TOOLS = [
    "bearing", "reinforcement", "section_design", "section_properties",
    "composite_section", "soil_three_phase", "darcy_law",
    "bolt_connection", "beam_forces", "rankine_earth_pressure", "foundation_bearing",
    "rebar_quick",
]

FIELDS = {
    "bearing": ["h0", "fc", "fy", "alpha1", "xi_b", "rho_min", "rho_max", "x", "xi", "as_req", "mu", "status"],
    "reinforcement": ["h0", "fc", "fy", "xi_b", "rho_min", "alpha_s", "xi", "gamma_s", "as_req", "as_min", "as_max", "need_double", "as_prime_req", "status"],
    "section_design": ["flexural.mu", "flexural.x", "flexural.xi", "flexural.as_req", "flexural.status", "shear.V_c", "shear.V_cs", "shear.V_max", "shear.A_sv", "shear.rho_sv", "shear.rho_sv_min", "shear.status"],
    "section_properties": ["A", "I_x", "I_y", "W_x", "W_y", "i_x", "i_y", "S_x", "y_c", "I_p", "status"],
    "composite_section": ["n_blocks", "n_holes", "A", "y_bar", "x_bar", "I_z", "I_y", "W_z_top", "W_z_bot", "W_y", "i_z", "i_y", "S_z", "status"],
    "soil_three_phase": ["Gs", "w", "gamma", "gamma_d", "gamma_sat", "gamma_prime", "e", "n", "Sr", "rho", "rho_d", "rho_sat"],
    "darcy_law": ["k", "i", "delta_h", "L", "Q", "v", "A", "j", "i_cr", "gamma_prime", "Gs", "e", "Fs"],
    "bolt_connection": ["per_bolt_capacity", "total_capacity", "control", "utilization", "passed", "details.shear_capacity", "details.bearing_capacity", "details.pretension"],
    "beam_forces": ["RA", "RB", "fixed_moment", "Vmax", "Mmax", "x_Mmax", "M_positive", "x_M_positive", "M_negative", "x_M_negative", "status"],
    "rankine_earth_pressure": ["total_height", "earth_resultant", "water_resultant", "total_resultant", "action_height", "earth_action_height", "water_action_height", "max_pressure"],
    "foundation_bearing": ["eta_b", "eta_d", "b_correction", "d_correction", "area", "Wx", "Wy", "Gk", "N", "fa", "width_increment", "depth_increment", "pk", "pmax", "pmin", "pmax_linear", "pmin_linear", "eccentricity", "contact_width", "pressure_mode", "full_contact", "supported", "stable", "mean_pass", "edge_pass", "overall_pass", "mean_utilization", "edge_utilization"],
    "rebar_quick": ["operation", "diameter", "nominal_area", "unit_weight", "total_length", "total_weight", "weight_tonnes", "bar_count", "interval_count", "actual_spacing", "source_area", "required_count", "replacement_area", "area_difference", "area_change_percent", "status"],
}


def rfloat(rng: random.Random, low: float, high: float, digits: int = 4) -> float:
    return round(rng.uniform(low, high), digits)


def generate_case(tool: str, rng: random.Random) -> dict:
    concrete = rng.choice(["C20", "C30", "C40", "C50", "C60", "C80"])
    rebar = rng.choice(["HPB300", "HRB400", "HRB500"])
    if tool == "bearing":
        h = rng.randrange(400, 1001, 20)
        case = {"b": rng.randrange(200, 501, 20), "h": h, "concrete_grade": concrete,
                "rebar_grade": rebar, "a_s": rng.randrange(30, min(81, h - 80), 5),
                "as_type": rng.choice(["single", "single", "double"])}
        if rng.random() < 0.75:
            case["as_given"] = rfloat(rng, 150, 5500, 1)
            if case["as_type"] == "double":
                case["a_s_prime"] = rng.randrange(30, 71, 5)
                case["as_prime_given"] = rfloat(rng, 50, case["as_given"] * 0.75, 1)
        return case
    if tool == "reinforcement":
        h = rng.randrange(400, 1001, 20)
        return {"M": rfloat(rng, 5, 1000, 3), "b": rng.randrange(200, 501, 20), "h": h,
                "concrete_grade": concrete, "rebar_grade": rebar, "a_s": rng.randrange(30, 76, 5),
                "a_s_prime": rng.randrange(30, 71, 5), "bar_diameters": [14, 16, 18, 20, 22, 25]}
    if tool == "section_design":
        h = rng.randrange(400, 1001, 20)
        load_type = rng.choice(["uniform", "concentrated"])
        case = {"b": rng.randrange(200, 501, 20), "h": h, "concrete_grade": concrete,
                "rebar_grade": rebar, "stirrup_grade": rng.choice(["HPB300", "HRB400"]),
                "a_s": rng.randrange(30, 76, 5), "a_s_prime": rng.randrange(30, 71, 5),
                "as_type": "single", "load_type": load_type}
        if load_type == "concentrated":
            case["shear_span_ratio"] = rfloat(rng, 1.5, 3.0, 3)
        if rng.random() < 0.7:
            case.update(stirrup_diameter=rng.choice([6, 8, 10, 12]),
                        stirrup_legs=rng.randint(1, 4), stirrup_spacing=rng.randrange(50, 401, 10))
        return case
    if tool == "section_properties":
        shape = rng.choice(["rectangle", "t-section", "circle", "annular", "i-beam"])
        if shape == "rectangle":
            return {"shape": shape, "b": rng.randrange(50, 801, 10), "h": rng.randrange(50, 1201, 10)}
        if shape == "circle":
            return {"shape": shape, "d": rng.randrange(20, 1001, 10)}
        if shape == "annular":
            outer = rng.randrange(60, 1001, 10)
            return {"shape": shape, "D": outer, "d": rng.randrange(10, outer, 10)}
        if shape == "t-section":
            bf = rng.randrange(100, 801, 10); h = rng.randrange(100, 1201, 10)
            return {"shape": shape, "b_f": bf, "h_f": rng.randrange(10, h, 10),
                    "b_w": rng.randrange(10, bf + 1, 10), "h": h}
        bf = rng.randrange(100, 801, 10); h = rng.randrange(100, 1201, 10)
        tf = rng.randrange(10, max(11, h // 2), 10)
        return {"shape": shape, "b_f": bf, "h": h, "t_f": tf,
                "t_w": rng.randrange(10, bf + 1, 10)}
    if tool == "composite_section":
        width = rng.randrange(100, 501, 10); height = rng.randrange(100, 801, 10)
        blocks = [{"b": width, "h": height, "x0": 0, "y0": 0, "label": "主体"}]
        if rng.random() < 0.6:
            hole_w = rng.randrange(10, max(11, width), 10); hole_h = rng.randrange(10, max(11, height), 10)
            blocks.append({"b": hole_w, "h": hole_h,
                           "x0": rfloat(rng, 0, width - hole_w, 2), "y0": rfloat(rng, 0, height - hole_h, 2),
                           "is_hole": True, "label": "孔洞"})
        if rng.random() < 0.5:
            blocks.append({"b": rng.randrange(20, 301, 10), "h": rng.randrange(20, 301, 10),
                           "x0": rfloat(rng, 0, width, 2), "y0": height, "label": "附加块"})
        return {"blocks": blocks}
    if tool == "soil_three_phase":
        gs = rfloat(rng, 2.55, 2.85, 4); e = rfloat(rng, 0.35, 1.2, 4)
        w = rfloat(rng, 0.02, min(0.45, e / gs * 0.95), 5)
        return {"Gs": gs, "w": w, "e": e, "gamma_w": rng.choice([9.81, 10.0])}
    if tool == "darcy_law":
        return {"k": 10 ** rng.uniform(-8, -3), "i": rfloat(rng, 0.01, 4, 6),
                "A": 10 ** rng.uniform(-4, 1), "gamma_w": rng.choice([9.81, 10.0])}
    if tool == "bolt_connection":
        if rng.random() < 0.55:
            return {"bolt_type": "ordinary", "diameter": rng.choice([12, 16, 20, 22, 24, 30]),
                    "bolt_count": rng.randint(1, 20), "shear_planes": rng.randint(1, 3),
                    "bolt_grade": rng.choice(["4.6", "4.8", "5.6", "8.8"]),
                    "steel_grade": rng.choice(["Q235", "Q355", "Q390", "Q420"]),
                    "connected_thickness": rfloat(rng, 4, 50, 2), "load": rfloat(rng, 1, 3000, 3)}
        return {"bolt_type": "high_strength", "diameter": rng.choice([16, 20, 22, 24, 27, 30]),
                "bolt_count": rng.randint(1, 20), "shear_planes": 1,
                "bolt_grade": rng.choice(["8.8", "10.9"]), "steel_grade": "Q355",
                "connected_thickness": rfloat(rng, 4, 50, 2), "load": rfloat(rng, 1, 3000, 3),
                "slip_coefficient": rfloat(rng, 0.25, 0.55, 3), "friction_surfaces": rng.randint(1, 3),
                "hole_type": rng.choice(["standard", "oversize", "slotted"])}
    if tool == "rankine_earth_pressure":
        layer_count = rng.randint(1, 4)
        has_water = rng.random() < 0.55
        layers = []
        for _ in range(layer_count):
            gamma = rfloat(rng, 15, 22, 3)
            layers.append({
                "h": rfloat(rng, 0.5, 6, 3),
                "gamma": gamma,
                "gamma_sat": rfloat(rng, max(gamma, 18), 24, 3),
                "phi": rfloat(rng, 0, 42, 3),
                "c": rfloat(rng, 0, 35, 3),
            })
        height = sum(item["h"] for item in layers)
        return {
            "mode": rng.choice(["active", "passive", "at_rest"]),
            "layers": layers,
            "q": rfloat(rng, 0, 80, 3),
            "water_table": rfloat(rng, 0, height, 3) if has_water else None,
            "water_method": rng.choice(["separate", "combined"]),
            "gamma_w": rng.choice([9.81, 10.0]),
        }
    if tool == "foundation_bearing":
        b = rfloat(rng, 1.0, 6.5, 3)
        length = rfloat(rng, b, 9.0, 3)
        fk = rfloat(rng, 50, 2500, 3)
        gk = rfloat(rng, 0, 700, 3)
        vertical = fk + gk
        mode = rng.choice(["axial", "uniaxial", "biaxial_full", "biaxial_separation"])
        mx = my = 0.0
        if mode == "uniaxial":
            direction = rng.choice(["x", "y"])
            dimension = length if direction == "x" else b
            eccentricity = rfloat(rng, 0, dimension * 0.45, 5)
            if direction == "x":
                mx = vertical * eccentricity
            else:
                my = vertical * eccentricity
        elif mode == "biaxial_full":
            mx = vertical * length * rfloat(rng, 0.005, 0.045, 5)
            my = vertical * b * rfloat(rng, 0.005, 0.045, 5)
        elif mode == "biaxial_separation":
            mx = vertical * length * rfloat(rng, 0.09, 0.18, 5)
            my = vertical * b * rfloat(rng, 0.09, 0.18, 5)
        soil = rng.choice([
            "silt_muck_fill_soft_clay", "red_clay_wet", "red_clay_dry",
            "silt_clay_ge10", "silt_clay_lt10", "cohesive_firm", "fine_sand", "coarse_soil",
        ])
        return {
            "b": b, "l": length, "d": rfloat(rng, 0.1, 5, 3),
            "fak": rfloat(rng, 60, 500, 3),
            "gamma": rfloat(rng, 7, 23, 3), "gamma_m": rfloat(rng, 7, 23, 3),
            "Fk": fk, "Gk": gk, "Mx": rfloat(rng, -mx, mx, 5) if mx else 0,
            "My": rfloat(rng, -my, my, 5) if my else 0, "soil_category": soil,
        }
    if tool == "rebar_quick":
        diameters = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40, 50]
        operation = rng.choice(["quantity", "weight_to_length", "spacing", "equivalent"])
        if operation == "quantity":
            return {"operation": operation, "diameter": rng.choice(diameters),
                    "bar_length": rfloat(rng, 0.1, 20, 3), "bar_count": rng.randint(1, 10000)}
        if operation == "weight_to_length":
            return {"operation": operation, "diameter": rng.choice(diameters),
                    "total_weight": rfloat(rng, 0.1, 100000, 3)}
        if operation == "spacing":
            return {"operation": operation, "diameter": rng.choice(diameters),
                    "layout_length": rfloat(rng, 50, 50000, 3),
                    "max_spacing": rfloat(rng, 50, 500, 3),
                    "bar_length": rfloat(rng, 0.1, 20, 3)}
        return {"operation": operation, "source_diameter": rng.choice(diameters),
                "source_count": rng.randint(1, 1000), "target_diameter": rng.choice(diameters)}
    length = rfloat(rng, 2, 20, 3)
    if rng.random() < 0.7:
        loads = [{"type": "point", "value": rfloat(rng, 1, 200, 3), "x": rfloat(rng, 0, length, 3)}]
        if rng.random() < 0.7:
            x1 = rfloat(rng, 0, length * 0.8, 3)
            loads.append({"type": "udl", "value": rfloat(rng, 0.5, 50, 3), "x1": x1,
                          "x2": rfloat(rng, x1 + 0.001, length, 3)})
        if rng.random() < 0.4:
            loads.append({"type": "moment", "value": rfloat(rng, 1, 150, 3),
                          "x": rfloat(rng, 0, length, 3), "direction": rng.choice(["clockwise", "counterclockwise"])})
        return {"beam_type": "simply_supported", "load_type": "combined", "L": length, "loads": loads}
    return {"beam_type": "cantilever", "load_type": "combined", "L": length,
            "fixed_end": rng.choice(["left", "right"]),
            "loads": [{"type": "point", "value": rfloat(rng, 1, 200, 3), "x": rfloat(rng, 0, length, 3)}]}


def dotted(value: dict, name: str):
    current = value
    for part in name.split("."):
        if current is None:
            return None
        current = current.get(part)
    return current


def select(value: dict, tool: str) -> dict:
    return {name: dotted(value, name) for name in FIELDS[tool]}


def reference(tool: str, inp: dict) -> dict:
    if tool == "bearing":
        return select(asdict(calculate_bearing_capacity(BearingCapacityInput(**inp))), tool)
    if tool == "reinforcement":
        adapted = dict(inp); adapted["bar_diameter_range"] = adapted.pop("bar_diameters", [14, 16, 18, 20, 22, 25])
        return select(asdict(calculate_reinforcement(ReinforcementInput(**adapted))), tool)
    if tool == "section_design":
        flex_keys = {"b", "h", "concrete_grade", "rebar_grade", "a_s", "a_s_prime", "as_type", "as_given", "as_prime_given"}
        shear_keys = {"b", "h", "concrete_grade", "stirrup_grade", "a_s", "load_type", "shear_span_ratio", "stirrup_diameter", "stirrup_legs", "stirrup_spacing"}
        flex = asdict(calculate_bearing_capacity(BearingCapacityInput(**{k: v for k, v in inp.items() if k in flex_keys})))
        shear = asdict(calculate_shear_capacity(ShearCapacityInput(**{k: v for k, v in inp.items() if k in shear_keys})))
        return select({"flexural": flex, "shear": shear}, tool)
    if tool == "section_properties":
        return select(asdict(calculate_section_properties(SectionPropertiesInput(**inp))), tool)
    if tool == "composite_section":
        result = calculate_composite_section([CompositeBlock(**item) for item in inp["blocks"]])
        return select(asdict(result), tool)
    if tool == "soil_three_phase":
        return select(asdict(calculate_soil_three_phase(SoilThreePhaseInput(**inp))), tool)
    if tool == "darcy_law":
        return select(asdict(calculate_darcy_law(DarcyLawInput(**inp))), tool)
    if tool == "bolt_connection":
        return select(calculate_bolt_connection(BoltConnectionInput(**inp)), tool)
    if tool == "rankine_earth_pressure":
        adapted = dict(inp)
        adapted["layers"] = [RankineLayer(**item) for item in inp["layers"]]
        return select(calculate_rankine_earth_pressure(RankineEarthPressureInput(**adapted)), tool)
    if tool == "foundation_bearing":
        return select(calculate_foundation_bearing(FoundationBearingInput(**inp)), tool)
    if tool == "rebar_quick":
        return select(calculate_rebar_quick(RebarQuickInput(**inp)), tool)
    adapted = dict(inp); adapted["loads"] = [BeamLoadInput(**item) for item in inp.get("loads", [])]
    return select(asdict(calculate_beam_forces(BeamForceInput(**adapted))), tool)


def tolerance(field: str, expected) -> tuple[float, float]:
    if not isinstance(expected, (int, float)) or isinstance(expected, bool):
        return 0.0, 0.0
    if field in {"rho_min", "rho_max", "rho_sv", "rho_sv_min"}:
        return 0.00011, 1e-9
    if field in {"nominal_area", "source_area", "replacement_area", "area_difference"}:
        return 0.0011, 1e-9
    if field in {"as_req", "as_min", "as_max", "as_prime_req", "A_sv",
                 }:
        return 0.11, 1e-9
    if field in {"x_bar", "y_bar", "i_x", "i_y", "i_z", "y_c"}:
        return 0.1000001, 1e-9
    if field in {"I_x", "I_y", "I_z", "I_p", "W_x", "W_y", "W_z_top", "W_z_bot", "S_x", "S_z"}:
        return 1.1, 1e-9
    return 0.0011, 1e-8


def compare(expected, actual, field: str) -> tuple[bool, float, float]:
    if expected is None or actual is None or isinstance(expected, (str, bool)):
        return expected == actual, 0.0, 0.0
    if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
        return False, math.inf, 0.0
    abs_tol, rel_tol = tolerance(field, expected)
    error = abs(float(actual) - float(expected))
    allowed = abs_tol + rel_tol * abs(float(expected))
    return error <= allowed, error, allowed


def git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch differential verification for engineering-calc")
    parser.add_argument("--cases-per-tool", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260719)
    parser.add_argument("--tools", default=",".join(TOOLS))
    parser.add_argument("--node", default=os.environ.get("NODE_EXE") or shutil.which("node"))
    parser.add_argument("--report")
    args = parser.parse_args()
    if not args.node:
        parser.error("Node.js not found. Pass --node C:\\path\\to\\node.exe or set NODE_EXE.")
    requested = [item.strip() for item in args.tools.split(",") if item.strip()]
    unknown = sorted(set(requested) - set(TOOLS))
    if unknown:
        parser.error(f"Unknown tools: {', '.join(unknown)}")
    if args.cases_per_tool < 1:
        parser.error("--cases-per-tool must be positive")

    rng = random.Random(args.seed)
    cases = []
    expected = {}
    generation_failures = []
    for tool in requested:
        for index in range(args.cases_per_tool):
            case_id = f"{tool}-{index + 1:05d}"
            inp = generate_case(tool, rng)
            try:
                expected[case_id] = reference(tool, inp)
                cases.append({"id": case_id, "tool": tool, "input": inp})
            except Exception as exc:
                generation_failures.append({"id": case_id, "tool": tool, "input": inp, "error": str(exc)})

    with tempfile.TemporaryDirectory(prefix="calculation-verifier-") as temp:
        input_path = Path(temp) / "cases.json"; output_path = Path(temp) / "results.json"
        property_path = Path(temp) / "properties.json"
        input_path.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(args.node), str(SKILL_DIR / "scripts" / "js_batch_runner.mjs"), str(REPO), str(input_path), str(output_path)], check=True)
        actual_results = json.loads(output_path.read_text(encoding="utf-8"))
        property_count = min(200, args.cases_per_tool)
        subprocess.run([str(args.node), str(SKILL_DIR / "scripts" / "property_checks.mjs"), str(REPO), str(property_path), str(property_count), str(args.seed)], check=True)
        property_results = json.loads(property_path.read_text(encoding="utf-8"))

    summaries = {tool: {"total": 0, "passed": 0, "max_error": 0.0, "max_field": ""} for tool in requested}
    failures = list(generation_failures)
    case_lookup = {item["id"]: item for item in cases}
    for result in actual_results:
        tool = result["tool"]; summary = summaries[tool]; summary["total"] += 1
        if not result["ok"]:
            failures.append({**case_lookup[result["id"]], "error": result.get("error", "JavaScript error")})
            continue
        case_ok = True
        for field in FIELDS[tool]:
            exp = expected[result["id"]].get(field); act = result["values"].get(field)
            ok, error, allowed = compare(exp, act, field)
            if math.isfinite(error) and error > summary["max_error"]:
                summary["max_error"] = error; summary["max_field"] = field
            if not ok:
                case_ok = False
                failures.append({**case_lookup[result["id"]], "field": field, "expected": exp,
                                 "actual": act, "absolute_error": error, "allowed_error": allowed})
                break
        if case_ok:
            summary["passed"] += 1

    summaries["mathematical_properties"] = {
        "total": property_results["total"], "passed": property_results["passed"],
        "max_error": 0.0, "max_field": "property checks",
    }
    failures.extend({"id": f"property-{index + 1:05d}", "tool": "mathematical_properties", **failure}
                    for index, failure in enumerate(property_results["failures"]))

    total = sum(item["total"] for item in summaries.values()) + len(generation_failures)
    passed = sum(item["passed"] for item in summaries.values())
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    report_path = Path(args.report) if args.report else REPO / "verification" / "reports" / f"verification-{datetime.now():%Y%m%d-%H%M%S}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 工程计算批量验算报告", "", f"- 时间：{timestamp}", f"- Git：`{git_revision()}`",
             f"- 随机种子：`{args.seed}`", f"- 每项计划算例：{args.cases_per_tool}", f"- 总通过：{passed}/{total}", "",
             "| 工具 | 算例数 | 通过数 | 通过率 | 最大绝对误差 | 对应字段 |", "|---|---:|---:|---:|---:|---|"]
    display_tools = requested + ["mathematical_properties"]
    for tool in display_tools:
        item = summaries[tool]; rate = item["passed"] / item["total"] * 100 if item["total"] else 0
        lines.append(f"| {tool} | {item['total']} | {item['passed']} | {rate:.2f}% | {item['max_error']:.6g} | {item['max_field'] or '-'} |")
    lines += ["", "## 失败算例", ""]
    if not failures:
        lines.append("无。Python 参考实现与 JavaScript 网页计算核心在本批算例中一致。")
    else:
        for failure in failures[:50]:
            lines += [f"### {failure.get('id')} · {failure.get('tool')}", "", "```json",
                      json.dumps(failure, ensure_ascii=False, indent=2, default=str), "```", ""]
        if len(failures) > 50:
            lines.append(f"另有 {len(failures) - 50} 个失败未展开。")
    lines += ["", "## 结论边界", "",
              "本报告同时覆盖 Python/JavaScript 差分验证和数学性质测试。"
              "它们不单独构成规范公式正确性的最终证明；正式发布前仍须同时通过标注出处的权威固定算例、"
              "非法输入测试、项目回归测试和 H5 构建。", ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"验证完成：{passed}/{total} 通过")
    print(f"报告：{report_path}")
    if failures:
        print(f"失败：{len(failures)}（首个：{failures[0].get('id')}）")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
