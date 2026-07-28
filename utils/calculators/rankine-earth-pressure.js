import { roundTo, requirePositive } from './common.js'

const MODES = ['active', 'passive', 'at_rest']
const WATER_METHODS = ['separate', 'combined']

const coefficient = (mode, phi) => {
  const radians = phi * Math.PI / 180
  if (mode === 'active') return Math.tan(Math.PI / 4 - radians / 2) ** 2
  if (mode === 'passive') return Math.tan(Math.PI / 4 + radians / 2) ** 2
  return 1 - Math.sin(radians)
}

function normalize(raw = {}) {
  const mode = raw.mode || 'active'
  if (!MODES.includes(mode)) throw new Error('土压力类型必须为主动、被动或静止')
  const waterMethod = raw.water_method || 'separate'
  if (!WATER_METHODS.includes(waterMethod)) throw new Error('地下水算法必须为水土分算或水土合算')
  if (!Array.isArray(raw.layers) || raw.layers.length < 1 || raw.layers.length > 8) {
    throw new Error('请设置 1～8 层土')
  }
  const layers = raw.layers.map((item, index) => {
    const h = requirePositive(item.h, `第${index + 1}层厚度 h`)
    const gamma = requirePositive(item.gamma, `第${index + 1}层天然重度 γ`)
    const phi = Number(item.phi)
    const c = Number(item.c ?? 0)
    if (!Number.isFinite(phi) || phi < 0 || phi >= 45) throw new Error(`第${index + 1}层内摩擦角 φ 应在 0～45° 之间`)
    if (!Number.isFinite(c) || c < 0) throw new Error(`第${index + 1}层黏聚力 c 不能小于 0`)
    const gammaSat = item.gamma_sat === '' || item.gamma_sat === null || item.gamma_sat === undefined
      ? gamma : requirePositive(item.gamma_sat, `第${index + 1}层饱和重度 γsat`)
    return { h, gamma, gamma_sat: gammaSat, phi, c }
  })
  const H = layers.reduce((sum, item) => sum + item.h, 0)
  const q = Number(raw.q ?? 0)
  const gammaW = requirePositive(raw.gamma_w ?? 9.81, '水的重度 γw')
  if (!Number.isFinite(q) || q < 0) throw new Error('地面均布荷载 q 不能小于 0')
  const hasWater = raw.water_table !== null && raw.water_table !== undefined && raw.water_table !== ''
  const waterTable = hasWater ? Number(raw.water_table) : null
  if (hasWater && (!Number.isFinite(waterTable) || waterTable < 0 || waterTable > H)) {
    throw new Error(`地下水位深度应在 0～${H.toFixed(3)} m 之间`)
  }
  if (hasWater) {
    layers.forEach((item, index) => {
      if (item.gamma_sat <= gammaW) throw new Error(`第${index + 1}层饱和重度必须大于水的重度`)
    })
  }
  return { mode, water_method: waterMethod, layers, q, gamma_w: gammaW, water_table: waterTable, H }
}

function calculateVerticalStress(input, depth) {
  let stress = input.q
  let top = 0
  for (const layer of input.layers) {
    const bottom = top + layer.h
    const length = Math.max(0, Math.min(depth, bottom) - top)
    if (length > 0) {
      if (input.water_table === null) stress += layer.gamma * length
      else {
        const above = Math.max(0, Math.min(depth, bottom, input.water_table) - top)
        const belowStart = Math.max(top, input.water_table)
        const below = Math.max(0, Math.min(depth, bottom) - belowStart)
        const submergedGamma = input.water_method === 'separate'
          ? layer.gamma_sat - input.gamma_w
          : layer.gamma_sat
        stress += layer.gamma * above + submergedGamma * below
      }
    }
    if (depth <= bottom) break
    top = bottom
  }
  return stress
}

function pressureAt(input, layer, depth) {
  const K = coefficient(input.mode, layer.phi)
  const vertical = calculateVerticalStress(input, depth)
  let soil
  if (input.mode === 'active') soil = Math.max(K * vertical - 2 * layer.c * Math.sqrt(K), 0)
  else if (input.mode === 'passive') soil = K * vertical + 2 * layer.c * Math.sqrt(K)
  else soil = K * vertical
  const water = input.water_method === 'separate' && input.water_table !== null
    ? input.gamma_w * Math.max(depth - input.water_table, 0)
    : 0
  return { K, vertical, soil, water, total: soil + water }
}

function integrateLinear(z1, z2, p1, p2, totalHeight) {
  const length = z2 - z1
  const resultant = (p1 + p2) * length / 2
  if (resultant === 0) return { resultant: 0, momentBase: 0 }
  const localCentroid = length * (p1 + 2 * p2) / (3 * (p1 + p2))
  return { resultant, momentBase: resultant * (totalHeight - z1 - localCentroid) }
}

