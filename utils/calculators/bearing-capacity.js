import { roundTo, requirePositive } from './common.js'
import { CONCRETE_FC, CONCRETE_FT, REBAR_FY, getAlpha1, getBeta1, getXiB } from './materials.js'

function baseInput(raw) {
  const input = {
    ...raw, b: requirePositive(raw.b, '截面宽度 b'), h: requirePositive(raw.h, '截面高度 h'),
    a_s: requirePositive(raw.a_s ?? 40, '受拉钢筋合力点距离 a_s'),
    a_s_prime: requirePositive(raw.a_s_prime ?? 40, '受压钢筋合力点距离 a_s′')
  }
  input.as_given = raw.as_given === null || raw.as_given === undefined || raw.as_given === '' ? null : requirePositive(raw.as_given, '受拉钢筋面积 As')
  input.as_prime_given = raw.as_prime_given === null || raw.as_prime_given === undefined || raw.as_prime_given === '' ? null : requirePositive(raw.as_prime_given, '受压钢筋面积 As′')
  if (!CONCRETE_FC[input.concrete_grade]) throw new Error(`不支持的混凝土强度等级: ${input.concrete_grade}`)
  if (!REBAR_FY[input.rebar_grade]) throw new Error(`不支持的钢筋牌号: ${input.rebar_grade}`)
  if (input.h <= input.a_s) throw new Error('截面高度 h 必须大于 a_s')
  return input
}

function common(input) {
  const fc = CONCRETE_FC[input.concrete_grade], fy = REBAR_FY[input.rebar_grade]
  const alpha1 = getAlpha1(input.concrete_grade), xiB = getXiB(input.concrete_grade, input.rebar_grade)
  const rhoMin = Math.max(0.002, 0.45 * CONCRETE_FT[input.concrete_grade] / fy), h0 = input.h - input.a_s
  return { fc, fy, alpha1, xiB, rhoMin, h0, rhoMax: xiB * alpha1 * fc / fy }
}

function wrapResult(result, message) {
  const data = {
    h0: result.h0, fc: result.fc, fy: result.fy, alpha1: result.alpha1,
    xi_b: roundTo(result.xi_b, 3), rho_min: roundTo(result.rho_min, 5),
    rho_max: roundTo(result.rho_max, 5), x: roundTo(result.x, 3), xi: roundTo(result.xi, 3),
    as_req: result.as_req, mu: roundTo(result.mu, 3), status: result.status, steps: result.steps
  }
  if (result.design_points !== undefined && result.design_points !== null) data.design_points = result.design_points
  return { data, message }
}

function single(input, c) {
  const { b, h } = input, { fc, fy, alpha1, xiB, rhoMin, rhoMax, h0 } = c
  const steps = []
  if (input.as_given !== null) {
    const As = input.as_given, x = fy * As / (alpha1 * fc * b), xi = x / h0
    const mu = alpha1 * fc * b * x * (h0 - x / 2) / 1e6
    steps.push(`已知受拉钢筋面积 As = ${As.toFixed(1)} mm²`, '由力平衡：α₁·f꜀·b·x = fᵧ·As', `x = fᵧ·As/(α₁·f꜀·b) = ${x.toFixed(2)} mm`, `ξ = x/h₀ = ${xi.toFixed(4)}`, `Mᵤ = α₁·f꜀·b·x·(h₀−x/2) = ${mu.toFixed(3)} kN·m`)
    let status = 'ok', message = '适筋梁，满足规范要求'
    if (xi > xiB) { status = 'over_reinforced'; message = `超筋！ξ = ${xi.toFixed(4)} > ξb = ${xiB.toFixed(4)}，应增大截面或采用双筋截面` }
    else if (As / (b * h) < rhoMin) { status = 'under_reinforced'; message = `少筋！配筋率 ρ = ${(As / (b * h)).toFixed(4)} < ρ_min = ${rhoMin.toFixed(4)}` }
    return wrapResult({ h0, fc, fy, alpha1, xi_b: xiB, rho_min: rhoMin, rho_max: rhoMax, x, xi, as_req: As, mu, status, steps }, message)
  }

  const AsMax = rhoMax * b * h0, xMax = xiB * h0
  const muMax = alpha1 * fc * b * xMax * (h0 - xMax / 2) / 1e6
  const point = (label, rho, As, note) => {
    const x = fy * As / (alpha1 * fc * b), xi = x / h0
    return { label, rho: roundTo(rho, 4), As: roundTo(As, 1), x: roundTo(x), xi: roundTo(xi), Mu: roundTo(alpha1 * fc * b * x * (h0 - x / 2) / 1e6), note }
  }
  const min = point('最小配筋', rhoMin, rhoMin * b * h, '按规范最小配筋率，承载力低，实际工程一般不采用')
  const max = point('最大配筋(界限)', rhoMax, AsMax, '单筋截面承载力上限，超过需改为双筋截面')
  steps.push('=== 单筋矩形截面设计 ===', `截面 b×h = ${b}×${h} mm，有效高度 h₀ = ${h0} mm`, `α₁ = ${alpha1}，β₁ = ${getBeta1(input.concrete_grade)}，ξb = ${xiB.toFixed(4)}`, `最小配筋率 ρ_min = ${rhoMin.toFixed(4)}`, `最大配筋率 ρ_max = ${rhoMax.toFixed(4)}`, `最小配筋 As = ${min.As.toFixed(1)} mm²，Mᵤ = ${min.Mu.toFixed(3)} kN·m`, `界限配筋 As = ${max.As.toFixed(1)} mm²，Mᵤ = ${max.Mu.toFixed(3)} kN·m`)
  return wrapResult({ h0, fc, fy, alpha1, xi_b: xiB, rho_min: rhoMin, rho_max: rhoMax, x: xMax, xi: xiB, as_req: roundTo(AsMax, 1), mu: muMax, status: 'ok', steps, design_points: [min, max] }, `单筋截面设计：最小配筋 ${min.As.toFixed(1)} mm² (Mu=${min.Mu.toFixed(3)} kN·m) / 最大配筋 ${max.As.toFixed(1)} mm² (Mu=${max.Mu.toFixed(3)} kN·m)`)
}

