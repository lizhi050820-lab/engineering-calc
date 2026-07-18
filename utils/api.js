/**
 * 统一计算入口
 *
 * GitHub Pages 主版本与微信小程序均使用浏览器/设备本地计算。
 * Python FastAPI 保留为公式参考实现与自动回归测试基准。
 */

import { localApi } from './calculators/common.js'
import { calculateSoilThreePhase } from './calculators/soil-three-phase.js'
import { calculateDarcyLaw } from './calculators/darcy-law.js'
import { calculateBeamForces } from './calculators/beam-forces.js'
import { materialReferences } from './calculators/materials.js'
import { calculateBearingCapacity } from './calculators/bearing-capacity.js'
import { calculateReinforcement } from './calculators/reinforcement.js'
import { calculateSectionDesign } from './calculators/section-design.js'
import { calculateSectionProperties } from './calculators/section-properties.js'
import { calculateCompositeSection } from './calculators/composite-section.js'
import { calculateBoltConnection } from './calculators/bolt-connection.js'

/**
 * 获取材料参数参考表（混凝土、钢筋数据）
 */
export function getReferences() {
  return Promise.resolve(materialReferences())
}

/**
 * 正截面承载力计算
 * @param {Object} params
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 钢筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {string} params.as_type - "single" | "double"
 * @param {number} [params.as_given] - 已知受拉钢筋面积（校核模式）
 * @param {number} [params.as_prime_given] - 已知受压钢筋面积（双筋校核）
 */
export function calcBearingCapacity(params) {
  return localApi(calculateBearingCapacity, params)
}

/**
 * 配筋计算
 * @param {Object} params
 * @param {number} params.M - 设计弯矩 (kN·m)
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 钢筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {number[]} [params.bar_diameters] - 可选钢筋直径
 */
export function calcReinforcement(params) {
  return localApi(calculateReinforcement, params)
}

/**
 * 截面统一设计（正截面 + 斜截面）
 * @param {Object} params
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 纵筋牌号
 * @param {string} params.stirrup_grade - 箍筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {string} params.load_type - "uniform" | "concentrated"
 * @param {number} [params.shear_span_ratio] - 剪跨比
 * @param {number} [params.as_given] - 已知受拉钢筋面积
 * @param {number} [params.stirrup_diameter] - 箍筋直径
 * @param {number} [params.stirrup_legs] - 箍筋肢数
 * @param {number} [params.stirrup_spacing] - 箍筋间距
 */
export function calcSectionDesign(params) {
  return localApi(calculateSectionDesign, params)
}

/**
 * 截面几何性质计算
 * @param {Object} params
 * @param {string} params.shape - 截面形状: "rectangle"|"t-section"|"circle"|"annular"|"i-beam"
 * @param {number} [params.b] - 宽度 (mm) — 矩形
 * @param {number} [params.h] - 高度 (mm) — 矩形/T形/工字钢
 * @param {number} [params.b_f] - 翼缘宽度 (mm) — T形/工字钢
 * @param {number} [params.h_f] - 翼缘厚度 (mm) — T形
 * @param {number} [params.b_w] - 腹板宽度 (mm) — T形
 * @param {number} [params.t_f] - 翼缘厚度 (mm) — 工字钢
 * @param {number} [params.t_w] - 腹板厚度 (mm) — 工字钢
 * @param {number} [params.d] - 直径 (mm) — 圆形; 内径 (mm) — 环形
 * @param {number} [params.D] - 外径 (mm) — 环形
 */
export function calcSectionProperties(params) {
  return localApi(calculateSectionProperties, params)
}

/**
 * 组合截面几何性质计算（平行移轴公式）
 * @param {Object[]} params.blocks - 矩形分块列表
 * @param {number} params.blocks[].b - 宽度 (mm)
 * @param {number} params.blocks[].h - 高度 (mm)
 * @param {number} params.blocks[].y0 - 底边距参考轴距离 (mm)
 * @param {number} [params.blocks[].x0] - 左边距参考轴距离 (mm)，默认 0
 * @param {boolean} [params.blocks[].is_hole] - 是否为孔洞
 * @param {string} [params.blocks[].label] - 分块名称
 */
export function calcCompositeSection(params) {
  return localApi(calculateCompositeSection, params)
}

/**
 * 土力学三相比例指标计算
 * @param {Object} params - 已知指标（任意子集，通常 ≥3 个）
 * @param {number} [params.Gs] - 土粒比重
 * @param {number} [params.w] - 含水量（小数）
 * @param {number} [params.gamma] - 天然重度 (kN/m³)
 * @param {number} [params.gamma_d] - 干重度 (kN/m³)
 * @param {number} [params.gamma_sat] - 饱和重度 (kN/m³)
 * @param {number} [params.gamma_prime] - 有效重度 (kN/m³)
 * @param {number} [params.e] - 孔隙比
 * @param {number} [params.n] - 孔隙率（小数）
 * @param {number} [params.Sr] - 饱和度（小数）
 * @param {number} [params.rho] - 天然密度 (g/cm³)
 * @param {number} [params.rho_d] - 干密度 (g/cm³)
 * @param {number} [params.rho_sat] - 饱和密度 (g/cm³)
 * @param {number} [params.gamma_w] - 水的重度，默认 9.81
 */
export function calcSoilThreePhase(params) {
  return localApi(calculateSoilThreePhase, params)
}

/**
 * 达西定律渗透计算
 * @param {Object} params - 已知参数（任意子集）
 */
export function calcDarcyLaw(params) {
  return localApi(calculateDarcyLaw, params)
}

/** 钢结构螺栓连接承载力计算 */
export function calcBoltConnection(params) {
  return localApi(calculateBoltConnection, params)
}

/** 结构力学常见梁内力速算 */
export function calcBeamForces(params) {
  return localApi(calculateBeamForces, params)
}
