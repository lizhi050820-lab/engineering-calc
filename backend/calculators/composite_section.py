"""
组合截面几何性质计算器（平行移轴公式）

依据：《材料力学》附录I — 截面几何性质 · 平行移轴定理

功能：用户自定义若干矩形分块，以底边为参考轴，通过平行移轴公式
      计算组合截面的形心位置和惯性矩。

典型应用场景：
  - 考試常见题：T形/工字形/槽形/L形等组合截面惯性矩计算
  - 含孔洞截面（负面积法）
  - 任意矩形组合截面

平行移轴公式：I_z = I_zc + a²·A
  I_zc — 图形对自身形心轴的惯性矩
  a   — 两平行轴间距
  A   — 图形面积
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class CompositeBlock:
    """组合截面的一个矩形分块"""
    b: float          # 宽度 (mm)，平行于 x 轴
    h: float          # 高度 (mm)，平行于 y 轴
    y0: float         # 底边距参考轴的距离 (mm)，参考轴通常取截面底边 y=0
    x0: float = 0.0   # 左边距参考轴的距离 (mm)，参考轴通常取截面左边缘 x=0
    is_hole: bool = False  # 是否为孔洞（负面积）
    label: str = ""   # 分块名称（如"翼缘""腹板""孔洞"）


@dataclass
class BlockCalcDetail:
    """单个分块的计算过程"""
    label: str
    b: float
    h: float
    y0: float
    A: float           # 面积（孔洞为负）
    y_ci: float        # 分块形心距参考轴距离
    d_y: float         # 分块形心到组合形心距离
    I_zc: float        # 自身对形心轴惯性矩  b·h³/12
    Ady2: float        # 移轴项 A·d_y²
    I_z_contrib: float # 贡献 I_zc + A·d_y²
    is_hole: bool


@dataclass
class CompositeSectionResult:
    """组合截面计算结果"""
    shape: str = "composite"
    n_blocks: int = 0
    n_holes: int = 0
    A: float = 0.0          # 总面积（扣除孔洞）(mm²)
    y_bar: float = 0.0      # 形心距参考轴距离 (mm)
    x_bar: float = 0.0      # 形心距参考轴距离 (mm)
    I_z: float = 0.0        # 对水平形心轴惯性矩 (mm⁴)
    I_y: float = 0.0        # 对竖直形心轴惯性矩 (mm⁴)
    W_z_top: float = 0.0    # 上边缘抵抗矩 (mm³)
    W_z_bot: float = 0.0    # 下边缘抵抗矩 (mm³)
    W_y: float = 0.0        # 水平方向抵抗矩 (mm³)
    i_z: float = 0.0        # 对z轴回转半径 (mm)
    i_y: float = 0.0        # 对y轴回转半径 (mm)
    S_z: float = 0.0        # 最大面积矩（中性轴处）(mm³)
    y_max: float = 0.0      # 截面最高点距参考轴 (mm)
    y_min: float = 0.0      # 截面最低点距参考轴 (mm)
    block_details: list = field(default_factory=list)  # 各分块计算明细
    steps: list = field(default_factory=list)
    status: str = "ok"
    message: str = ""


# =============================================================================
# 核心计算
# =============================================================================

def calculate_composite_section(blocks: List[CompositeBlock]) -> CompositeSectionResult:
    """
    用平行移轴公式计算组合截面的几何性质

    步骤:
    1. 求各分块面积和自身形心位置
    2. 求组合截面形心
    3. 用平行移轴公式计算各分块对形心轴的惯性矩
    4. 求和
    """

    if not blocks:
        raise ValueError("请至少添加一个分块")

    # --- 第1步：汇总各分块基本信息 ---
    solids = [b for b in blocks if not b.is_hole]
    if not solids:
        raise ValueError("至少需要一个实体分块（非孔洞）")

    areas = []
    y_centroids = []   # 各分块形心 y 坐标（距参考轴）
    x_centroids = []   # 各分块形心 x 坐标（距参考轴）

    for blk in blocks:
        A_i = blk.b * blk.h
        y_ci = blk.y0 + blk.h / 2   # 形心 y
        x_ci = blk.x0 + blk.b / 2   # 形心 x

        if blk.is_hole:
            areas.append(-A_i)
        else:
            areas.append(A_i)

        y_centroids.append(y_ci)
        x_centroids.append(x_ci)

    # 总面积（净面积）
    A_total = sum(areas)

    if A_total <= 0:
        raise ValueError(f"净面积必须大于0，当前净面积 A = {A_total:.1f} mm²（孔洞太大）")

    # --- 第2步：求组合截面形心（静矩法） ---
    # y_bar = Σ(A_i * y_ci) / ΣA_i
    S_z_ref = sum(a * y for a, y in zip(areas, y_centroids))  # 对参考轴的静矩
    y_bar = S_z_ref / A_total

    S_y_ref = sum(a * x for a, x in zip(areas, x_centroids))
    x_bar = S_y_ref / A_total

    # --- 第3步：平行移轴公式计算各分块对形心轴的惯性矩 ---
    steps = []
    steps.append("=== 组合截面几何性质计算（平行移轴公式） ===")
    steps.append(f"分块数量: {len(blocks)}（实体 {len(solids)} + 孔洞 {len(blocks) - len(solids)}）")
    steps.append("")
    steps.append("--- 第1步：求组合截面形心 ---")
    steps.append(f"参考轴：底边 y=0，左边缘 x=0")
    steps.append("")

    # 形心计算明细
    for i, blk in enumerate(blocks):
        a = areas[i]
        yc = y_centroids[i]
        sign = "（孔洞，负面积）" if blk.is_hole else ""
        steps.append(
            f"  分块{i+1}[{blk.label or f'矩形{i+1}'}]: "
            f"A = {blk.b:.0f}×{blk.h:.0f} = {abs(a):.0f} mm²{sign}, "
            f"形心 y_c = {blk.y0:.0f} + {blk.h:.0f}/2 = {yc:.1f} mm"
        )

    steps.append("")
    steps.append(f"  总面积 A = {' + '.join(f'{a:.0f}' for a in areas)} = {A_total:.1f} mm²")
    steps.append(f"  形心 ȳ = Σ(A_i·y_ci) / ΣA_i = {S_z_ref:.1f} / {A_total:.1f} = {y_bar:.1f} mm")
    steps.append(f"  形心 x̄ = Σ(A_i·x_ci) / ΣA_i = {S_y_ref:.1f} / {A_total:.1f} = {x_bar:.1f} mm")
    steps.append("")

    # --- 各分块惯性矩计算 ---
    steps.append("--- 第2步：平行移轴公式 I_z = I_zc + A·d² ---")
    steps.append("")

    block_details = []
    I_z_total = 0.0
    I_y_total = 0.0

    # 用于后续 S_z 计算
    y_max_val = -1e9
    y_min_val = 1e9
    x_max_val = -1e9
    x_min_val = 1e9

    for i, blk in enumerate(blocks):
        label = blk.label or f"矩形{i+1}"
        A_i = blk.b * blk.h
        y_ci = blk.y0 + blk.h / 2
        x_ci = blk.x0 + blk.b / 2

        # 自身对形心轴的惯性矩
        I_zc_i = blk.b * blk.h**3 / 12
        I_yc_i = blk.h * blk.b**3 / 12

        # 到组合形心的距离
        d_y = y_ci - y_bar
        d_x = x_ci - x_bar

        # 移轴项
        Ady2 = A_i * d_y**2
        Adx2 = A_i * d_x**2

        # 对组合形心轴的贡献
        I_z_contrib = I_zc_i + Ady2
        I_y_contrib = I_yc_i + Adx2

        # 孔洞扣除
        sign = -1 if blk.is_hole else 1

        detail = BlockCalcDetail(
            label=label,
            b=blk.b, h=blk.h, y0=blk.y0,
            A=sign * A_i,
            y_ci=y_ci,
            d_y=round(d_y, 1),
            I_zc=round(I_zc_i, 0),
            Ady2=round(Ady2, 0),
            I_z_contrib=round(sign * I_z_contrib, 0),
            is_hole=blk.is_hole,
        )
        block_details.append(detail)

        I_z_total += sign * I_z_contrib
        I_y_total += sign * I_y_contrib

        # 形心计算过程行
        steps.append(
            f"  [{label}] b={blk.b:.0f}, h={blk.h:.0f}, "
            f"y₀={blk.y0:.0f}, A={abs(detail.A):.0f} mm²"
        )
        steps.append(
            f"    自身 I_zc = b·h³/12 = {blk.b:.0f}×{blk.h:.0f}³/12 = {I_zc_i:.0f} mm⁴"
        )
        steps.append(
            f"    形心距 y_ci = {y_ci:.1f}, d_y = y_ci − ȳ = {y_ci:.1f} − {y_bar:.1f} = {d_y:.1f} mm"
        )
        steps.append(
            f"    A·d_y² = {A_i:.0f} × {d_y:.1f}² = {Ady2:.0f} mm⁴"
        )
        steps.append(
            f"    I_z = I_zc + A·d_y² = {I_zc_i:.0f} + {Ady2:.0f} = {detail.I_z_contrib:.0f} mm⁴"
            + ("（孔洞扣除）" if blk.is_hole else "")
        )
        steps.append("")

        # 记录截面边界范围
        y_max_val = max(y_max_val, blk.y0 + blk.h)
        y_min_val = min(y_min_val, blk.y0)
        x_max_val = max(x_max_val, blk.x0 + blk.b)
        x_min_val = min(x_min_val, blk.x0)

    # --- 第4步：求和 ---
    steps.append("--- 第3步：求和 ---")
    contrib_str = " + ".join(
        f"{d.I_z_contrib:.0f}" for d in block_details
    )
    steps.append(f"  I_z = {contrib_str} = {I_z_total:.0f} mm⁴")
    steps.append(f"  I_y = {I_y_total:.0f} mm⁴")
    steps.append("")

    # --- 抵抗矩 ---
    y_top = y_max_val - y_bar   # 形心到截面顶边
    y_bot = y_bar - y_min_val   # 形心到截面底边

    W_z_top = I_z_total / y_top if y_top > 0 else 0
    W_z_bot = I_z_total / y_bot if y_bot > 0 else 0

    x_right = x_max_val - x_bar
    x_left = x_bar - x_min_val
    W_y = I_y_total / max(x_left, x_right) if max(x_left, x_right) > 0 else 0

    # --- 回转半径 ---
    i_z = np.sqrt(abs(I_z_total) / A_total)
    i_y = np.sqrt(abs(I_y_total) / A_total)

    # --- 面积矩（中性轴以上部分对中性轴的静矩） ---
    S_z = 0.0
    for blk in blocks:
        sign = -1 if blk.is_hole else 1
        y_top_i = blk.y0 + blk.h   # 分块顶边
        y_bot_i = blk.y0           # 分块底边

        if y_bot_i >= y_bar:
            # 整个分块在中性轴以上
            y_ci = blk.y0 + blk.h / 2
            S_z += sign * blk.b * blk.h * (y_ci - y_bar)
        elif y_top_i <= y_bar:
            # 整个分块在中性轴以下，不计入 S_z（取上方部分即可）
            pass
        else:
            # 中性轴穿过该分块，仅取中性轴以上部分
            h_above = y_top_i - y_bar
            S_z += sign * blk.b * h_above * (h_above / 2)

    S_z = abs(S_z)  # 面积矩取正值

    steps.append("--- 截面特性汇总 ---")
    steps.append(f"  截面总高度 H = {y_max_val - y_min_val:.0f} mm")
    steps.append(f"  形心距底边 ȳ = {y_bar:.1f} mm")
    steps.append(f"  形心距顶边 y_top = {y_top:.1f} mm")
    steps.append(f"  抵抗矩 W_z_top = I_z / y_top = {W_z_top:.0f} mm³")
    steps.append(f"  抵抗矩 W_z_bot = I_z / y_bot = {W_z_bot:.0f} mm³")
    steps.append(f"  回转半径 i_z = √(I_z/A) = {i_z:.1f} mm")
    steps.append(f"  面积矩 S_z = {S_z:.0f} mm³")

    # --- 精度处理 ---
    A_total = round(A_total, 1)
    I_z_total = round(I_z_total, 0)
    I_y_total = round(I_y_total, 0)
    W_z_top = round(W_z_top, 0)
    W_z_bot = round(W_z_bot, 0)
    W_y = round(W_y, 0)
    i_z = round(i_z, 1)
    i_y = round(i_y, 1)
    S_z = round(S_z, 0)
    y_bar = round(y_bar, 1)
    x_bar = round(x_bar, 1)

    return CompositeSectionResult(
        n_blocks=len(blocks),
        n_holes=len(blocks) - len(solids),
        A=A_total,
        y_bar=y_bar,
        x_bar=x_bar,
        I_z=I_z_total,
        I_y=I_y_total,
        W_z_top=W_z_top,
        W_z_bot=W_z_bot,
        W_y=W_y,
        i_z=i_z,
        i_y=i_y,
        S_z=S_z,
        y_max=y_max_val,
        y_min=y_min_val,
        block_details=block_details,
        steps=steps,
        message=f"组合截面计算完成（{len(blocks)}个分块，形心距底边 {y_bar:.1f} mm）",
    )
