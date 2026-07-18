import { roundTo, requirePositive } from './common.js'
import { CONCRETE_FC, CONCRETE_FT, REBAR_FY, REBAR_AREA, getAlpha1, getXiB } from './materials.js'

function schemesFor(required, diameters) {
  const schemes = []
  for (const raw of diameters) {
    const diameter = Number(raw), single = REBAR_AREA[diameter]
    if (!single) continue
    for (let count = 2; count <= 10; count += 1) {
      const area = count * single
      if (area >= required && area <= required * 1.3) {
        schemes.push({ desc: `${count}Φ${diameter}`, count, diameter, area: roundTo(area, 1), layout: count <= 5 ? '单排' : '双排' })
        break
      }
    }
  }
  return schemes.sort((a, b) => Math.abs(a.area - required) - Math.abs(b.area - required)).slice(0, 5)
}

export function calculateReinforcement(raw) {
  const input = {
    ...raw, M: requirePositive(raw.M, '设计弯矩 M'), b: requirePositive(raw.b, '截面宽度 b'),
    h: requirePositive(raw.h, '截面高度 h'), a_s: requirePositive(raw.a_s ?? 40, 'a_s'),
    a_s_prime: requirePositive(raw.a_s_prime ?? 40, 'a_s′')
  }
  const fc = CONCRETE_FC[input.concrete_grade], fy = REBAR_FY[input.rebar_grade]
  if (!fc) throw new Error(`不支持的混凝土强度等级: ${input.concrete_grade}`)
  if (!fy) throw new Error(`不支持的钢筋牌号: ${input.rebar_grade}`)
  const h0 = input.h - input.a_s
  if (h0 <= 0 || h0 <= input.a_s_prime) throw new Error('截面有效高度必须大于 a_s′')
  const alpha1 = getAlpha1(input.concrete_grade), xiB = getXiB(input.concrete_grade, input.rebar_grade)
  const rhoMin = Math.max(0.002, 0.45 * CONCRETE_FT[input.concrete_grade] / fy)
  const M = input.M * 1e6, alphaS = M / (alpha1 * fc * input.b * h0 ** 2)
  const alphaSMax = xiB * (1 - 0.5 * xiB), steps = ['=== 单筋矩形截面配筋计算 ===', `截面有效高度 h₀ = h−a_s = ${input.h}−${input.a_s} = ${h0} mm`, `设计弯矩 M = ${input.M} kN·m`, `1. 截面抵抗矩系数 αs = ${alphaS.toFixed(4)}`]
  let xi, gammaS, As, AsPrime = 0, M2 = 0, needDouble = false, status, message
  const AsMin = rhoMin * input.b * input.h, AsMax = xiB * alpha1 * fc * input.b * h0 / fy
  if (alphaS > alphaSMax) {
    xi = xiB; gammaS = 1 - 0.5 * xiB; needDouble = true
    const M1Max = alpha1 * fc * input.b * h0 ** 2 * alphaSMax / 1e6
    M2 = input.M - M1Max; AsPrime = M2 * 1e6 / (fy * (h0 - input.a_s_prime)); As = AsMax + AsPrime
    status = 'need_double'; message = `需要双筋截面！As = ${As.toFixed(1)} mm², As' = ${AsPrime.toFixed(1)} mm²`
    steps.push(`2. αs = ${alphaS.toFixed(4)} > αs,max = ${alphaSMax.toFixed(4)}，按 ξ = ξb 转入双筋设计`, `单筋部分最大弯矩 M₁,max = ${M1Max.toFixed(2)} kN·m`, `剩余弯矩 M₂ = ${M2.toFixed(2)} kN·m`, `受压钢筋 As′ = ${AsPrime.toFixed(1)} mm²`, `受拉钢筋 As = As₁ + As′ = ${As.toFixed(1)} mm²`)
  } else {
    xi = 1 - Math.sqrt(1 - 2 * alphaS); gammaS = 1 - 0.5 * xi
    As = M / (fy * gammaS * h0)
    steps.push(`2. 相对受压区高度 ξ = 1−√(1−2αs) = ${xi.toFixed(4)}`, `3. 内力臂系数 γs = 1−0.5ξ = ${gammaS.toFixed(4)}`, `4. 所需钢筋面积 As = M/(fᵧ·γs·h₀) = ${As.toFixed(1)} mm²`, `5. 最小配筋面积 As,min = ${AsMin.toFixed(1)} mm²`, `单筋最大配筋面积 As,max = ${AsMax.toFixed(1)} mm²`)
    if (As < AsMin) { As = AsMin; status = 'min_reinforcement'; message = `计算配筋小于最小要求，按构造配筋 As = ${AsMin.toFixed(1)} mm²` }
    else { status = 'ok'; message = `所需钢筋面积 As = ${As.toFixed(1)} mm²` }
  }
  const diameters = Array.isArray(raw.bar_diameters) ? raw.bar_diameters : (Array.isArray(raw.bar_diameter_range) ? raw.bar_diameter_range : [14, 16, 18, 20, 22, 25])
  const schemes = schemesFor(As > 0 ? As : Math.max(AsMin, 100), diameters)
  if (needDouble && AsPrime > 0) {
    steps.push('7. 受压钢筋选筋方案:')
    schemesFor(AsPrime, diameters).slice(0, 3).forEach(item => steps.push(`${item.desc}（面积 ${item.area.toFixed(1)} mm²）`))
  }
  steps.push('8. 受拉钢筋选筋方案:')
  schemes.forEach((item, index) => steps.push(`方案${index + 1}: ${item.desc}，面积 ${item.area.toFixed(1)} mm²（${item.layout}）`))
  return {
    data: {
      h0, fc, fy, xi_b: roundTo(xiB, 4), rho_min: roundTo(rhoMin, 5), alpha_s: roundTo(alphaS, 4),
      xi: roundTo(xi, 4), gamma_s: roundTo(gammaS, 4), as_req: roundTo(As, 1), as_min: roundTo(AsMin, 1),
      as_max: roundTo(AsMax, 1), need_double: needDouble, as_prime_req: needDouble ? roundTo(AsPrime, 1) : 0,
      schemes, status, steps
    }, message
  }
}