function double(input, c) {
  const { b, h, a_s_prime: asPrimeDistance } = input
  const { fc, fy, alpha1, xiB, rhoMin, rhoMax, h0 } = c
  const steps = []
  if (input.as_given !== null && input.as_prime_given !== null) {
    const As = input.as_given, AsPrime = input.as_prime_given
    let x = fy * (As - AsPrime) / (alpha1 * fc * b), xi = x / h0, mu, status, message, xResult = x
    steps.push('=== 双筋截面校核 ===', `受拉钢筋 As = ${As.toFixed(1)} mm²，受压钢筋 As′ = ${AsPrime.toFixed(1)} mm²`)
    if (x < 2 * asPrimeDistance) {
      xResult = 2 * asPrimeDistance; xi = xResult / h0; mu = fy * As * (h0 - asPrimeDistance) / 1e6
      steps.push(`受压钢筋未屈服（x=${x.toFixed(2)} < 2a_s′=${(2 * asPrimeDistance).toFixed(0)}）`, `Mᵤ = fᵧ·As·(h₀−a_s′) = ${mu.toFixed(3)} kN·m`)
      if (As / (b * h) < rhoMin) { status = 'under_reinforced'; message = '少筋！受拉配筋率不满足最小要求' }
      else { status = 'ok'; message = `受压钢筋未屈服，按 x < 2a_s′ 的简化公式计算，Mu = ${mu.toFixed(2)} kN·m` }
    } else if (xi > xiB) {
      x = xiB * h0; xResult = x; xi = xiB
      mu = (alpha1 * fc * b * x * (h0 - x / 2) + fy * AsPrime * (h0 - asPrimeDistance)) / 1e6
      status = 'over_reinforced'; message = `超筋！承载力按 ξ=ξb 取为 ${mu.toFixed(2)} kN·m`
      steps.push(`超筋：ξ = ${(fy * (As - AsPrime) / (alpha1 * fc * b) / h0).toFixed(4)} > ξb = ${xiB.toFixed(4)}`, `按 ξ=ξb，Mᵤ = ${mu.toFixed(3)} kN·m`)
    } else {
      mu = (alpha1 * fc * b * x * (h0 - x / 2) + fy * AsPrime * (h0 - asPrimeDistance)) / 1e6
      if (As / (b * h) < rhoMin) { status = 'under_reinforced'; message = '少筋！受拉配筋率不满足最小要求' }
      else { status = 'ok'; message = `双筋截面，承载力 Mu = ${mu.toFixed(2)} kN·m` }
      steps.push(`x = (fᵧ·As−fᵧ′·As′)/(α₁·f꜀·b) = ${x.toFixed(2)} mm`, `Mᵤ = α₁·f꜀·b·x·(h₀−x/2)+fᵧ′·As′·(h₀−a_s′) = ${mu.toFixed(3)} kN·m`)
    }
    return wrapResult({ h0, fc, fy, alpha1, xi_b: xiB, rho_min: rhoMin, rho_max: rhoMax, x: xResult, xi, as_req: As, mu, status, steps }, message)
  }
  if ((input.as_given === null) !== (input.as_prime_given === null)) throw new Error('双筋校核时必须同时填写 As 和 As′')

  const As1Max = rhoMax * b * h0, xMax = xiB * h0
  const singleMax = alpha1 * fc * b * xMax * (h0 - xMax / 2) / 1e6
  const stepM = Math.max(50, Math.round(singleMax * 0.15 / 50) * 50)
  const moments = [singleMax, singleMax + stepM, singleMax + 2 * stepM, singleMax + 3 * stepM]
  if (moments[moments.length - 1] < singleMax * 2) moments.push(singleMax * 2)
  const points = moments.slice(1).map(M => {
    const AsPrime = (M - singleMax) * 1e6 / (fy * (h0 - asPrimeDistance)), As = As1Max + AsPrime
    return { label: `M=${M.toFixed(1)} kN·m`, rho: roundTo(As / (b * h), 4), As: roundTo(As, 1), As_prime: roundTo(AsPrime, 1), M: roundTo(M), Mu_single_max: roundTo(singleMax), note: '需双筋' }
  })
  steps.push('=== 双筋矩形截面设计参考 ===', `单筋截面最大承载力 Mᵤ,max = ${singleMax.toFixed(3)} kN·m`, `受压钢筋面积 As′ = (M−Mᵤ,max)×10⁶/[fᵧ′(h₀−a_s′)]`, `受拉钢筋面积 As = ${As1Max.toFixed(1)} + As′`)
  return wrapResult({ h0, fc, fy, alpha1, xi_b: xiB, rho_min: rhoMin, rho_max: rhoMax, x: xMax, xi: xiB, as_req: roundTo(As1Max, 1), mu: singleMax, status: 'ok', steps, design_points: points }, `双筋截面设计参考：单筋上限 ${singleMax.toFixed(3)} kN·m，超出部分需配置受压钢筋`)
}

export function calculateBearingCapacity(raw) {
  const input = baseInput(raw), c = common(input)
  return input.as_type === 'double' ? double(input, c) : single(input, c)
}
