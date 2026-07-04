"""
土木工程计算工具箱 — FastAPI 后端

提供正截面承载力计算、配筋计算等 API
启动: uvicorn main:app --reload --host 0.0.0.0 --port 8000
文档: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional

from calculators.bearing_capacity import (
    BearingCapacityInput,
    calculate_bearing_capacity,
    CONCRETE_FC,
    CONCRETE_FT,
    REBAR_FY,
    REBAR_ES,
    REBAR_AREA,
)

from calculators.reinforcement import (
    ReinforcementInput,
    calculate_reinforcement,
)

from calculators.shear_capacity import (
    ShearCapacityInput,
    calculate_shear_capacity,
    STIRRUP_FYV,
)

from calculators.section_properties import (
    SectionPropertiesInput,
    calculate_section_properties,
)

from calculators.composite_section import (
    CompositeBlock,
    calculate_composite_section,
)

from calculators.soil_three_phase import (
    SoilThreePhaseInput,
    calculate_soil_three_phase,
)

from calculators.darcy_law import (
    DarcyLawInput,
    calculate_darcy_law,
)

app = FastAPI(
    title="土木工程计算工具箱",
    description="Civil Engineering Calculation Toolkit — 正截面承载力 · 配筋计算",
    version="0.1.0",
)

# CORS: 允许小程序和其他来源访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request / Response Models
# =============================================================================

class BearingCapacityRequest(BaseModel):
    """正截面承载力计算请求"""
    b: float = Field(..., gt=0, description="截面宽度 (mm)", examples=[300])
    h: float = Field(..., gt=0, description="截面高度 (mm)", examples=[600])
    concrete_grade: str = Field(
        default="C30",
        description="混凝土强度等级",
        examples=["C30"],
    )
    rebar_grade: str = Field(
        default="HRB400",
        description="钢筋牌号",
        examples=["HRB400"],
    )
    a_s: float = Field(default=40.0, ge=20, le=100,
                       description="受拉钢筋合力点至受拉边缘距离 (mm)")
    a_s_prime: float = Field(default=40.0, ge=20, le=100,
                             description="受压钢筋合力点至受压边缘距离 (mm)")
    as_type: Literal["single", "double"] = Field(
        default="single",
        description="截面类型: single=单筋, double=双筋",
    )
    as_given: Optional[float] = Field(
        default=None, gt=0,
        description="已知受拉钢筋面积 (mm²)，校核模式时填写",
    )
    as_prime_given: Optional[float] = Field(
        default=None, gt=0,
        description="已知受压钢筋面积 (mm²)，双筋校核时必填",
    )

    # 快捷选混凝土标号
    @field_validator("concrete_grade")
    @classmethod
    def validate_concrete(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in CONCRETE_FC:
            raise ValueError(f"不支持的混凝土强度等级: {v}，可选: {list(CONCRETE_FC.keys())}")
        return v

    @field_validator("rebar_grade")
    @classmethod
    def validate_rebar(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in REBAR_FY:
            raise ValueError(f"不支持的钢筋牌号: {v}，可选: {list(REBAR_FY.keys())}")
        return v


class BearingCapacityResponse(BaseModel):
    """正截面承载力计算结果响应"""
    success: bool = True
    data: dict
    message: str


class ReinforcementRequest(BaseModel):
    """配筋计算请求"""
    M: float = Field(..., gt=0, description="设计弯矩 (kN·m)", examples=[200])
    b: float = Field(..., gt=0, description="截面宽度 (mm)", examples=[300])
    h: float = Field(..., gt=0, description="截面高度 (mm)", examples=[600])
    concrete_grade: str = Field(default="C30", description="混凝土强度等级")
    rebar_grade: str = Field(default="HRB400", description="钢筋牌号")
    a_s: float = Field(default=40.0, ge=20, le=100,
                       description="受拉钢筋合力点至受拉边缘距离 (mm)")
    a_s_prime: float = Field(default=40.0, ge=20, le=100,
                             description="受压钢筋合力点至受压边缘距离 (mm)")
    bar_diameters: List[int] = Field(
        default=[14, 16, 18, 20, 22, 25],
        description="可选钢筋直径列表 (mm)",
    )

    @field_validator("concrete_grade")
    @classmethod
    def validate_concrete(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in CONCRETE_FC:
            raise ValueError(f"不支持的混凝土强度等级: {v}，可选: {list(CONCRETE_FC.keys())}")
        return v

    @field_validator("rebar_grade")
    @classmethod
    def validate_rebar(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in REBAR_FY:
            raise ValueError(f"不支持的钢筋牌号: {v}，可选: {list(REBAR_FY.keys())}")
        return v


class ReinforcementResponse(BaseModel):
    """配筋计算结果响应"""
    success: bool = True
    data: dict
    message: str


class SectionPropertiesRequest(BaseModel):
    """截面几何性质计算请求"""
    shape: Literal["rectangle", "t-section", "circle", "annular", "i-beam"] = Field(
        ..., description="截面形状",
    )
    b: Optional[float] = Field(default=None, gt=0, description="宽度 (mm) — 矩形", examples=[200])
    h: Optional[float] = Field(default=None, gt=0, description="高度 (mm) — 矩形/T形/工字钢", examples=[400])
    b_f: Optional[float] = Field(default=None, gt=0, description="翼缘宽度 (mm) — T形/工字钢", examples=[400])
    h_f: Optional[float] = Field(default=None, gt=0, description="翼缘厚度 (mm) — T形", examples=[100])
    b_w: Optional[float] = Field(default=None, gt=0, description="腹板宽度 (mm) — T形", examples=[200])
    t_f: Optional[float] = Field(default=None, gt=0, description="翼缘厚度 (mm) — 工字钢", examples=[20])
    t_w: Optional[float] = Field(default=None, gt=0, description="腹板厚度 (mm) — 工字钢", examples=[12])
    d: Optional[float] = Field(default=None, gt=0, description="直径 (mm) — 圆形; 内径 (mm) — 环形", examples=[200])
    D: Optional[float] = Field(default=None, gt=0, description="外径 (mm) — 环形", examples=[200])


class SectionPropertiesResponse(BaseModel):
    """截面几何性质计算结果响应"""
    success: bool = True
    data: dict
    message: str


class BlockItem(BaseModel):
    """组合截面 — 单个矩形分块"""
    b: float = Field(..., gt=0, description="宽度 (mm)", examples=[200])
    h: float = Field(..., gt=0, description="高度 (mm)", examples=[20])
    y0: float = Field(..., ge=0, description="底边距参考轴距离 (mm)", examples=[120])
    x0: float = Field(default=0.0, ge=0, description="左边距参考轴距离 (mm)", examples=[0])
    is_hole: bool = Field(default=False, description="是否为孔洞（负面积）")
    label: str = Field(default="", description="分块名称", examples=["上翼缘"])


class CompositeSectionRequest(BaseModel):
    """组合截面几何性质计算请求"""
    blocks: List[BlockItem] = Field(..., min_length=1, description="矩形分块列表")


class DarcyLawRequest(BaseModel):
    """达西定律渗透计算请求 — 全部可选"""
    k: Optional[float] = Field(default=None, gt=0, description="渗透系数 (m/s)")
    i: Optional[float] = Field(default=None, ge=0, description="水力梯度")
    delta_h: Optional[float] = Field(default=None, ge=0, description="水头差 (m)")
    L: Optional[float] = Field(default=None, gt=0, description="渗径长度 (m)")
    Q: Optional[float] = Field(default=None, ge=0, description="渗流量 (m³/s)")
    v: Optional[float] = Field(default=None, ge=0, description="渗透速度 (m/s)")
    A: Optional[float] = Field(default=None, gt=0, description="截面积 (m²)")
    t: Optional[float] = Field(default=None, gt=0, description="时间 (s)")
    a: Optional[float] = Field(default=None, gt=0, description="细管截面积 (cm²) — 变水头")
    h1: Optional[float] = Field(default=None, gt=0, description="初始水头 (cm)")
    h2: Optional[float] = Field(default=None, gt=0, description="终止水头 (cm)")
    j: Optional[float] = Field(default=None, ge=0, description="单位渗透力 (kN/m³)")
    J: Optional[float] = Field(default=None, ge=0, description="总渗透力 (kN)")
    V: Optional[float] = Field(default=None, gt=0, description="土体体积 (m³)")
    i_cr: Optional[float] = Field(default=None, ge=0, description="临界水力梯度")
    gamma_prime: Optional[float] = Field(default=None, gt=0, description="有效重度 (kN/m³)")
    Gs: Optional[float] = Field(default=None, gt=0, description="土粒比重")
    e: Optional[float] = Field(default=None, ge=0, description="孔隙比")
    Fs: Optional[float] = Field(default=None, ge=0, description="安全系数")
    gamma_w: float = Field(default=9.81, gt=0, description="水的重度 (kN/m³)")
    k_unit: str = Field(default="m/s", description="渗透系数输入单位: m/s, cm/s, m/d")


class DarcyLawLayer(BaseModel):
    """成层土 — 单层参数"""
    k_val: float = Field(..., gt=0, description="该层渗透系数")
    H: float = Field(..., gt=0, description="该层厚度 (m)")


class SoilThreePhaseRequest(BaseModel):
    """土力学三相比例指标计算请求"""
    Gs: Optional[float] = Field(default=None, gt=0, description="土粒比重（相对密度）", examples=[2.70])
    w: Optional[float] = Field(default=None, ge=0, description="含水量（小数，如 0.15=15%）", examples=[0.15])
    gamma: Optional[float] = Field(default=None, gt=0, description="天然重度 (kN/m³)", examples=[18.5])
    gamma_d: Optional[float] = Field(default=None, gt=0, description="干重度 (kN/m³)")
    gamma_sat: Optional[float] = Field(default=None, gt=0, description="饱和重度 (kN/m³)")
    gamma_prime: Optional[float] = Field(default=None, gt=0, description="有效重度 (kN/m³)")
    e: Optional[float] = Field(default=None, ge=0, description="孔隙比")
    n: Optional[float] = Field(default=None, ge=0, lt=1, description="孔隙率（小数）")
    Sr: Optional[float] = Field(default=None, ge=0, le=1, description="饱和度（小数，1.0=完全饱和）")
    rho: Optional[float] = Field(default=None, gt=0, description="天然密度 (g/cm³)")
    rho_d: Optional[float] = Field(default=None, gt=0, description="干密度 (g/cm³)")
    rho_sat: Optional[float] = Field(default=None, gt=0, description="饱和密度 (g/cm³)")
    gamma_w: float = Field(default=9.81, gt=0, description="水的重度 (kN/m³)，考试常用10")


class MaterialReferenceResponse(BaseModel):
    """材料参数参考表"""
    success: bool = True
    concrete: dict
    rebar: dict
    rebar_areas: dict


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
def root():
    """根路径"""
    return {
        "name": "土木工程计算工具箱 API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": [
            "POST /api/calculate/section-design      截面设计（正截面+斜截面）",
            "POST /api/calculate/bearing-capacity   正截面承载力计算",
            "POST /api/calculate/reinforcement       配筋计算",
            "POST /api/calculate/section-properties  截面几何性质计算",
            "POST /api/calculate/composite-section   组合截面（平行移轴）",
            "POST /api/calculate/soil-three-phase   土力学三相指标计算",
            "GET  /api/references                     材料参数参考表",
        ],
    }


@app.post("/api/calculate/bearing-capacity", response_model=BearingCapacityResponse)
def api_bearing_capacity(req: BearingCapacityRequest):
    """
    正截面承载力计算

    计算矩形截面受弯构件的正截面承载力，支持：
    - 校核模式：给定配筋，计算极限弯矩 Mu
    - 设计模式：给定截面，提供配筋-承载力对照表

    双筋模式下 as_given 和 as_prime_given 必须同时提供。
    """
    try:
        inp = BearingCapacityInput(
            b=req.b,
            h=req.h,
            concrete_grade=req.concrete_grade,
            rebar_grade=req.rebar_grade,
            a_s=req.a_s,
            a_s_prime=req.a_s_prime,
            as_type=req.as_type,
            as_given=req.as_given,
            as_prime_given=req.as_prime_given,
        )
        result = calculate_bearing_capacity(inp)

        data = {
            "h0": result.h0,
            "fc": result.fc,
            "fy": result.fy,
            "alpha1": result.alpha1,
            "xi_b": result.xi_b,
            "rho_min": round(result.rho_min, 5),
            "rho_max": round(result.rho_max, 5),
            "x": result.x,
            "xi": result.xi,
            "as_req": result.as_req,
            "mu": result.mu,
            "status": result.status,
            "steps": result.steps,
        }
        # 设计模式下附带三档配筋方案
        if result.design_points is not None:
            data["design_points"] = result.design_points

        return BearingCapacityResponse(
            success=True,
            data=data,
            message=result.message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/reinforcement", response_model=ReinforcementResponse)
def api_reinforcement(req: ReinforcementRequest):
    """
    配筋计算

    给定设计弯矩 M，计算所需钢筋面积并推荐选筋方案。
    自动判断是否需要双筋截面。

    返回包含：
    - 所需钢筋面积 As
    - 相对受压区高度 ξ
    - 选筋方案（多种钢筋直径搭配）
    - 判定信息（适筋/超筋/少筋）
    """
    try:
        inp = ReinforcementInput(
            M=req.M,
            b=req.b,
            h=req.h,
            concrete_grade=req.concrete_grade,
            rebar_grade=req.rebar_grade,
            a_s=req.a_s,
            a_s_prime=req.a_s_prime,
            bar_diameter_range=req.bar_diameters,
        )
        result = calculate_reinforcement(inp)

        return ReinforcementResponse(
            success=True,
            data={
                "h0": result.h0,
                "fc": result.fc,
                "fy": result.fy,
                "xi_b": result.xi_b,
                "rho_min": round(result.rho_min, 5),
                "alpha_s": result.alpha_s,
                "xi": result.xi,
                "gamma_s": result.gamma_s,
                "as_req": result.as_req,
                "as_min": round(result.as_min, 1),
                "as_max": round(result.as_max, 1),
                "need_double": result.need_double,
                "as_prime_req": round(result.as_prime_req, 1) if result.need_double else 0,
                "schemes": [
                    {"desc": s.description, "count": s.count,
                     "diameter": s.diameter, "area": s.area, "layout": s.layout}
                    for s in result.schemes
                ],
                "status": result.status,
                "steps": result.steps,
            },
            message=result.message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SectionDesignRequest(BaseModel):
    """截面统一设计请求 — 正截面 + 斜截面"""
    b: float = Field(..., gt=0, description="截面宽度 (mm)", examples=[300])
    h: float = Field(..., gt=0, description="截面高度 (mm)", examples=[600])
    concrete_grade: str = Field(default="C30", description="混凝土强度等级")
    rebar_grade: str = Field(default="HRB400", description="纵筋牌号")
    stirrup_grade: str = Field(default="HPB300", description="箍筋牌号")
    a_s: float = Field(default=40.0, ge=20, le=100, description="受拉纵筋保护层厚度 (mm)")
    a_s_prime: float = Field(default=40.0, ge=20, le=100, description="受压纵筋保护层厚度 (mm)")
    as_type: Literal["single", "double"] = Field(default="single", description="配筋类型: single=单筋, double=双筋")
    load_type: Literal["uniform", "concentrated"] = Field(default="uniform", description="荷载类型")
    shear_span_ratio: Optional[float] = Field(default=None, ge=1.5, le=3.0, description="剪跨比 (集中荷载时必填)")
    # 正截面校核（可选）
    as_given: Optional[float] = Field(default=None, gt=0, description="已知受拉钢筋面积 (mm²)")
    as_prime_given: Optional[float] = Field(default=None, gt=0, description="已知受压钢筋面积 (mm²)，双筋校核时填写")
    # 斜截面校核（可选）
    stirrup_diameter: Optional[float] = Field(default=None, ge=6, le=12, description="箍筋直径 (mm)")
    stirrup_legs: int = Field(default=2, ge=1, le=4, description="箍筋肢数")
    stirrup_spacing: Optional[float] = Field(default=None, ge=50, le=400, description="箍筋间距 (mm)")

    @field_validator("concrete_grade")
    @classmethod
    def validate_concrete(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in CONCRETE_FC:
            raise ValueError(f"不支持的混凝土强度等级: {v}")
        return v

    @field_validator("rebar_grade")
    @classmethod
    def validate_rebar(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in REBAR_FY:
            raise ValueError(f"不支持的钢筋牌号: {v}")
        return v

    @field_validator("stirrup_grade")
    @classmethod
    def validate_stirrup(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in STIRRUP_FYV:
            raise ValueError(f"不支持的箍筋牌号: {v}，可选: {list(STIRRUP_FYV.keys())}")
        return v


@app.post("/api/calculate/section-design")
def api_section_design(req: SectionDesignRequest):
    """
    截面统一设计 — 同时完成正截面和斜截面计算

    输入截面尺寸和材料，一次返回：
    - flexural: 正截面承载力（最小/最大配筋、弯矩）
    - shear: 斜截面受剪承载力（V_c、V_cs、V_max）
    """
    try:
        # --- 正截面计算 ---
        flex_inp = BearingCapacityInput(
            b=req.b, h=req.h,
            concrete_grade=req.concrete_grade,
            rebar_grade=req.rebar_grade,
            a_s=req.a_s, a_s_prime=req.a_s_prime,
            as_type=req.as_type,
            as_given=req.as_given,
            as_prime_given=req.as_prime_given,
        )
        flex_result = calculate_bearing_capacity(flex_inp)

        flex_data = {
            "h0": flex_result.h0,
            "fc": flex_result.fc,
            "fy": flex_result.fy,
            "alpha1": flex_result.alpha1,
            "xi_b": flex_result.xi_b,
            "rho_min": round(flex_result.rho_min, 5),
            "rho_max": round(flex_result.rho_max, 5),
            "x": flex_result.x,
            "xi": flex_result.xi,
            "as_req": flex_result.as_req,
            "mu": flex_result.mu,
            "status": flex_result.status,
            "message": flex_result.message,
            "steps": flex_result.steps,
        }
        if flex_result.design_points is not None:
            flex_data["design_points"] = flex_result.design_points

        # --- 斜截面计算 ---
        shear_inp = ShearCapacityInput(
            b=req.b, h=req.h,
            concrete_grade=req.concrete_grade,
            stirrup_grade=req.stirrup_grade,
            a_s=req.a_s,
            load_type=req.load_type,
            shear_span_ratio=req.shear_span_ratio,
            stirrup_diameter=req.stirrup_diameter,
            stirrup_legs=req.stirrup_legs,
            stirrup_spacing=req.stirrup_spacing,
        )
        shear_result = calculate_shear_capacity(shear_inp)

        shear_data = {
            "h0": shear_result.h0,
            "fc": shear_result.fc,
            "ft": shear_result.ft,
            "f_yv": shear_result.f_yv,
            "beta_c": shear_result.beta_c,
            "beta_h": shear_result.beta_h,
            "V_c": shear_result.V_c,
            "V_cs": shear_result.V_cs,
            "V_max": shear_result.V_max,
            "A_sv": shear_result.A_sv,
            "rho_sv": shear_result.rho_sv,
            "rho_sv_min": shear_result.rho_sv_min,
            "status": shear_result.status,
            "message": shear_result.message,
            "steps": shear_result.steps,
        }

        return {
            "success": True,
            "message": f"正截面: {flex_result.message} | 斜截面: {shear_result.message}",
            "data": {
                "flexural": flex_data,
                "shear": shear_data,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/section-properties", response_model=SectionPropertiesResponse)
def api_section_properties(req: SectionPropertiesRequest):
    """
    截面几何性质计算

    支持五种截面形状：矩形、T形、圆形、环形、工字钢。
    根据所选形状填写对应尺寸参数，计算：
    - 面积 A
    - 惯性矩 I_x, I_y
    - 抵抗矩 W_x, W_y
    - 回转半径 i_x, i_y
    - 面积矩 S_x
    """
    try:
        inp = SectionPropertiesInput(
            shape=req.shape,
            b=req.b or 0.0,
            h=req.h or 0.0,
            b_f=req.b_f or 0.0,
            h_f=req.h_f or 0.0,
            b_w=req.b_w or 0.0,
            t_f=req.t_f or 0.0,
            t_w=req.t_w or 0.0,
            d=req.d or 0.0,
            D=req.D or 0.0,
        )
        result = calculate_section_properties(inp)

        data = {
            "shape": result.shape,
            "A": result.A,
            "I_x": result.I_x,
            "I_y": result.I_y,
            "W_x": result.W_x,
            "W_y": result.W_y,
            "i_x": result.i_x,
            "i_y": result.i_y,
            "S_x": result.S_x,
            "y_c": result.y_c,
            "I_p": result.I_p,
            "steps": result.steps,
            "status": result.status,
        }

        return SectionPropertiesResponse(
            success=True,
            data=data,
            message=result.message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/composite-section")
def api_composite_section(req: CompositeSectionRequest):
    """
    组合截面几何性质计算（平行移轴公式）

    用户自定义若干矩形分块（含孔洞），以底边为参考轴，
    通过平行移轴公式计算组合截面的形心位置和惯性矩。

    返回：
    - 组合形心位置 y_bar
    - 惯性矩 I_z, I_y
    - 抵抗矩 W_z_top, W_z_bot, W_y
    - 回转半径 i_z, i_y
    - 面积矩 S_z
    - 各分块计算明细表
    """
    try:
        blocks = []
        for item in req.blocks:
            blocks.append(CompositeBlock(
                b=item.b,
                h=item.h,
                y0=item.y0,
                x0=item.x0,
                is_hole=item.is_hole,
                label=item.label,
            ))

        result = calculate_composite_section(blocks)

        data = {
            "shape": "composite",
            "n_blocks": result.n_blocks,
            "n_holes": result.n_holes,
            "A": result.A,
            "y_bar": result.y_bar,
            "x_bar": result.x_bar,
            "I_z": result.I_z,
            "I_y": result.I_y,
            "W_z_top": result.W_z_top,
            "W_z_bot": result.W_z_bot,
            "W_y": result.W_y,
            "i_z": result.i_z,
            "i_y": result.i_y,
            "S_z": result.S_z,
            "y_max": result.y_max,
            "y_min": result.y_min,
            "block_details": [
                {
                    "label": d.label,
                    "b": d.b,
                    "h": d.h,
                    "y0": d.y0,
                    "A": d.A,
                    "y_ci": d.y_ci,
                    "d_y": d.d_y,
                    "I_zc": d.I_zc,
                    "Ady2": d.Ady2,
                    "I_z_contrib": d.I_z_contrib,
                    "is_hole": d.is_hole,
                }
                for d in result.block_details
            ],
            "steps": result.steps,
            "status": result.status,
        }

        return {
            "success": True,
            "data": data,
            "message": result.message,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/soil-three-phase")
def api_soil_three_phase(req: SoilThreePhaseRequest):
    """
    土力学三相比例指标计算

    输入任意已知指标（通常 ≥3 个），系统通过约束传播推导所有未知指标。

    核心公式基于三相草图法（令 V_s = 1），可推导:
    - 试验指标: Gs, w, γ
    - 换算指标: e, n, Sr, γ_d, γ_sat, γ'
    - 密度指标: ρ, ρ_d, ρ_sat
    """
    try:
        inp = SoilThreePhaseInput(
            Gs=req.Gs,
            w=req.w,
            gamma=req.gamma,
            gamma_d=req.gamma_d,
            gamma_sat=req.gamma_sat,
            gamma_prime=req.gamma_prime,
            e=req.e,
            n=req.n,
            Sr=req.Sr,
            rho=req.rho,
            rho_d=req.rho_d,
            rho_sat=req.rho_sat,
            gamma_w=req.gamma_w,
        )
        result = calculate_soil_three_phase(inp)

        data = {
            "Gs": result.Gs,
            "w": result.w,
            "gamma": result.gamma,
            "gamma_d": result.gamma_d,
            "gamma_sat": result.gamma_sat,
            "gamma_prime": result.gamma_prime,
            "e": result.e,
            "n": result.n,
            "Sr": result.Sr,
            "rho": result.rho,
            "rho_d": result.rho_d,
            "rho_sat": result.rho_sat,
            "gamma_w": result.gamma_w,
            "derivations": [
                {"symbol": d.symbol, "value": d.value, "formula": d.formula, "unit": d.unit}
                for d in result.derivations
            ],
            "missing": result.missing,
        }

        return {
            "success": True,
            "data": data,
            "message": result.message,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/darcy-law")
def api_darcy_law(req: DarcyLawRequest):
    """
    达西定律与渗透计算

    输入任意已知参数，通过约束传播推导所有未知量。

    涵盖:
    - 达西定律: v = k·i, Q = k·i·A
    - 常水头试验: k = Q·L/(A·Δh·t)
    - 变水头试验: k = a·L/(A·t)·ln(h1/h2)
    - 渗透力: j = γw·i, J = j·V
    - 临界水力梯度: i_cr = γ'/γw = (Gs-1)/(1+e)
    - 安全系数: Fs = i_cr/i
    - 流土判别
    """
    try:
        inp = DarcyLawInput(
            k=req.k, i=req.i, delta_h=req.delta_h, L=req.L,
            Q=req.Q, v=req.v, A=req.A, t=req.t,
            a=req.a, h1=req.h1, h2=req.h2,
            j=req.j, J=req.J, V=req.V,
            i_cr=req.i_cr, gamma_prime=req.gamma_prime,
            Gs=req.Gs, e=req.e, Fs=req.Fs,
            gamma_w=req.gamma_w,
        )
        result = calculate_darcy_law(inp)

        data = {
            "k": result.k, "i": result.i,
            "delta_h": result.delta_h, "L": result.L,
            "Q": result.Q, "v": result.v,
            "A": result.A, "t": result.t,
            "a": result.a, "h1": result.h1, "h2": result.h2,
            "j": result.j, "J": result.J, "V": result.V,
            "i_cr": result.i_cr, "gamma_prime": result.gamma_prime,
            "Gs": result.Gs, "e": result.e, "Fs": result.Fs,
            "gamma_w": result.gamma_w,
            "quicksand_risk": result.quicksand_risk,
            "derivations": [
                {"symbol": d.symbol, "value": d.value, "formula": d.formula, "unit": d.unit}
                for d in result.derivations
            ],
            "missing": result.missing,
        }

        return {"success": True, "data": data, "message": result.message}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/references", response_model=MaterialReferenceResponse)
def api_references():
    """
    获取材料参数参考表

    返回混凝土强度设计值、钢筋强度设计值、钢筋公称面积表。
    用于前端下拉框和参数校验。
    """
    return MaterialReferenceResponse(
        success=True,
        concrete={
            "grades": list(CONCRETE_FC.keys()),
            "fc": CONCRETE_FC,
            "ft": CONCRETE_FT,
        },
        rebar={
            "grades": list(REBAR_FY.keys()),
            "fy": REBAR_FY,
            "es": REBAR_ES,
        },
        rebar_areas={str(k): v for k, v in REBAR_AREA.items()},
    )


# =============================================================================
# 启动入口
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
