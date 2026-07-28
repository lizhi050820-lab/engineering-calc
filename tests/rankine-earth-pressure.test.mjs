import assert from 'node:assert/strict'
import { calculateRankineEarthPressure } from '../utils/calculators/rankine-earth-pressure.js'

const close = (actual, expected, tolerance = 0.001) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `期望 ${expected}，实际 ${actual}`)

// 武汉理工大学《土压力》公开课件例题2：
// 两层砂土 H1=6m, φ1=30°, γ1=18；H2=4m, φ2=35°, γ2=20；q=20kPa。
const layered = calculateRankineEarthPressure({
  mode: 'active',
  q: 20,
  layers: [
    { h: 6, phi: 30, gamma: 18, c: 0 },
    { h: 4, phi: 35, gamma: 20, c: 0 }
  ]
}).data
close(layered.total_resultant, 330, 0.2)
close(layered.action_height, 3.82, 0.02)

const sand = calculateRankineEarthPressure({
  mode: 'active', q: 0,
  layers: [{ h: 6, phi: 30, gamma: 18, c: 0 }]
}).data
close(sand.coefficients[0].K, 1 / 3, 0.0001)
close(sand.total_resultant, 0.5 * 18 * 6 ** 2 / 3)
close(sand.action_height, 2)

const passive = calculateRankineEarthPressure({
  mode: 'passive', q: 0,
  layers: [{ h: 6, phi: 30, gamma: 18, c: 0 }]
}).data
close(passive.coefficients[0].K, 3, 0.0001)
close(passive.total_resultant, 0.5 * 18 * 6 ** 2 * 3)

const water = calculateRankineEarthPressure({
  mode: 'active', q: 0, water_table: 2, water_method: 'separate', gamma_w: 10,
  layers: [{ h: 6, phi: 30, gamma: 18, gamma_sat: 20, c: 0 }]
}).data
close(water.water_resultant, 0.5 * 10 * 4 ** 2)
close(water.total_resultant, water.earth_resultant + water.water_resultant)

const cohesive = calculateRankineEarthPressure({
  mode: 'active', q: 0,
  layers: [{ h: 5, phi: 20, gamma: 18, c: 15 }]
}).data
assert.ok(cohesive.segments[0].soil_p1 === 0)
assert.ok(cohesive.total_resultant > 0)

assert.throws(() => calculateRankineEarthPressure({
  mode: 'active', water_table: 7,
  layers: [{ h: 5, phi: 30, gamma: 18, gamma_sat: 20 }]
}), /地下水位深度/)

console.log('朗肯土压力：经典、分层、地下水、黏性土与非法输入算例全部通过')
