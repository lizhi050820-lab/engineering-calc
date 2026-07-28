import { roundTo, requirePositive } from './common.js'

export const SOIL_CORRECTION_PRESETS = {
  silt_muck_fill_soft_clay: { label: '淤泥、人工填土或软黏性土', eta_b: 0, eta_d: 1.0 },
  red_clay_wet: { label: '红黏土（含水比 αw＞0.8）', eta_b: 0, eta_d: 1.2 },
  red_clay_dry: { label: '红黏土（含水比 αw≤0.8）', eta_b: 0.15, eta_d: 1.4 },
  compacted_silt: { label: '大面积压实粉土', eta_b: 0, eta_d: 1.5 },
  compacted_gravel: { label: '大面积压实级配砂石', eta_b: 0, eta_d: 2.0 },
  silt_clay_ge10: { label: '粉土（黏粒含量≥10%）', eta_b: 0.3, eta_d: 1.5 },
  silt_clay_lt10: { label: '粉土（黏粒含量＜10%）', eta_b: 0.5, eta_d: 2.0 },
  cohesive_firm: { label: 'e、IL 均＜0.85 的黏性土', eta_b: 0.3, eta_d: 1.6 },
  fine_sand: { label: '粉砂、细砂（不含很湿/饱和稍密）', eta_b: 2.0, eta_d: 3.0 },
  coarse_soil: { label: '中粗砂、砾砂及碎石土', eta_b: 3.0, eta_d: 4.4 },
  custom: { label: '自定义修正系数', eta_b: null, eta_d: null }
}

const finiteNonnegative = (value, label) => {
  const number = Number(value ?? 0)
  if (!Number.isFinite(number) || number < 0) throw new Error(`${label}不能小于 0`)
  return number
}

function normalize(raw = {}) {
  const b = requirePositive(raw.b, '基础宽度 b')
  const l = requirePositive(raw.l, '基础长度 l')
  const d = finiteNonnegative(raw.d, '基础埋深 d')
  const fak = requirePositive(raw.fak, '地基承载力特征值 fak')
  const gamma = requirePositive(raw.gamma, '基底以下土重度 γ')
  const gammaM = requirePositive(raw.gamma_m, '基底以上土平均重度 γm')
  const Fk = finiteNonnegative(raw.Fk, '上部竖向力 Fk')
  const Mx = Number(raw.Mx ?? 0)
  const My = Number(raw.My ?? 0)
  if (!Number.isFinite(Mx) || !Number.isFinite(My)) throw new Error('基础底面弯矩必须为有效数字')

  const soilCategory = raw.soil_category || 'cohesive_firm'
  const preset = SOIL_CORRECTION_PRESETS[soilCategory]
  if (!preset) throw new Error('不支持的持力层土类别')
  if (soilCategory === 'custom' && (raw.eta_b === undefined || raw.eta_b === null || raw.eta_b === '' ||
    raw.eta_d === undefined || raw.eta_d === null || raw.eta_d === '')) {
    throw new Error('自定义土类必须填写 ηb 和 ηd')
  }
  const etaB = finiteNonnegative(soilCategory === 'custom' ? raw.eta_b : preset.eta_b, '宽度修正系数 ηb')
  const etaD = finiteNonnegative(soilCategory === 'custom' ? raw.eta_d : preset.eta_d, '深度修正系数 ηd')

  const area = b * l
  let weightSource = 'manual'
  let foundationWeightPressure = null
  let Gk
  if (raw.Gk !== undefined && raw.Gk !== null && raw.Gk !== '') {
    Gk = finiteNonnegative(raw.Gk, '基础及覆土重 Gk')
  } else {
    foundationWeightPressure = requirePositive(raw.foundation_weight_pressure ?? 20, '单位面积基础及覆土重')
    Gk = foundationWeightPressure * area
    weightSource = 'auto'
  }
  const N = Fk + Gk
  if (N <= 0) throw new Error('竖向合力 Fk＋Gk 必须大于 0')

  return {
    b, l, d, fak, gamma, gamma_m: gammaM, Fk, Gk, Mx, My, N, area,
    soil_category: soilCategory, soil_label: preset.label, eta_b: etaB, eta_d: etaD,
    weight_source: weightSource, foundation_weight_pressure: foundationWeightPressure
  }
}

