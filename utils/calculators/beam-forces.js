import { roundTo, requirePositive } from './common.js'

function legacyLoads(input,total){
  const P=()=>requirePositive(input.P,'集中力 P'), q=()=>requirePositive(input.q,'均布荷载 q')
  const map={
    mid_point:()=>[{type:'point',value:P(),x:input.L/2}],
    point:()=>[{type:'point',value:P(),x:requirePositive(input.a,'荷载位置 a')}],
    uniform:()=>[{type:'udl',value:q(),x1:0,x2:input.L}],
    end_point:()=>[{type:'point',value:P(),x:input.L}],
    end_moment:()=>[{type:'moment',value:requirePositive(input.M,'集中弯矩 M'),x:input.L,direction:'clockwise'}],
    overhang_end_point:()=>[{type:'point',value:P(),x:total}],
    main_uniform:()=>[{type:'udl',value:q(),x1:0,x2:input.L}],
  }
  if(!map[input.load_type]) throw new Error('请至少添加一项荷载')
  return map[input.load_type]()
}

function normaliseLoads(input,total){
  const raw=input.loads?.length?input.loads:legacyLoads(input,total)
  if(raw.length>20) throw new Error('单次最多添加 20 项荷载')
  return raw.map((item,index)=>{
    const value=requirePositive(item.value,`第 ${index+1} 项荷载值`)
    if(item.type==='point'||item.type==='moment'){
      const x=Number(item.x)
      if(!Number.isFinite(x)||x<0||x>total) throw new Error(`第 ${index+1} 项荷载位置 x 应满足 0 ≤ x ≤ ${total.toFixed(3)} m`)
      if(item.type==='moment'&&!['clockwise','counterclockwise'].includes(item.direction)) throw new Error(`请选择第 ${index+1} 项集中弯矩的方向`)
      return {type:item.type,value,x,direction:item.direction}
    }
    if(item.type==='udl'){
      const x1=Number(item.x1),x2=Number(item.x2)
      if(!Number.isFinite(x1)||!Number.isFinite(x2)||x1<0||x1>=x2||x2>total) throw new Error(`第 ${index+1} 项均布荷载范围应满足 0 ≤ x₁ < x₂ ≤ ${total.toFixed(3)} m`)
      return {type:'udl',value,x1,x2}
    }
    throw new Error(`第 ${index+1} 项荷载类型不受支持`)
  })
}

const couple=load=>load.direction==='counterclockwise'?load.value:-load.value
const included=(x,position,side)=>x>position||(x===position&&side==='right')

