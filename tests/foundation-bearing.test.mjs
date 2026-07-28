import assert from 'node:assert/strict'
import { calculateFoundationBearing } from '../utils/calculators/foundation-bearing.js'

const close = (actual, expected, tolerance = 0.001) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `期望 ${expected}，实际 ${actual}`)

// 江苏建筑职业技术学院公开独立基础计算书，节点5，标准组合（第6～7页）。
const published = calculateFoundationBearing({
  b: 1.7, l: 1.7, d: 1.6, fak: 180,
  soil_category: 'cohesive_firm', gamma: 20, gamma_m: 20,
  Fk: 72.8, Gk: 69.36, Mx: 4.78, My: 28.81
}).data
close(published.fa, 215.2)
close(published.pk, 49.19, 0.01)
close(published.pmax, 90.21, 0.03)
close(published.pmin, 8.17, 0.03)
assert.equal(published.overall_pass, true)

const axial = calculateFoundationBearing({
  b: 2, l: 3, d: 0.4, fak: 150,
  soil_category: 'cohesive_firm', gamma: 18, gamma_m: 18,
  Fk: 600, foundation_weight_pressure: 20
}).data
close(axial.fa, 150)
close(axial.pk, 120)
close(axial.Gk, 120)
assert.equal(axial.pressure_mode, 'uniform')

const uniaxialLarge = calculateFoundationBearing({
  b: 2, l: 3, d: 1, fak: 180,
  soil_category: 'cohesive_firm', gamma: 18, gamma_m: 18,
  Fk: 500, Gk: 100, My: 240
}).data
assert.equal(uniaxialLarge.pressure_mode, 'uniaxial_triangular_contact')
close(uniaxialLarge.eccentricity, 0.4)
close(uniaxialLarge.contact_width, 1.8)
close(uniaxialLarge.pmax, 222.222)

const biaxialSeparation = calculateFoundationBearing({
  b: 2, l: 2, d: 1, fak: 180,
  soil_category: 'cohesive_firm', gamma: 18, gamma_m: 18,
  Fk: 300, Gk: 50, Mx: 100, My: 100
}).data
assert.equal(biaxialSeparation.pressure_mode, 'biaxial_separation_review')
assert.equal(biaxialSeparation.pmax, null)
assert.equal(biaxialSeparation.overall_pass, false)

assert.throws(() => calculateFoundationBearing({
  b: 0, l: 2, d: 1, fak: 180, gamma: 18, gamma_m: 18, Fk: 300
}), /基础宽度/)

assert.throws(() => calculateFoundationBearing({
  b: 2, l: 2, d: 1, fak: 180, gamma: 18, gamma_m: 18, Fk: 300,
  soil_category: 'custom'
}), /ηb/)

console.log('地基承载力：权威算例、轴心、单向大偏心、双向脱空与非法输入全部通过')
