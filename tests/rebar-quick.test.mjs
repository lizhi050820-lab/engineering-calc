import assert from 'node:assert/strict'
import { calculateRebarQuick, STANDARD_REBARS } from '../utils/calculators/rebar-quick.js'

const close = (actual, expected, tolerance = 0.001) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `期望 ${expected}，实际 ${actual}`)

const standard16 = STANDARD_REBARS.find(item => item.diameter === 16)
close(standard16.area, 201.1)
close(standard16.unit_weight, 1.58)

const quantity = calculateRebarQuick({
  operation: 'quantity', diameter: 16, bar_length: 6, bar_count: 25
}).data
close(quantity.total_length, 150)
close(quantity.total_weight, 237)

const inverse = calculateRebarQuick({
  operation: 'weight_to_length', diameter: 16, total_weight: 158
}).data
close(inverse.total_length, 100)

const spacing = calculateRebarQuick({
  operation: 'spacing', diameter: 16, layout_length: 5100,
  max_spacing: 200, bar_length: 6
}).data
assert.equal(spacing.interval_count, 26)
assert.equal(spacing.bar_count, 27)
close(spacing.actual_spacing, 196.154)
close(spacing.total_weight, 255.96)

const equivalent = calculateRebarQuick({
  operation: 'equivalent', source_diameter: 20, source_count: 4, target_diameter: 18
}).data
close(equivalent.source_area, 1256.8, 0.1)
assert.equal(equivalent.required_count, 5)
close(equivalent.replacement_area, 1272.5, 0.1)
assert.ok(equivalent.replacement_area >= equivalent.source_area)

assert.throws(() => calculateRebarQuick({
  operation: 'quantity', diameter: 15, bar_length: 6, bar_count: 10
}), /标准规格/)
assert.throws(() => calculateRebarQuick({
  operation: 'quantity', diameter: 16, bar_length: 6, bar_count: 2.5
}), /正整数/)
assert.throws(() => calculateRebarQuick({
  operation: 'spacing', diameter: 16, layout_length: 0, max_spacing: 200, bar_length: 6
}), /布置长度/)

console.log('钢筋工程速算：国标表值、用量、反算、排布、代换与非法输入全部通过')