export function calculateBeamForces(input={}){
  const L=requirePositive(input.L,'梁长 L')
  if(!['simply_supported','cantilever','overhanging'].includes(input.beam_type)) throw new Error('不支持的梁型')
  let total,supportA,supportB=null,fixedX=null
  if(input.beam_type==='overhanging'){
    const c=requirePositive(input.c,'右外伸长度 c');total=L+c;supportA=0;supportB=L
  }else if(input.beam_type==='simply_supported'){
    total=L;supportA=input.support_a==null?0:Number(input.support_a);supportB=input.support_b==null?L:Number(input.support_b)
    if(!(supportA>=0&&supportA<supportB&&supportB<=total)) throw new Error(`两支座位置应满足 0 ≤ xA < xB ≤ ${total.toFixed(3)} m`)
  }else{
    total=L
    const fixedEnd=input.fixed_end||'left'
    if(!['left','right'].includes(fixedEnd)) throw new Error('固定端只能选择左端或右端')
    fixedX=fixedEnd==='left'?0:total;supportA=fixedX
  }
  const loads=normaliseLoads(input,total)
  const points=loads.filter(x=>x.type==='point'),udls=loads.filter(x=>x.type==='udl'),moments=loads.filter(x=>x.type==='moment')
  let vertical=points.reduce((s,x)=>s+x.value,0)
  let verticalMoment=points.reduce((s,x)=>s+x.value*x.x,0)
  for(const load of udls){const W=load.value*(load.x2-load.x1),xc=(load.x1+load.x2)/2;vertical+=W;verticalMoment+=W*xc}
  const coupleTotal=moments.reduce((s,x)=>s+couple(x),0)
  let RA=vertical,RB=null,fixedMoment=null
  if(input.beam_type==='cantilever') fixedMoment=verticalMoment-vertical*fixedX-coupleTotal
  else {RB=(verticalMoment-vertical*supportA-coupleTotal)/(supportB-supportA);RA=vertical-RB}

  const shearAt=(x,side='right')=>{
    let value=0
    if(included(x,supportA,side))value+=RA
    if(RB!=null&&included(x,supportB,side))value+=RB
    for(const load of points)if(included(x,load.x,side))value-=load.value
    for(const load of udls)value-=load.value*Math.min(Math.max(x-load.x1,0),load.x2-load.x1)
    return value
  }
  const momentAt=(x,side='right')=>{
    let value=0
    if(fixedMoment!=null&&included(x,fixedX,side))value-=fixedMoment
    if(x>supportA)value+=RA*(x-supportA)
    if(RB!=null&&x>supportB)value+=RB*(x-supportB)
    for(const load of points)if(x>load.x)value-=load.value*(x-load.x)
    for(const load of udls){const len=Math.min(Math.max(x-load.x1,0),load.x2-load.x1);if(len>0){const xc=load.x1+len/2;value-=load.value*len*(x-xc)}}
    for(const load of moments)if(included(x,load.x,side))value-=couple(load)
    return value
  }

  const breaks=new Set([0,total,supportA]);if(supportB!=null)breaks.add(supportB)
  for(const load of [...points,...moments])breaks.add(load.x)
  for(const load of udls){breaks.add(load.x1);breaks.add(load.x2)}
  const ordered=[...breaks].sort((a,b)=>a-b),critical=new Set(ordered)
  for(let i=0;i<ordered.length-1;i++){
    const left=ordered[i],right=ordered[i+1],mid=(left+right)/2
    const activeQ=udls.filter(x=>x.x1<mid&&mid<x.x2).reduce((s,x)=>s+x.value,0)
    if(activeQ>0){const root=mid+shearAt(mid)/activeQ;if(left<root&&root<right)critical.add(root)}
  }
  const momentsAt=[],shears=[]
  for(const x of [...critical].sort((a,b)=>a-b)){
    momentsAt.push([momentAt(x,'left'),x],[momentAt(x,'right'),x]);shears.push(shearAt(x,'left'),shearAt(x,'right'))
  }
  const positive=momentsAt.reduce((a,b)=>b[0]>a[0]?b:a),negative=momentsAt.reduce((a,b)=>b[0]<a[0]?b:a),absolute=momentsAt.reduce((a,b)=>Math.abs(b[0])>Math.abs(a[0])?b:a)
  const vmax=Math.max(...shears.map(Math.abs))
  const steps=['=== 多荷载静定梁内力计算 ===',`梁长范围：0～${total.toFixed(3)} m；共 ${loads.length} 项荷载。`]
  if(RB!=null){steps.push(`支座位置：A 点 xA = ${supportA.toFixed(3)} m，B 点 xB = ${supportB.toFixed(3)} m；支座间距 s = ${(supportB-supportA).toFixed(3)} m。`)}
  else steps.push(`固定端位于${fixedX===0?'左端':'右端'} x = ${fixedX.toFixed(3)} m。`)
  loads.forEach((load,index)=>{
    if(load.type==='point')steps.push(`荷载 ${index+1}：集中力 P = ${load.value.toFixed(3)} kN，位置 x = ${load.x.toFixed(3)} m。`)
    else if(load.type==='udl')steps.push(`荷载 ${index+1}：均布荷载 q = ${load.value.toFixed(3)} kN/m，范围 ${load.x1.toFixed(3)}～${load.x2.toFixed(3)} m。`)
    else steps.push(`荷载 ${index+1}：集中弯矩 M = ${load.value.toFixed(3)} kN·m（${load.direction==='clockwise'?'顺时针':'逆时针'}），位置 x = ${load.x.toFixed(3)} m。`)
  })
  if(RB!=null)steps.push(`由整体平衡得 RA = ${RA.toFixed(3)} kN，RB = ${RB.toFixed(3)} kN。`)
  else steps.push(`由整体平衡得 RF = ${RA.toFixed(3)} kN，MF = ${fixedMoment.toFixed(3)} kN·m。`)
  steps.push('按叠加原理建立 V(x) 与 M(x)，并检查所有荷载边界、支座位置及 V(x)=0 的区间点。',`最大正弯矩 M⁺max = ${positive[0].toFixed(3)} kN·m，x = ${positive[1].toFixed(3)} m。`,`最大负弯矩 M⁻min = ${negative[0].toFixed(3)} kN·m，x = ${negative[1].toFixed(3)} m。`,`最大绝对剪力 |V|max = ${vmax.toFixed(3)} kN；最大绝对弯矩 |M|max = ${Math.abs(absolute[0]).toFixed(3)} kN·m。`)

  const sample=new Set([...critical]);for(let i=0;i<=40;i++)sample.add(total*i/40)
  const data={
    beam_type:input.beam_type,load_type:input.loads?.length?'combined':input.load_type,L:roundTo(L),RA:roundTo(RA),RB:RB==null?null:roundTo(RB),fixed_moment:fixedMoment==null?null:roundTo(fixedMoment),
    Vmax:roundTo(vmax),Mmax:roundTo(Math.abs(absolute[0])),x_Mmax:roundTo(absolute[1]),M_positive:roundTo(positive[0]),x_M_positive:roundTo(positive[1]),M_negative:roundTo(negative[0]),x_M_negative:roundTo(negative[1]),
    key_values:{total_length:roundTo(total),load_count:loads.length,support_a:roundTo(supportA),support_b:supportB==null?null:roundTo(supportB),fixed_end:fixedX==null?null:fixedX===0?'left':'right'},
    diagram:{beam:{length:roundTo(total),support_a:roundTo(supportA),support_b:supportB==null?null:roundTo(supportB)},loads,reactions:{RA:roundTo(RA),RB:RB==null?null:roundTo(RB)},shear:[...sample].sort((a,b)=>a-b).map(x=>({x:roundTo(x),V:roundTo(shearAt(x))})),moment:[...sample].sort((a,b)=>a-b).map(x=>({x:roundTo(x),M:roundTo(momentAt(x))}))},
    steps,status:'ok'
  }
  return {data,message:'多荷载梁内力计算完成'}
}
