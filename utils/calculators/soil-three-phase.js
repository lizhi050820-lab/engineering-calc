import { has, roundTo } from './common.js'

const KEYS = ['Gs','w','gamma','gamma_d','gamma_sat','gamma_prime','e','n','Sr','rho','rho_d','rho_sat']

function add(vals, derivations, key, value, formula, unit = '') {
  if (has(vals, key) || !Number.isFinite(value)) return false
  vals[key] = value
  derivations.push({ symbol:key, value, formula, unit })
  return true
}

function solve(known, gammaW, g) {
  const vals = { ...known }
  const derivations = []
  let changed = true

  for (let iteration=0; changed && iteration<20; iteration++) {
    changed = false
    if (has(vals,'rho') && !has(vals,'gamma')) changed = add(vals,derivations,'gamma',vals.rho*g,'γ = ρ·g','kN/m³') || changed
    if (!has(vals,'rho') && has(vals,'gamma')) changed = add(vals,derivations,'rho',vals.gamma/g,'ρ = γ/g','g/cm³') || changed
    if (has(vals,'rho_d') && !has(vals,'gamma_d')) changed = add(vals,derivations,'gamma_d',vals.rho_d*g,'γ_d = ρ_d·g','kN/m³') || changed
    if (!has(vals,'rho_d') && has(vals,'gamma_d')) changed = add(vals,derivations,'rho_d',vals.gamma_d/g,'ρ_d = γ_d/g','g/cm³') || changed
    if (has(vals,'rho_sat') && !has(vals,'gamma_sat')) changed = add(vals,derivations,'gamma_sat',vals.rho_sat*g,'γ_sat = ρ_sat·g','kN/m³') || changed
    if (!has(vals,'rho_sat') && has(vals,'gamma_sat')) changed = add(vals,derivations,'rho_sat',vals.gamma_sat/g,'ρ_sat = γ_sat/g','g/cm³') || changed

    if (has(vals,'gamma') && has(vals,'w') && !has(vals,'gamma_d')) {
      changed = add(vals,derivations,'gamma_d',vals.gamma/(1+vals.w),`γ_d = γ/(1+w) = ${vals.gamma.toFixed(2)}/(1+${vals.w.toFixed(4)})`,'kN/m³') || changed
    }
    if (has(vals,'gamma_d') && has(vals,'w') && !has(vals,'gamma')) {
      changed = add(vals,derivations,'gamma',vals.gamma_d*(1+vals.w),`γ = γ_d·(1+w) = ${vals.gamma_d.toFixed(2)}×(1+${vals.w.toFixed(4)})`,'kN/m³') || changed
    }
    if (has(vals,'Gs') && has(vals,'e') && !has(vals,'gamma_d')) {
      changed = add(vals,derivations,'gamma_d',vals.Gs*gammaW/(1+vals.e),`γ_d = G_s·γ_w/(1+e) = ${vals.Gs.toFixed(2)}×${gammaW}/(1+${vals.e.toFixed(4)})`,'kN/m³') || changed
    }
    if (has(vals,'Gs') && has(vals,'gamma_d') && !has(vals,'e')) {
      const e = vals.Gs*gammaW/vals.gamma_d-1
      if (e>=0) changed = add(vals,derivations,'e',e,`e = G_s·γ_w/γ_d-1 = ${vals.Gs.toFixed(2)}×${gammaW}/${vals.gamma_d.toFixed(2)}-1`) || changed
    }
    if (has(vals,'e') && !has(vals,'n')) changed = add(vals,derivations,'n',vals.e/(1+vals.e),`n = e/(1+e) = ${vals.e.toFixed(4)}/(1+${vals.e.toFixed(4)})`) || changed
    if (has(vals,'n') && !has(vals,'e') && vals.n<1) changed = add(vals,derivations,'e',vals.n/(1-vals.n),`e = n/(1-n) = ${vals.n.toFixed(4)}/(1-${vals.n.toFixed(4)})`) || changed

    if (has(vals,'w') && has(vals,'Gs') && has(vals,'e') && !has(vals,'Sr') && vals.e!==0) {
      changed = add(vals,derivations,'Sr',vals.w*vals.Gs/vals.e,`S_r = w·G_s/e = ${vals.w.toFixed(4)}×${vals.Gs.toFixed(2)}/${vals.e.toFixed(4)}`) || changed
    }
    if (has(vals,'Sr') && has(vals,'Gs') && has(vals,'e') && !has(vals,'w')) changed = add(vals,derivations,'w',vals.Sr*vals.e/vals.Gs,`w = S_r·e/G_s`) || changed
    if (has(vals,'w') && has(vals,'Gs') && has(vals,'Sr') && !has(vals,'e') && vals.Sr>0) changed = add(vals,derivations,'e',vals.w*vals.Gs/vals.Sr,`e = w·G_s/S_r`) || changed

    if (has(vals,'Gs') && has(vals,'e') && !has(vals,'gamma_sat')) {
      changed = add(vals,derivations,'gamma_sat',(vals.Gs+vals.e)*gammaW/(1+vals.e),`γ_sat = (G_s+e)·γ_w/(1+e)`,'kN/m³') || changed
    }
    if (has(vals,'gamma_sat') && !has(vals,'gamma_prime')) changed = add(vals,derivations,'gamma_prime',vals.gamma_sat-gammaW,`γ′ = γ_sat-γ_w = ${vals.gamma_sat.toFixed(2)}-${gammaW}`,'kN/m³') || changed
    if (has(vals,'gamma_prime') && !has(vals,'gamma_sat')) changed = add(vals,derivations,'gamma_sat',vals.gamma_prime+gammaW,`γ_sat = γ′+γ_w`,'kN/m³') || changed
    if (has(vals,'Gs') && has(vals,'w') && has(vals,'e') && !has(vals,'gamma')) changed = add(vals,derivations,'gamma',vals.Gs*gammaW*(1+vals.w)/(1+vals.e),`γ = G_s·γ_w·(1+w)/(1+e)`,'kN/m³') || changed
  }
  return { vals, derivations }
}

