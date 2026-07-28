import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const [repoArg, outputPath, countArg = '200', seedArg = '20260719'] = process.argv.slice(2)
const repo = path.resolve(repoArg)
const count = Number(countArg), seed = Number(seedArg)
const load = async name => import(pathToFileURL(path.join(repo, 'utils', 'calculators', name)).href)
const [section, composite, soil, darcy, bolt, beam, rebar, bearing, design, shear, foundation] = await Promise.all([
  load('section-properties.js'), load('composite-section.js'), load('soil-three-phase.js'),
  load('darcy-law.js'), load('bolt-connection.js'), load('beam-forces.js'),
  load('reinforcement.js'), load('bearing-capacity.js'), load('section-design.js'), load('shear-capacity.js'),
  load('foundation-bearing.js')
])

let state = seed >>> 0
const random = () => {
  state += 0x6D2B79F5
  let value = state
  value = Math.imul(value ^ value >>> 15, value | 1)
  value ^= value + Math.imul(value ^ value >>> 7, value | 61)
  return ((value ^ value >>> 14) >>> 0) / 4294967296
}
const between = (low, high) => low + random() * (high - low)
const close = (a, b, abs = 0.002, rel = 1e-8) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= abs + rel * Math.abs(b)
const failures = []
let total = 0, passed = 0

function check(property, input, condition, actual = null, expected = null) {
  total += 1
  if (condition) passed += 1
  else failures.push({ property, input, actual, expected })
}

