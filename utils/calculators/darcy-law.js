import { has, roundTo } from './common.js'

const KEYS = ['k','i','delta_h','L','Q','v','A','t','a','h1','h2','j','J','V','i_cr','gamma_prime','Gs','e','Fs']

function add(vals, derivations, key, value, formula, unit='') {
  if (has(vals,key) || !Number.isFinite(value)) return false
  vals[key]=value
  derivations.push({symbol:key,value,formula,unit})
  return true
}

function solve(known,gammaW) {
  const vals={...known}, derivations=[]
  let changed=true
  for(let iteration=0;changed&&iteration<30;iteration++){
    changed=false
    if(has(vals,'delta_h')&&has(vals,'L')&&!has(vals,'i')&&vals.L>0) changed=add(vals,derivations,'i',vals.delta_h/vals.L,`i = Δh/L = ${vals.delta_h.toFixed(4)}/${vals.L.toFixed(4)}`)||changed
    if(has(vals,'i')&&has(vals,'L')&&!has(vals,'delta_h')) changed=add(vals,derivations,'delta_h',vals.i*vals.L,`Δh = i·L`,'m')||changed
    if(has(vals,'i')&&has(vals,'delta_h')&&!has(vals,'L')&&vals.i>0) changed=add(vals,derivations,'L',vals.delta_h/vals.i,`L = Δh/i`,'m')||changed

    if(has(vals,'k')&&has(vals,'i')&&!has(vals,'v')) changed=add(vals,derivations,'v',vals.k*vals.i,`v = k·i = ${vals.k.toFixed(6)}×${vals.i.toFixed(4)}`,'m/s')||changed
    if(has(vals,'v')&&has(vals,'i')&&!has(vals,'k')&&vals.i>0) changed=add(vals,derivations,'k',vals.v/vals.i,'k = v/i','m/s')||changed
    if(has(vals,'v')&&has(vals,'k')&&!has(vals,'i')&&vals.k>0) changed=add(vals,derivations,'i',vals.v/vals.k,'i = v/k')||changed

    const constantHead=['Q','L','A','delta_h','t'].every(k=>has(vals,k))
    if(!constantHead&&has(vals,'v')&&has(vals,'A')&&!has(vals,'Q')) changed=add(vals,derivations,'Q',vals.v*vals.A,`Q = v·A = ${vals.v.toFixed(6)}×${vals.A.toFixed(4)}`,'m³/s')||changed
    if(!constantHead&&has(vals,'Q')&&has(vals,'A')&&!has(vals,'v')&&vals.A>0) changed=add(vals,derivations,'v',vals.Q/vals.A,'v = Q/A','m/s')||changed
    if(!constantHead&&has(vals,'Q')&&has(vals,'v')&&!has(vals,'A')&&vals.v>0) changed=add(vals,derivations,'A',vals.Q/vals.v,'A = Q/v','m²')||changed

    if(has(vals,'k')&&has(vals,'i')&&has(vals,'A')&&has(vals,'t')&&!has(vals,'Q')) changed=add(vals,derivations,'Q',vals.k*vals.i*vals.A*vals.t,'Q = k·i·A·t','m³')||changed
    if(['Q','L','A','delta_h','t'].every(k=>has(vals,k))&&!has(vals,'k')){
      const denominator=vals.A*vals.delta_h*vals.t
      if(denominator>0) changed=add(vals,derivations,'k',vals.Q*vals.L/denominator,`k = Q·L/(A·Δh·t)`,'m/s')||changed
    }
    if(['a','L','A','t','h1','h2'].every(k=>has(vals,k))&&!has(vals,'k')&&vals.A>0&&vals.t>0&&vals.h2>0){
      const ratio=vals.h1/vals.h2
      if(ratio>1) changed=add(vals,derivations,'k',(vals.a*1e-4*vals.L)/(vals.A*vals.t)*Math.log(ratio),'k = (a×10⁻⁴)·L/(A·t)·ln(h₁/h₂)','m/s')||changed
    }

    if(has(vals,'i')&&!has(vals,'j')) changed=add(vals,derivations,'j',gammaW*vals.i,`j = γ_w·i = ${gammaW}×${vals.i.toFixed(4)}`,'kN/m³')||changed
    if(has(vals,'j')&&!has(vals,'i')&&gammaW>0) changed=add(vals,derivations,'i',vals.j/gammaW,'i = j/γ_w')||changed
    if(has(vals,'j')&&has(vals,'V')&&!has(vals,'J')) changed=add(vals,derivations,'J',vals.j*vals.V,'J = j·V','kN')||changed
    if(has(vals,'J')&&has(vals,'V')&&!has(vals,'j')&&vals.V>0) changed=add(vals,derivations,'j',vals.J/vals.V,'j = J/V','kN/m³')||changed
    if(has(vals,'J')&&has(vals,'j')&&!has(vals,'V')&&vals.j>0) changed=add(vals,derivations,'V',vals.J/vals.j,'V = J/j','m³')||changed

    if(has(vals,'gamma_prime')&&!has(vals,'i_cr')) changed=add(vals,derivations,'i_cr',vals.gamma_prime/gammaW,'i_cr = γ′/γ_w')||changed
    if(has(vals,'i_cr')&&!has(vals,'gamma_prime')) changed=add(vals,derivations,'gamma_prime',vals.i_cr*gammaW,'γ′ = i_cr·γ_w','kN/m³')||changed
    if(has(vals,'Gs')&&has(vals,'e')&&!has(vals,'i_cr')) changed=add(vals,derivations,'i_cr',(vals.Gs-1)/(1+vals.e),'i_cr = (G_s-1)/(1+e)')||changed
    if(has(vals,'i_cr')&&has(vals,'e')&&!has(vals,'Gs')) changed=add(vals,derivations,'Gs',vals.i_cr*(1+vals.e)+1,'G_s = i_cr·(1+e)+1')||changed
    if(has(vals,'Gs')&&has(vals,'i_cr')&&!has(vals,'e')&&vals.i_cr>0){const e=(vals.Gs-1)/vals.i_cr-1;if(e>=0)changed=add(vals,derivations,'e',e,'e = (G_s-1)/i_cr-1')||changed}
    if(has(vals,'i_cr')&&has(vals,'i')&&!has(vals,'Fs')&&vals.i>0) changed=add(vals,derivations,'Fs',vals.i_cr/vals.i,'F_s = i_cr/i')||changed
    if(has(vals,'Fs')&&has(vals,'i')&&!has(vals,'i_cr')) changed=add(vals,derivations,'i_cr',vals.Fs*vals.i,'i_cr = F_s·i')||changed
    if(has(vals,'i_cr')&&has(vals,'Fs')&&!has(vals,'i')&&vals.Fs>0) changed=add(vals,derivations,'i',vals.i_cr/vals.Fs,'i = i_cr/F_s')||changed
    if(has(vals,'i')&&has(vals,'V')&&!has(vals,'J')) changed=add(vals,derivations,'J',gammaW*vals.i*vals.V,'J = γ_w·i·V','kN')||changed
  }
  return {vals,derivations}
}

