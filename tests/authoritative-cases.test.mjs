import assert from 'node:assert/strict'
import fs from 'node:fs'

import { calculateSoilThreePhase } from '../utils/calculators/soil-three-phase.js'
import { calculateDarcyLaw } from '../utils/calculators/darcy-law.js'
import { calculateBoltConnection } from '../utils/calculators/bolt-connection.js'
import { calculateBearingCapacity } from '../utils/calculators/bearing-capacity.js'
import { calculateRankineEarthPressure } from '../utils/calculators/rankine-earth-pressure.js'
import { calculateFoundationBearing } from '../utils/calculators/foundation-bearing.js'

const cases = JSON.parse(fs.readFileSync(new URL('../verification/authoritative-cases/cases.json', import.meta.url), 'utf8'))
const calculators = {
  soil_three_phase: calculateSoilThreePhase,
  darcy_law: calculateDarcyLaw,
  bolt_connection: calculateBoltConnection,
  bearing: calculateBearingCapacity,
  rankine_earth_pressure: calculateRankineEarthPressure,
  foundation_bearing: calculateFoundationBearing
}

const get = (object, path) => path.split('.').reduce((value, key) => value?.[key], object)
const close = (actual, expected, tolerance, label) => {
  assert.ok(Number.isFinite(actual), `${label}: 实际值不是有限数`)
  assert.ok(Math.abs(actual - expected) <= tolerance,
    `${label}: 期望 ${expected}，实际 ${actual}，容差 ${tolerance}`)
}

let gatePassed = 0
const reviews = []
for (const item of cases) {
  const result = calculators[item.tool](item.input).data
  if (item.status === 'review') {
    reviews.push({ id: item.id, actual: result.mu, ...item.published_expected })
    continue
  }

  for (const [field, expected] of Object.entries(item.expected)) {
    const actual = field === 'volume_10s' ? result.Q * item.input.t : get(result, field)
    if (typeof expected === 'number') close(actual, expected, item.tolerance[field], `${item.id}.${field}`)
    else assert.equal(actual, expected, `${item.id}.${field}`)
  }
  gatePassed += 1
}

console.log(`权威固定算例：${gatePassed} 个发布门禁算例全部通过`)
for (const item of reviews) {
  console.log(`[待审查] ${item.id}: 程序=${item.actual} kN·m，论文修正法=${item.research_method_mu} kN·m，论文所列传统法=${item.conventional_double_rebar_mu} kN·m`)
}