export function calculateFoundationBearing(raw = {}) {
  const input = normalize(raw)
  const bCorrection = Math.min(6, Math.max(3, Math.min(input.b, input.l)))
  const dCorrection = Math.max(0.5, input.d)
  const widthIncrement = input.eta_b * input.gamma * (bCorrection - 3)
  const depthIncrement = input.eta_d * input.gamma_m * (dCorrection - 0.5)
  const fa = input.fak + widthIncrement + depthIncrement

  const Wx = input.b * input.l ** 2 / 6
  const Wy = input.l * input.b ** 2 / 6
  const tx = Math.abs(input.Mx) / Wx
  const ty = Math.abs(input.My) / Wy
  const pk = input.N / input.area
  const pmaxLinear = pk + tx + ty
  const pminLinear = pk - tx - ty
  const tolerance = 1e-10
  const hasMx = Math.abs(input.Mx) > tolerance
  const hasMy = Math.abs(input.My) > tolerance
  const biaxial = hasMx && hasMy
  let fullContact = pminLinear >= -tolerance
  let supported = true
  let stable = true
  let pressureMode = hasMx || hasMy ? 'linear_full_contact' : 'uniform'
  let pmax = pmaxLinear
  let pmin = Math.max(pminLinear, 0)
  let contactWidth = hasMy ? input.b : input.l
  let eccentricity = 0

  if (!fullContact) {
    if (biaxial) {
      supported = false
      pressureMode = 'biaxial_separation_review'
      pmax = null
      pmin = pminLinear
      contactWidth = null
    } else {
      const moment = Math.max(Math.abs(input.Mx), Math.abs(input.My))
      const directionSize = hasMy ? input.b : input.l
      const perpendicularSize = hasMy ? input.l : input.b
      eccentricity = moment / input.N
      const a = directionSize / 2 - eccentricity
      pressureMode = 'uniaxial_triangular_contact'
      if (a <= 0) {
        supported = false
        stable = false
        pressureMode = 'resultant_outside_base'
        pmax = null
        pmin = null
        contactWidth = 0
      } else {
        pmax = 2 * input.N / (3 * perpendicularSize * a)
        pmin = 0
        contactWidth = 3 * a
      }
    }
  }

  const meanPass = pk <= fa + tolerance
  const edgePass = supported && stable && pmax !== null ? pmax <= 1.2 * fa + tolerance : null
  const overallPass = meanPass && edgePass === true && stable && supported
  let status = overallPass ? 'pass' : 'fail'
  if (!supported && stable) status = 'review'
  if (!stable) status = 'unstable'

  const corners = {
    top_left: pk + input.Mx / Wx - input.My / Wy,
    top_right: pk + input.Mx / Wx + input.My / Wy,
    bottom_left: pk - input.Mx / Wx - input.My / Wy,
    bottom_right: pk - input.Mx / Wx + input.My / Wy
  }
  const steps = [
    `基础底面积 A = b·l = ${input.b.toFixed(3)}×${input.l.toFixed(3)} = ${input.area.toFixed(3)} m²`,
    `修正用宽度 b₀ = ${bCorrection.toFixed(3)} m，修正用埋深 d₀ = ${dCorrection.toFixed(3)} m`,
    `fₐ = fₐₖ＋ηbγ(b₀－3)＋ηdγm(d₀－0.5) = ${fa.toFixed(3)} kPa`,
    `竖向合力 Nₖ = Fₖ＋Gₖ = ${input.N.toFixed(3)} kN`,
    `平均压力 pₖ = Nₖ/A = ${pk.toFixed(3)} kPa`,
    `基础底面抵抗矩 Wₓ = ${Wx.toFixed(3)} m³，Wᵧ = ${Wy.toFixed(3)} m³`,
    pressureMode === 'uniaxial_triangular_contact'
      ? `单向大偏心：e = ${eccentricity.toFixed(3)} m，受压宽度 3a = ${contactWidth.toFixed(3)} m，pₖ,max = ${pmax.toFixed(3)} kPa`
      : pressureMode === 'biaxial_separation_review'
        ? '双向偏心出现基底脱空，规范简化线性压力公式不再适用，需进行专门的接触压力分析'
        : pressureMode === 'resultant_outside_base'
          ? '竖向合力作用线位于基础底面以外，基础存在倾覆失稳风险'
          : `基底保持全截面受压，pₖ,max = ${pmax.toFixed(3)} kPa，pₖ,min = ${pmin.toFixed(3)} kPa`,
    `平均压力验算：pₖ ${meanPass ? '≤' : '＞'} fₐ`,
    edgePass === null
      ? '边缘最大压力验算：当前工况不适用本页简化公式'
      : `边缘压力验算：pₖ,max ${edgePass ? '≤' : '＞'} 1.2fₐ`
  ]

  const roundedCorners = Object.fromEntries(Object.entries(corners).map(([key, value]) => [key, roundTo(value)]))
  return {
    data: {
      soil_category: input.soil_category,
      soil_label: input.soil_label,
      eta_b: roundTo(input.eta_b),
      eta_d: roundTo(input.eta_d),
      b_correction: roundTo(bCorrection),
      d_correction: roundTo(dCorrection),
      area: roundTo(input.area),
      Wx: roundTo(Wx),
      Wy: roundTo(Wy),
      Gk: roundTo(input.Gk),
      N: roundTo(input.N),
      fa: roundTo(fa),
      width_increment: roundTo(widthIncrement),
      depth_increment: roundTo(depthIncrement),
      pk: roundTo(pk),
      pmax: pmax === null ? null : roundTo(pmax),
      pmin: pmin === null ? null : roundTo(pmin),
      pmax_linear: roundTo(pmaxLinear),
      pmin_linear: roundTo(pminLinear),
      eccentricity: roundTo(eccentricity),
      contact_width: contactWidth === null ? null : roundTo(contactWidth),
      pressure_mode: pressureMode,
      full_contact: fullContact,
      supported,
      stable,
      mean_pass: meanPass,
      edge_pass: edgePass,
      overall_pass: overallPass,
      mean_utilization: roundTo(pk / fa),
      edge_utilization: pmax === null ? null : roundTo(pmax / (1.2 * fa)),
      corners: roundedCorners,
      steps,
      assumptions: [
        '采用作用标准组合，基础底面为矩形，输入弯矩为基础底面形心处弯矩',
        'fₐₖ 应由勘察、载荷试验、原位测试或工程经验综合确定，本工具不替代勘察',
        '未包含软弱下卧层、沉降、抗滑、抗倾覆、冲切和基础配筋验算'
      ],
      weight_source: input.weight_source,
      foundation_weight_pressure: input.foundation_weight_pressure
    },
    message: overallPass ? '地基承载力验算满足' : status === 'review' ? '需要进行接触压力专项复核' : '地基承载力验算不满足',
    status
  }
}
