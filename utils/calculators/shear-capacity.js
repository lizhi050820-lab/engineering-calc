import { roundTo, requirePositive } from './common.js'
import { CONCRETE_FC, CONCRETE_FT, REBAR_AREA, STIRRUP_FYV } from './materials.js'

export function getBetaC(grade) {
  const strength = Number(String(grade).slice(1))
  return strength <= 50 ? 1 : Math.max(0.8, roundTo(1 - (strength - 50) * 0.2 / 30, 2))
}

export function getBetaH(h0) {
  const height = Math.min(2000, Math.max(800, h0))
  return roundTo((800 / height) ** 0.25, 4)
}

export function calculateShearCapacity(raw) {
  const b = requirePositive(raw.b, '截面宽度 b'), h = requirePositive(raw.h, '截面高度 h')
  const as = requirePositive(raw.a_s ?? 40, 'a_s'), h0 = h - as
  if (h0 <= 0) throw new Error('截面高度 h 必须大于 a_s')
  const fc = CONCRETE_FC[raw.concrete_grade], ft = CONCRETE_FT[raw.concrete_grade], fyv = STIRRUP_FYV[raw.stirrup_grade]
  if (!fc || !ft) throw new Error(`不支持的混凝土等级: ${raw.concrete_grade}`)
  if (!fyv) throw new Error(`不支持的箍筋牌号: ${raw.stirrup_grade}`)
  const betaC = getBetaC(raw.concrete_grade), betaH = getBetaH(h0)
  const Vmax = 0.25 * betaC * fc * b * h0 / 1000
  let Vc
  const steps = ['=== 斜截面受剪承载力计算 ===', `截面 b×h = ${b}×${h} mm，h₀ = ${h0} mm`, `β꜀ = ${betaC}，βₕ = ${betaH.toFixed(4)}`, `1. 截面限制 Vmax = 0.25·β꜀·f꜀·b·h₀ = ${Vmax.toFixed(3)} kN`]
  if (raw.load_type === 'concentrated') {
    if (raw.shear_span_ratio === null || raw.shear_span_ratio === undefined || raw.shear_span_ratio === '') throw new Error('集中荷载时需提供剪跨比 λ')
    const lambda = Math.max(1.5, Math.min(3, Number(raw.shear_span_ratio)))
    Vc = 1.75 / (lambda + 1) * ft * b * h0 / 1000
    steps.push(`2. 集中荷载混凝土项 V꜀ = 1.75/(λ+1)·fₜ·b·h₀ = ${Vc.toFixed(3)} kN`)
  } else {
    Vc = 0.7 * betaH * ft * b * h0 / 1000
    steps.push(`2. 均布荷载混凝土项 V꜀ = 0.7·βₕ·fₜ·b·h₀ = ${Vc.toFixed(3)} kN`)
  }
  const rhoMin = 0.24 * ft / fyv
  steps.push(`3. 最小配箍率 ρₛᵥ,min = 0.24fₜ/fᵧᵥ = ${rhoMin.toFixed(4)}`)
  let Asv = 0, rho = 0, Vcs = Vc, status = 'ok', message
  const hasStirrup = raw.stirrup_diameter !== null && raw.stirrup_diameter !== undefined && raw.stirrup_diameter !== '' && raw.stirrup_spacing !== null && raw.stirrup_spacing !== undefined && raw.stirrup_spacing !== ''
  if (hasStirrup) {
    const diameter = Number(raw.stirrup_diameter), single = REBAR_AREA[Math.trunc(diameter)]
    if (!single || diameter !== Math.trunc(diameter)) throw new Error(`不支持的箍筋直径: ${diameter}mm`)
    const legs = Math.trunc(requirePositive(raw.stirrup_legs ?? 2, '箍筋肢数')), spacing = requirePositive(raw.stirrup_spacing, '箍筋间距')
    Asv = legs * single; rho = Asv / (b * spacing)
    const Vsv = fyv * Asv / spacing * h0 / 1000; Vcs = Vc + Vsv
    steps.push(`4. 箍筋 Φ${diameter}@${spacing}（${legs}肢），Aₛᵥ = ${Asv.toFixed(1)} mm²`, `配箍率 ρₛᵥ = ${rho.toFixed(4)}`, `箍筋项 Vₛᵥ = ${Vsv.toFixed(3)} kN`, `V꜀ₛ = V꜀ + Vₛᵥ = ${Vcs.toFixed(3)} kN`)
    if (rho < rhoMin) { status = 'insufficient'; message = `配箍率不足！ρ_sv=${rho.toFixed(4)} < ρ_sv,min=${rhoMin.toFixed(4)}` }
    else if (Vcs > Vmax) { status = 'over_limit'; message = `超出截面限制！V_cs=${Vcs.toFixed(3)} > V_max=${Vmax.toFixed(3)} kN` }
    else message = `满足规范要求，V_cs = ${Vcs.toFixed(3)} kN`
  } else {
    steps.push(`4. 未配置箍筋，V꜀ = ${Vc.toFixed(3)} kN`)
    if (Vc > Vmax) { status = 'over_limit'; message = 'V_c 超出截面限制，需增大截面' }
    else message = `混凝土项 V_c = ${Vc.toFixed(3)} kN, 截面限制 V_max = ${Vmax.toFixed(3)} kN`
  }
  return { data: { h0: roundTo(h0, 1), fc, ft, f_yv: fyv, beta_c: betaC, beta_h: betaH, V_c: roundTo(Vc), V_cs: roundTo(Vcs), V_max: roundTo(Vmax), A_sv: roundTo(Asv, 1), rho_sv: roundTo(rho, 4), rho_sv_min: roundTo(rhoMin, 4), status, message, steps }, message }
}
