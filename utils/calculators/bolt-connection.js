import { roundTo, requirePositive } from './common.js'

const FVB = { '4.6': 140, '4.8': 140, '5.6': 190, '8.8': 320 }
const FUB = { '4.6': 400, '4.8': 400, '5.6': 500, '8.8': 800, '10.9': 1000 }
const FCB = { Q235: 305, Q355: 385, Q390: 400, Q420: 425 }
const HOLE = { standard: 1, oversize: 0.85, slotted: 0.70 }
const PRETENSION = {
  '8.8': { 16: 80, 20: 125, 22: 150, 24: 175, 27: 230, 30: 280 },
  '10.9': { 16: 100, 20: 155, 22: 190, 24: 225, 27: 290, 30: 355 }
}

export function calculateBoltConnection(input) {
  const diameter = requirePositive(input.diameter, '螺栓直径')
  const count = Math.trunc(requirePositive(input.bolt_count, '螺栓数量'))
  const planes = Math.trunc(requirePositive(input.shear_planes ?? 1, '受剪面数'))
  const thickness = requirePositive(input.connected_thickness, '承压构件总厚度')
  const load = input.load === null || input.load === undefined || input.load === '' ? null : requirePositive(input.load, '设计剪力')
  const area = Math.PI * diameter ** 2 / 4
  let perBolt, control, details, steps

  if (input.bolt_type === 'ordinary') {
    const fvb = FVB[input.bolt_grade], fcb = FCB[input.steel_grade]
    if (!fvb || !fcb) throw new Error('不支持所选螺栓性能等级或钢材牌号')
    const shear = planes * area * fvb / 1000, bearing = diameter * thickness * fcb / 1000
    perBolt = Math.min(shear, bearing); control = shear <= bearing ? '抗剪承载力' : '承压承载力'
    details = { area: roundTo(area, 1), fvb, fcb, shear_capacity: roundTo(shear), bearing_capacity: roundTo(bearing) }
    steps = [`螺栓杆截面积 A = πd²/4 = ${area.toFixed(1)} mm²`, `单个螺栓抗剪承载力 Nᵛᵦ = ${shear.toFixed(3)} kN`, `单个螺栓承压承载力 Nᶜᵦ = ${bearing.toFixed(3)} kN`, `单个螺栓承载力 Nᵦ = min(Nᵛᵦ, Nᶜᵦ) = ${perBolt.toFixed(3)} kN`]
  } else if (input.bolt_type === 'high_strength') {
    const diameterKey = Math.trunc(diameter), table = PRETENSION[input.bolt_grade]
    if (diameter !== diameterKey || !table || !table[diameterKey]) throw new Error('高强螺栓仅支持 M16、M20、M22、M24、M27、M30 预拉力查表')
    const mu = Number(input.slip_coefficient), surfaces = Math.trunc(Number(input.friction_surfaces)), holeFactor = HOLE[input.hole_type]
    if (!(mu > 0 && mu <= 1) || surfaces < 1 || holeFactor === undefined) throw new Error('请检查高强螺栓等级、抗滑移系数、摩擦面数和孔型')
    const pretension = table[diameterKey]
    perBolt = 0.9 * holeFactor * surfaces * mu * pretension; control = '抗滑移承载力'
    details = { area: roundTo(area, 1), fub: FUB[input.bolt_grade], pretension: roundTo(pretension), hole_factor: holeFactor }
    steps = [`螺栓杆截面积 A = πd²/4 = ${area.toFixed(1)} mm²`, `查预拉力表：${input.bolt_grade} 级 M${diameterKey}，P = ${pretension.toFixed(3)} kN`, `单个螺栓抗滑移承载力 Nᵥᵦ = 0.9kₛn𝒻μP = ${perBolt.toFixed(3)} kN`]
  } else throw new Error('不支持的螺栓类型')

  const total = perBolt * count, utilization = load === null ? null : load / total
  steps.push(`连接承载力 Nᵤ = nNᵦ = ${count}×${perBolt.toFixed(3)} = ${total.toFixed(3)} kN`)
  if (utilization !== null) steps.push(`承载力利用率 η = V/Nᵤ = ${load.toFixed(3)}/${total.toFixed(3)} = ${utilization.toFixed(3)}`)
  return { data: { bolt_type: input.bolt_type, per_bolt_capacity: roundTo(perBolt), total_capacity: roundTo(total), control, utilization: utilization === null ? null : roundTo(utilization), passed: utilization === null ? null : utilization <= 1, details, steps }, message: '螺栓连接承载力计算完成' }
}