export function calculateDarcyLaw(input={}){
  const gammaW=input.gamma_w==null?9.81:Number(input.gamma_w)
  const known={}
  for(const key of KEYS) if(input[key]!==null&&input[key]!==undefined&&input[key]!=='') known[key]=Number(input[key])
  if(Object.keys(known).length<2) throw new Error(`至少需要输入 2 个已知参数，当前仅 ${Object.keys(known).length} 个`)
  if(has(known,'h1')&&has(known,'h2')&&known.h1<=known.h2) throw new Error('变水头试验应满足初始水头 h₁ > 终止水头 h₂')
  const {vals,derivations}=solve(known,gammaW)
  const data={gamma_w:gammaW}
  for(const key of KEYS){
    if(!has(vals,key)) data[key]=null
    else data[key]=roundTo(vals[key],['k','v','Q'].includes(key)?12:['i','e','Fs','i_cr'].includes(key)?4:6)
  }
  data.derivations=derivations.map(d=>({...d,value:roundTo(d.value,['k','v','Q'].includes(d.symbol)?12:4)}))
  data.missing=KEYS.filter(key=>data[key]==null)
  data.quicksand_risk=null
  if(data.i!=null&&data.i_cr!=null) data.quicksand_risk=data.i>=data.i_cr?'danger':data.i>=.8*data.i_cr?'warning':'safe'
  const message=data.missing.length?`推导完成，${data.missing.length} 个未知参数无法确定`:'达西定律相关参数全部推导完成'
  return {data,message}
}