export function calculateRankineEarthPressure(raw = {}) {
  const input = normalize(raw)
  const segments = []
  const coefficients = []
  let layerTop = 0

  input.layers.forEach((layer, index) => {
    const layerBottom = layerTop + layer.h
    coefficients.push({
      layer: index + 1,
      phi: layer.phi,
      K: roundTo(coefficient(input.mode, layer.phi), 4)
    })
    const points = [layerTop, layerBottom]
    if (input.water_table !== null && input.water_table > layerTop && input.water_table < layerBottom) {
      points.push(input.water_table)
    }
    points.sort((a, b) => a - b)

    for (let i = 0; i < points.length - 1; i += 1) {
      const z1 = points[i], z2 = points[i + 1]
      const start = pressureAt(input, layer, z1)
      const end = pressureAt(input, layer, z2)
      const rawStart = start.K * start.vertical - 2 * layer.c * Math.sqrt(start.K)
      const rawEnd = end.K * end.vertical - 2 * layer.c * Math.sqrt(end.K)
      const split = [z1, z2]
      if (input.mode === 'active' && rawStart * rawEnd < 0) {
        split.push(z1 + (z2 - z1) * (-rawStart) / (rawEnd - rawStart))
        split.sort((a, b) => a - b)
      }
      for (let j = 0; j < split.length - 1; j += 1) {
        const a = pressureAt(input, layer, split[j])
        const b = pressureAt(input, layer, split[j + 1])
        segments.push({
          layer: index + 1,
          z1: split[j], z2: split[j + 1],
          p1: a.total, p2: b.total,
          soil_p1: a.soil, soil_p2: b.soil,
          water_p1: a.water, water_p2: b.water
        })
      }
    }
    layerTop = layerBottom
  })

  let earthResultant = 0, waterResultant = 0, totalResultant = 0
  let earthMoment = 0, waterMoment = 0, totalMoment = 0
  for (const segment of segments) {
    const earth = integrateLinear(segment.z1, segment.z2, segment.soil_p1, segment.soil_p2, input.H)
    const water = integrateLinear(segment.z1, segment.z2, segment.water_p1, segment.water_p2, input.H)
    const total = integrateLinear(segment.z1, segment.z2, segment.p1, segment.p2, input.H)
    earthResultant += earth.resultant; earthMoment += earth.momentBase
    waterResultant += water.resultant; waterMoment += water.momentBase
    totalResultant += total.resultant; totalMoment += total.momentBase
  }

  const tensionSegments = segments.filter(item => item.soil_p1 === 0 || item.soil_p2 === 0)
  const tensionDepth = input.mode === 'active' && input.layers.some(item => item.c > 0) && tensionSegments.length
    ? Math.max(...tensionSegments.flatMap(item => [item.z1, item.z2]).filter(z => pressureAt(input, input.layers.find((_, idx) => {
      const bottom = input.layers.slice(0, idx + 1).reduce((sum, layer) => sum + layer.h, 0)
      return z <= bottom + 1e-9
    }) || input.layers[0], z).soil === 0))
    : null

  const modeNames = { active: '主动土压力', passive: '被动土压力', at_rest: '静止土压力' }
  const steps = [
    `计算类型：${modeNames[input.mode]}，墙高 H = ${input.H.toFixed(3)} m`,
    ...coefficients.map(item => `第${item.layer}层：φ = ${item.phi.toFixed(2)}°，K = ${item.K.toFixed(4)}`),
    input.q > 0 ? `地面均布荷载 q = ${input.q.toFixed(3)} kPa 计入竖向应力` : '地面无附加均布荷载',
    input.water_table === null
      ? '未设置地下水'
      : `地下水位距地表 ${input.water_table.toFixed(3)} m，采用${input.water_method === 'separate' ? '水土分算' : '水土合算'}`,
    `土压力合力 Eₛ = ${earthResultant.toFixed(3)} kN/m`,
    input.water_method === 'separate' && input.water_table !== null
      ? `水压力合力 Eᵥ = ${waterResultant.toFixed(3)} kN/m`
      : '水压力不单独叠加',
    `总侧压力 E = ${totalResultant.toFixed(3)} kN/m，作用点距墙底 ${totalResultant ? (totalMoment / totalResultant).toFixed(3) : '0.000'} m`
  ]

  return {
    data: {
      mode: input.mode,
      water_method: input.water_method,
      total_height: roundTo(input.H),
      coefficients,
      earth_resultant: roundTo(earthResultant),
      water_resultant: roundTo(waterResultant),
      total_resultant: roundTo(totalResultant),
      action_height: roundTo(totalResultant ? totalMoment / totalResultant : 0),
      earth_action_height: roundTo(earthResultant ? earthMoment / earthResultant : 0),
      water_action_height: roundTo(waterResultant ? waterMoment / waterResultant : 0),
      max_pressure: roundTo(Math.max(...segments.flatMap(item => [item.p1, item.p2]))),
      tension_depth: tensionDepth === null ? null : roundTo(tensionDepth),
      segments: segments.map(item => Object.fromEntries(Object.entries(item).map(([key, value]) =>
        [key, typeof value === 'number' ? roundTo(value) : value]
      ))),
      steps,
      assumptions: [
        '墙背竖直、填土面水平、墙背光滑，满足经典朗肯条件',
        '结果按每延米墙长计算',
        '分层界面两侧因强度指标不同，侧压力可能发生跳变'
      ]
    },
    message: `${modeNames[input.mode]}计算完成`
  }
}
