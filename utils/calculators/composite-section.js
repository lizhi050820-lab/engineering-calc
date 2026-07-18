import { roundTo } from './common.js'

export function calculateCompositeSection(input) {
  const blocks = Array.isArray(input.blocks) ? input.blocks.map((raw, index) => {
    const block = {
      b: Number(raw.b), h: Number(raw.h), y0: Number(raw.y0), x0: Number(raw.x0 ?? 0),
      is_hole: Boolean(raw.is_hole), label: raw.label || `矩形${index + 1}`
    }
    if (![block.b, block.h, block.y0, block.x0].every(Number.isFinite) || block.b <= 0 || block.h <= 0) {
      throw new Error(`分块${index + 1}的宽度、高度和坐标无效`)
    }
    return block
  }) : []
  if (!blocks.length) throw new Error('请至少添加一个分块')
  const solids = blocks.filter(block => !block.is_hole)
  if (!solids.length) throw new Error('至少需要一个实体分块（非孔洞）')

  const signedAreas = blocks.map(block => (block.is_hole ? -1 : 1) * block.b * block.h)
  const yCenters = blocks.map(block => block.y0 + block.h / 2)
  const xCenters = blocks.map(block => block.x0 + block.b / 2)
  const totalArea = signedAreas.reduce((sum, area) => sum + area, 0)
  if (totalArea <= 0) throw new Error(`净面积必须大于0，当前净面积 A = ${totalArea.toFixed(1)} mm²（孔洞太大）`)
  const yMoment = signedAreas.reduce((sum, area, i) => sum + area * yCenters[i], 0)
  const xMoment = signedAreas.reduce((sum, area, i) => sum + area * xCenters[i], 0)
  const yBar = yMoment / totalArea, xBar = xMoment / totalArea

  const steps = ['=== 组合截面几何性质计算（平行移轴公式） ===', `分块数量: ${blocks.length}（实体 ${solids.length} + 孔洞 ${blocks.length - solids.length}）`, '', '--- 第1步：求组合截面形心 ---']
  blocks.forEach((block, i) => steps.push(`分块${i + 1}[${block.label}]: A = ${Math.abs(signedAreas[i]).toFixed(0)} mm²${block.is_hole ? '（孔洞，负面积）' : ''}，形心 y_ci = ${yCenters[i].toFixed(1)} mm`))
  steps.push(`总面积 A = ${totalArea.toFixed(1)} mm²`, `形心 ȳ = Σ(Aᵢ·y_ci)/ΣAᵢ = ${yBar.toFixed(1)} mm`, `形心 x̄ = Σ(Aᵢ·x_ci)/ΣAᵢ = ${xBar.toFixed(1)} mm`, '', '--- 第2步：平行移轴公式 I_z = I_zc + A·d² ---')

  let Iz = 0, Iy = 0, yMax = -Infinity, yMin = Infinity, xMax = -Infinity, xMin = Infinity
  const details = blocks.map((block, i) => {
    const area = block.b * block.h, sign = block.is_hole ? -1 : 1
    const Izc = block.b * block.h ** 3 / 12, Iyc = block.h * block.b ** 3 / 12
    const dy = yCenters[i] - yBar, dx = xCenters[i] - xBar
    const Ady2 = area * dy ** 2, Adx2 = area * dx ** 2
    const IzContribution = sign * (Izc + Ady2)
    Iz += IzContribution; Iy += sign * (Iyc + Adx2)
    yMax = Math.max(yMax, block.y0 + block.h); yMin = Math.min(yMin, block.y0)
    xMax = Math.max(xMax, block.x0 + block.b); xMin = Math.min(xMin, block.x0)
    steps.push(`[${block.label}] I_zc = ${Izc.toFixed(0)} mm⁴，d_y = ${dy.toFixed(1)} mm，A·d_y² = ${Ady2.toFixed(0)} mm⁴`, `I_z贡献 = ${IzContribution.toFixed(0)} mm⁴${block.is_hole ? '（孔洞扣除）' : ''}`)
    return { label: block.label, b: block.b, h: block.h, y0: block.y0, A: sign * area, y_ci: yCenters[i], d_y: roundTo(dy, 1), I_zc: roundTo(Izc, 0), Ady2: roundTo(Ady2, 0), I_z_contrib: roundTo(IzContribution, 0), is_hole: block.is_hole }
  })

  const yTop = yMax - yBar, yBottom = yBar - yMin
  const WzTop = yTop > 0 ? Iz / yTop : 0, WzBottom = yBottom > 0 ? Iz / yBottom : 0
  const sideDistance = Math.max(xMax - xBar, xBar - xMin), Wy = sideDistance > 0 ? Iy / sideDistance : 0
  const iz = Math.sqrt(Math.abs(Iz) / totalArea), iy = Math.sqrt(Math.abs(Iy) / totalArea)
  let Sz = 0
  blocks.forEach(block => {
    const sign = block.is_hole ? -1 : 1, top = block.y0 + block.h, bottom = block.y0
    if (bottom >= yBar) Sz += sign * block.b * block.h * (bottom + block.h / 2 - yBar)
    else if (top > yBar) { const above = top - yBar; Sz += sign * block.b * above * above / 2 }
  })
  Sz = Math.abs(Sz)
  steps.push('--- 第3步：求和 ---', `I_z = ${Iz.toFixed(0)} mm⁴`, `I_y = ${Iy.toFixed(0)} mm⁴`, '--- 截面特性汇总 ---', `形心距底边 ȳ = ${yBar.toFixed(1)} mm`, `抵抗矩 W_z,top = ${WzTop.toFixed(0)} mm³`, `回转半径 i_z = ${iz.toFixed(1)} mm`, `面积矩 S_z = ${Sz.toFixed(0)} mm³`)

  return {
    data: {
      shape: 'composite', n_blocks: blocks.length, n_holes: blocks.length - solids.length,
      A: roundTo(totalArea, 1), y_bar: roundTo(yBar, 1), x_bar: roundTo(xBar, 1),
      I_z: roundTo(Iz, 0), I_y: roundTo(Iy, 0), W_z_top: roundTo(WzTop, 0),
      W_z_bot: roundTo(WzBottom, 0), W_y: roundTo(Wy, 0), i_z: roundTo(iz, 1),
      i_y: roundTo(iy, 1), S_z: roundTo(Sz, 0), y_max: yMax, y_min: yMin,
      block_details: details, steps, status: 'ok'
    },
    message: `组合截面计算完成（${blocks.length}个分块，形心距底边 ${roundTo(yBar, 1).toFixed(1)} mm）`
  }
}
