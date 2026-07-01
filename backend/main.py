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
            "POST /api/calculate/section-design     截面设计（正截面+斜截面）",
            "POST /api/calculate/bearing-capacity  正截面承载力计算",
            "POST /api/calculate/reinforcement      配筋计算",
            "GET  /api/references                    材料参数参考表",
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
    a_s: float = Field(default=40.0, ge=20, le=100, description="纵筋保护层厚度 (mm)")
    load_type: Literal["uniform", "concentrated"] = Field(default="uniform", description="荷载类型")
    shear_span_ratio: Optional[float] = Field(default=None, ge=1.5, le=3.0, description="剪跨比 (集中荷载时必填)")
    # 正截面校核（可选）
    as_given: Optional[float] = Field(default=None, gt=0, description="已知受拉钢筋面积 (mm²)")
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
            a_s=req.a_s, a_s_prime=req.a_s,
            as_type="single",
            as_given=req.as_given,
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