for (let index = 0; index < count; index += 1) {
  const b = between(80, 800), h = between(80, 1200), scale = between(0.4, 3.5)
  const base = section.calculateSectionProperties({ shape: 'rectangle', b, h }).data
  const scaled = section.calculateSectionProperties({ shape: 'rectangle', b: b * scale, h: h * scale }).data
  const expectedArea = b * h * scale ** 2
  const expectedInertia = b * h ** 3 / 12 * scale ** 4
  check('截面缩放 A∝s²', { b, h, scale }, close(scaled.A, expectedArea, 0.100001), scaled.A, expectedArea)
  check('截面缩放 I∝s⁴', { b, h, scale }, close(scaled.I_x, expectedInertia, 1.000001), scaled.I_x, expectedInertia)

  const e = between(0.35, 1.2), Gs = between(2.55, 2.85), w = between(0.02, Math.min(0.4, e / Gs * 0.9))
  const phase = soil.calculateSoilThreePhase({ Gs, w, e }).data
  const expectedPorosity = e / (1 + e)
  const expectedSaturation = w * Gs / e
  check('三相指标 n=e/(1+e)', { Gs, w, e }, close(phase.n, expectedPorosity, 0.00010001), phase.n, expectedPorosity)
  check('三相指标 Sr=wGs/e', { Gs, w, e }, close(phase.Sr, expectedSaturation, 0.00010001), phase.Sr, expectedSaturation)

  const k = 10 ** between(-8, -3), i = between(0.02, 3), A = 10 ** between(-4, 0), factor = between(1.2, 4)
  const flow1 = darcy.calculateDarcyLaw({ k, i, A }).data
  const flow2 = darcy.calculateDarcyLaw({ k, i: i * factor, A }).data
  check('达西定律梯度线性', { k, i, A, factor }, close(flow2.Q, flow1.Q * factor, 1e-10, 1e-7), flow2.Q, flow1.Q * factor)

  const boltInput = { bolt_type: 'ordinary', diameter: 20, bolt_count: 1, shear_planes: 1, bolt_grade: '4.6', steel_grade: 'Q355', connected_thickness: between(5, 30) }
  const oneBolt = bolt.calculateBoltConnection(boltInput).data
  const boltCount = 2 + Math.floor(random() * 15)
  const manyBolts = bolt.calculateBoltConnection({ ...boltInput, bolt_count: boltCount }).data
  const expectedBoltTotal = oneBolt.per_bolt_capacity * boltCount
  const boltRoundingPropagation = 0.0010001 + boltCount * 0.0005
  check('螺栓总承载力与数量线性', { ...boltInput, bolt_count: boltCount }, close(manyBolts.total_capacity, expectedBoltTotal, boltRoundingPropagation), manyBolts.total_capacity, expectedBoltTotal)

  const length = between(3, 15), loadFactor = between(1.2, 4)
  const beamInput = { beam_type: 'simply_supported', load_type: 'combined', L: length, loads: [
    { type: 'point', value: between(5, 100), x: between(0, length) },
    { type: 'udl', value: between(1, 30), x1: length * 0.2, x2: length * 0.8 }
  ] }
  const beam1 = beam.calculateBeamForces(beamInput).data
  const beam2 = beam.calculateBeamForces({ ...beamInput, loads: beamInput.loads.map(item => ({ ...item, value: item.value * loadFactor })) }).data
  const beamRoundingPropagation = 0.0010001 + loadFactor * 0.0005
  check('梁反力与荷载线性', { ...beamInput, factor: loadFactor }, close(beam2.RA, beam1.RA * loadFactor, beamRoundingPropagation), beam2.RA, beam1.RA * loadFactor)
  check('梁弯矩与荷载线性', { ...beamInput, factor: loadFactor }, close(beam2.Mmax, beam1.Mmax * loadFactor, beamRoundingPropagation), beam2.Mmax, beam1.Mmax * loadFactor)

  const lowM = between(10, 400), highM = lowM + between(1, 300)
  const rc = { b: 300, h: 600, concrete_grade: 'C30', rebar_grade: 'HRB400', a_s: 40, a_s_prime: 40 }
  const lowRebar = rebar.calculateReinforcement({ ...rc, M: lowM }).data
  const highRebar = rebar.calculateReinforcement({ ...rc, M: highM }).data
  check('配筋面积随弯矩不减', { lowM, highM }, highRebar.as_req + 0.11 >= lowRebar.as_req, highRebar.as_req, lowRebar.as_req)

  const As1 = between(400, 1800), As2 = As1 + between(10, 500)
  const cap1 = bearing.calculateBearingCapacity({ ...rc, as_type: 'single', as_given: As1 }).data
  const cap2 = bearing.calculateBearingCapacity({ ...rc, as_type: 'single', as_given: As2 }).data
  check('适筋范围承载力随As增加', { As1, As2 }, cap2.mu >= cap1.mu, cap2.mu, cap1.mu)

  const blocks = [{ b: between(100, 400), h: between(100, 600), x0: 0, y0: 0 }]
  const original = composite.calculateCompositeSection({ blocks }).data
  const dx = between(-100, 100), dy = between(-100, 100)
  const translated = composite.calculateCompositeSection({ blocks: blocks.map(item => ({ ...item, x0: item.x0 + dx, y0: item.y0 + dy })) }).data
  check('组合截面平移不改变形心惯性矩', { blocks, dx, dy }, close(translated.I_z, original.I_z, 1.1) && close(translated.I_y, original.I_y, 1.1), { I_z: translated.I_z, I_y: translated.I_y }, { I_z: original.I_z, I_y: original.I_y })

  const designInput = { ...rc, as_type: 'single', stirrup_grade: 'HPB300', load_type: 'uniform', stirrup_diameter: 8, stirrup_legs: 2, stirrup_spacing: 200 }
  const unified = design.calculateSectionDesign(designInput).data
  const standaloneFlex = bearing.calculateBearingCapacity(designInput).data
  const standaloneShear = shear.calculateShearCapacity(designInput).data
  check('统一设计等于独立计算', designInput, unified.flexural.mu === standaloneFlex.mu && unified.shear.V_cs === standaloneShear.V_cs, { flexural: unified.flexural.mu, shear: unified.shear.V_cs }, { flexural: standaloneFlex.mu, shear: standaloneShear.V_cs })

  const foundationInput = {
    b: between(1.2, 5), l: between(5, 8), d: between(0.2, 3), fak: between(80, 350),
    gamma: between(8, 22), gamma_m: between(8, 22), soil_category: 'cohesive_firm',
    Fk: between(100, 1200), Gk: between(20, 300), Mx: 0, My: 0
  }
  const foundation1 = foundation.calculateFoundationBearing(foundationInput).data
  const loadIncrease = between(10, 500)
  const foundation2 = foundation.calculateFoundationBearing({ ...foundationInput, Fk: foundationInput.Fk + loadIncrease }).data
  const expectedPressureIncrease = loadIncrease / (foundationInput.b * foundationInput.l)
  check('地基平均压力随竖向力线性增加', { ...foundationInput, loadIncrease },
    close(foundation2.pk - foundation1.pk, expectedPressureIncrease, 0.0011),
    foundation2.pk - foundation1.pk, expectedPressureIncrease)
  check('轴心基础四角压力相等', foundationInput,
    Object.values(foundation1.corners).every(value => close(value, foundation1.pk, 0.0011)),
    foundation1.corners, foundation1.pk)
}

fs.writeFileSync(outputPath, JSON.stringify({ total, passed, failures }))
