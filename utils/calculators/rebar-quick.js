export const STANDARD_REBARS = Object.freeze([
  { diameter: 6, area: 28.27, unit_weight: 0.222 },
  { diameter: 8, area: 50.27, unit_weight: 0.395 },
  { diameter: 10, area: 78.54, unit_weight: 0.617 },
  { diameter: 12, area: 113.1, unit_weight: 0.888 },
  { diameter: 14, area: 153.9, unit_weight: 1.21 },
  { diameter: 16, area: 201.1, unit_weight: 1.58 },
  { diameter: 18, area: 254.5, unit_weight: 2.0 },
  { diameter: 20, area: 314.2, unit_weight: 2.47 },
  { diameter: 22, area: 380.1, unit_weight: 2.98 },
  { diameter: 25, area: 490.9, unit_weight: 3.85 },
  { diameter: 28, area: 615.8, unit_weight: 4.83 },
  { diameter: 32, area: 804.2, unit_weight: 6.31 },
  { diameter: 36, area: 1018, unit_weight: 7.99 },
  { diameter: 40, area: 1257, unit_weight: 9.87 },
  { diameter: 50, area: 1964, unit_weight: 15.42 }
])

const OPERATIONS = ['quantity', 'weight_to_length', 'spacing', 'equivalent']

function roundValue(value, digits = 3) {
  const factor = 10 ** digits
  return Math.round((value + 1e-10) * factor) / factor
}

function positive(value, label) {
  const number = Number(value)
  if (!Number.isFinite(number) || number <= 0) throw new Error(`请填写有效的${label}`)
  return number
}

function positiveInteger(value, label) {
  const number = positive(value, label)
  if (!Number.isInteger(number)) throw new Error(`${label}必须为正整数`)
  return number
}

function barByDiameter(value, label = '钢筋直径') {
  const diameter = positive(value, label)
  const bar = STANDARD_REBARS.find(item => item.diameter === diameter)
  if (!bar) throw new Error(`${label}应选择 GB 1499—2024 表2中的标准规格`)
  return bar
}

function baseResult(operation, bar) {
  return {
    operation,
    diameter: bar?.diameter ?? null,
    nominal_area: bar ? roundValue(bar.area, 1) : null,
    unit_weight: bar ? roundValue(bar.unit_weight, 3) : null,
    total_length: null,
    total_weight: null,
    weight_tonnes: null,
    bar_count: null,
    interval_count: null,
    actual_spacing: null,
    source_area: null,
    required_count: null,
    replacement_area: null,
    area_difference: null,
    area_change_percent: null,
    steps: [],
    status: 'ok'
  }
}

export function calculateRebarQuick(raw = {}) {
  const operation = raw.operation || 'quantity'
  if (!OPERATIONS.includes(operation)) throw new Error('请选择有效的钢筋速算类型')

  if (operation === 'equivalent') {
    const source = barByDiameter(raw.source_diameter, '原钢筋直径')
    const target = barByDiameter(raw.target_diameter, '替换钢筋直径')
    const sourceCount = positiveInteger(raw.source_count, '原钢筋根数')
    const sourceArea = source.area * sourceCount
    const requiredCount = Math.ceil(sourceArea / target.area - 1e-12)
    const replacementArea = target.area * requiredCount
    const difference = replacementArea - sourceArea
    const result = baseResult(operation, target)
    Object.assign(result, {
      bar_count: sourceCount,
      source_area: roundValue(sourceArea, 1),
      required_count: requiredCount,
      replacement_area: roundValue(replacementArea, 1),
      area_difference: roundValue(difference, 1),
      area_change_percent: roundValue(difference / sourceArea * 100, 3),
      steps: [
        `原配筋面积 Aₛ₁ = n₁·πd₁²/4 = ${sourceCount}×${source.area} = ${roundValue(sourceArea, 1)} mm²`,
        `理论替换根数 n₂ = Aₛ₁/Aₛ₂ = ${roundValue(sourceArea / target.area, 3)}`,
        `根数向上取整，采用 ${requiredCount} 根直径 ${target.diameter} mm 钢筋`,
        `替换后面积 Aₛ₂ = ${requiredCount}×${target.area} = ${roundValue(replacementArea, 1)} mm²`
      ]
    })
    return { data: result, message: '等面积代换计算完成' }
  }

  const bar = barByDiameter(raw.diameter)
  const result = baseResult(operation, bar)

  if (operation === 'quantity') {
    const barLength = positive(raw.bar_length, '单根长度')
    const count = positiveInteger(raw.bar_count, '钢筋根数')
    const totalLength = barLength * count
    const totalWeight = totalLength * bar.unit_weight
    Object.assign(result, {
      bar_count: count,
      total_length: roundValue(totalLength, 3),
      total_weight: roundValue(totalWeight, 3),
      weight_tonnes: roundValue(totalWeight / 1000, 3),
      steps: [
        `表2查得：直径 ${bar.diameter} mm 钢筋理论单位重量 m₀ = ${bar.unit_weight} kg/m`,
        `总长度 L = 单根长度×根数 = ${barLength}×${count} = ${roundValue(totalLength, 3)} m`,
        `总重量 G = m₀·L = ${bar.unit_weight}×${roundValue(totalLength, 3)} = ${roundValue(totalWeight, 3)} kg`
      ]
    })
    return { data: result, message: '钢筋用量计算完成' }
  }

  if (operation === 'weight_to_length') {
    const totalWeight = positive(raw.total_weight, '钢筋总重量')
    const totalLength = totalWeight / bar.unit_weight
    Object.assign(result, {
      total_length: roundValue(totalLength, 3),
      total_weight: roundValue(totalWeight, 3),
      weight_tonnes: roundValue(totalWeight / 1000, 3),
      steps: [
        `表2查得：直径 ${bar.diameter} mm 钢筋理论单位重量 m₀ = ${bar.unit_weight} kg/m`,
        `等效总长度 L = G/m₀ = ${totalWeight}/${bar.unit_weight} = ${roundValue(totalLength, 3)} m`
      ]
    })
    return { data: result, message: '钢筋重量反算完成' }
  }

  const layoutLength = positive(raw.layout_length, '布置长度')
  const maxSpacing = positive(raw.max_spacing, '最大间距')
  const barLength = positive(raw.bar_length, '单根钢筋长度')
  const intervalCount = Math.ceil(layoutLength / maxSpacing - 1e-12)
  const count = intervalCount + 1
  const actualSpacing = layoutLength / intervalCount
  const totalLength = barLength * count
  const totalWeight = totalLength * bar.unit_weight
  Object.assign(result, {
    bar_count: count,
    interval_count: intervalCount,
    actual_spacing: roundValue(actualSpacing, 3),
    total_length: roundValue(totalLength, 3),
    total_weight: roundValue(totalWeight, 3),
    weight_tonnes: roundValue(totalWeight / 1000, 3),
    steps: [
      `所需间隔数 nᵢ = ⌈L/sₘₐₓ⌉ = ⌈${layoutLength}/${maxSpacing}⌉ = ${intervalCount}`,
      `钢筋根数 n = nᵢ＋1 = ${count}`,
      `实际均布间距 s = L/nᵢ = ${layoutLength}/${intervalCount} = ${roundValue(actualSpacing, 3)} mm`,
      `总重量 G = ${count}×${barLength}×${bar.unit_weight} = ${roundValue(totalWeight, 3)} kg`
    ]
  })
  return { data: result, message: '钢筋间距与根数计算完成' }
}