export function calculateSoilThreePhase(input = {}) {
  const gammaW = input.gamma_w == null ? 9.81 : Number(input.gamma_w)
  const g = input.g == null ? 9.81 : Number(input.g)
  const known = {}
  for (const key of KEYS) if (input[key] !== null && input[key] !== undefined && input[key] !== '') known[key] = Number(input[key])
  if (Object.keys(known).length < 2) throw new Error(`至少需要输入 2-3 个已知指标才能推导其余量，当前仅输入了 ${Object.keys(known).length} 个`)
  if (!has(known,'Gs')) throw new Error('土粒比重 G_s 是核心参数，必须提供')
  if (has(known,'Sr') && (known.Sr<0 || known.Sr>1)) throw new Error('饱和度 S_r 应在 0～1 之间')
  if (has(known,'n') && (known.n<=0 || known.n>=1)) throw new Error('孔隙率 n 应在 0～1 之间')
  if (has(known,'w') && known.w>1.5) throw new Error('含水量 w 异常偏高，请确认百分数已换算为小数')

  const { vals, derivations } = solve(known,gammaW,g)
  if (has(vals,'Sr') && (vals.Sr<0 || vals.Sr>1)) throw new Error(`推导得到的饱和度 S_r=${vals.Sr.toFixed(4)} 超出 0～1，请检查已知参数是否相容`)
  if (has(vals,'n') && (vals.n<=0 || vals.n>=1)) throw new Error(`推导得到的孔隙率 n=${vals.n.toFixed(4)} 超出 0～1，请检查已知参数是否相容`)
  if (has(vals,'e') && vals.e<0) throw new Error('推导得到的孔隙比 e 小于 0，请检查已知参数是否相容')

  const data = { gamma_w:gammaW }
  for (const key of KEYS) data[key] = has(vals,key) ? roundTo(vals[key],4) : null
  data.derivations = derivations.map(d => ({...d,value:roundTo(d.value,4)}))
  data.missing = KEYS.filter(key => data[key] == null)
  const message = data.missing.length ? `推导完成，${data.missing.length} 个指标无法确定: ${data.missing.join(', ')}` : '三相指标全部推导完成 ✓'
  return { data, message }
}
