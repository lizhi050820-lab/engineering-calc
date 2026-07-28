import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const [repoArg, inputPath, outputPath] = process.argv.slice(2)
if (!repoArg || !inputPath || !outputPath) {
  throw new Error('Usage: node js_batch_runner.mjs <repo> <input.json> <output.json>')
}

const repo = path.resolve(repoArg)
const load = async name => import(pathToFileURL(path.join(repo, 'utils', 'calculators', name)).href)
const [bearing, reinforcement, sectionDesign, sectionProperties, composite, soil, darcy, bolt, beam, rankine, foundation, rebarQuick] = await Promise.all([
  load('bearing-capacity.js'), load('reinforcement.js'), load('section-design.js'),
  load('section-properties.js'), load('composite-section.js'), load('soil-three-phase.js'),
  load('darcy-law.js'), load('bolt-connection.js'), load('beam-forces.js'),
  load('rankine-earth-pressure.js'), load('foundation-bearing.js'), load('rebar-quick.js')
])

const calculators = {
  bearing: bearing.calculateBearingCapacity,
  reinforcement: reinforcement.calculateReinforcement,
  section_design: sectionDesign.calculateSectionDesign,
  section_properties: sectionProperties.calculateSectionProperties,
  composite_section: composite.calculateCompositeSection,
  soil_three_phase: soil.calculateSoilThreePhase,
  darcy_law: darcy.calculateDarcyLaw,
  bolt_connection: bolt.calculateBoltConnection,
  beam_forces: beam.calculateBeamForces,
  rankine_earth_pressure: rankine.calculateRankineEarthPressure,
  foundation_bearing: foundation.calculateFoundationBearing,
  rebar_quick: rebarQuick.calculateRebarQuick
}

const fields = {
  bearing: ['h0', 'fc', 'fy', 'alpha1', 'xi_b', 'rho_min', 'rho_max', 'x', 'xi', 'as_req', 'mu', 'status'],
  reinforcement: ['h0', 'fc', 'fy', 'xi_b', 'rho_min', 'alpha_s', 'xi', 'gamma_s', 'as_req', 'as_min', 'as_max', 'need_double', 'as_prime_req', 'status'],
  section_design: ['flexural.mu', 'flexural.x', 'flexural.xi', 'flexural.as_req', 'flexural.status', 'shear.V_c', 'shear.V_cs', 'shear.V_max', 'shear.A_sv', 'shear.rho_sv', 'shear.rho_sv_min', 'shear.status'],
  section_properties: ['A', 'I_x', 'I_y', 'W_x', 'W_y', 'i_x', 'i_y', 'S_x', 'y_c', 'I_p', 'status'],
  composite_section: ['n_blocks', 'n_holes', 'A', 'y_bar', 'x_bar', 'I_z', 'I_y', 'W_z_top', 'W_z_bot', 'W_y', 'i_z', 'i_y', 'S_z', 'status'],
  soil_three_phase: ['Gs', 'w', 'gamma', 'gamma_d', 'gamma_sat', 'gamma_prime', 'e', 'n', 'Sr', 'rho', 'rho_d', 'rho_sat'],
  darcy_law: ['k', 'i', 'delta_h', 'L', 'Q', 'v', 'A', 'j', 'i_cr', 'gamma_prime', 'Gs', 'e', 'Fs'],
  bolt_connection: ['per_bolt_capacity', 'total_capacity', 'control', 'utilization', 'passed', 'details.shear_capacity', 'details.bearing_capacity', 'details.pretension'],
  beam_forces: ['RA', 'RB', 'fixed_moment', 'Vmax', 'Mmax', 'x_Mmax', 'M_positive', 'x_M_positive', 'M_negative', 'x_M_negative', 'status'],
  rankine_earth_pressure: ['total_height', 'earth_resultant', 'water_resultant', 'total_resultant', 'action_height', 'earth_action_height', 'water_action_height', 'max_pressure'],
  foundation_bearing: ['eta_b', 'eta_d', 'b_correction', 'd_correction', 'area', 'Wx', 'Wy', 'Gk', 'N', 'fa', 'width_increment', 'depth_increment', 'pk', 'pmax', 'pmin', 'pmax_linear', 'pmin_linear', 'eccentricity', 'contact_width', 'pressure_mode', 'full_contact', 'supported', 'stable', 'mean_pass', 'edge_pass', 'overall_pass', 'mean_utilization', 'edge_utilization'],
  rebar_quick: ['operation', 'diameter', 'nominal_area', 'unit_weight', 'total_length', 'total_weight', 'weight_tonnes', 'bar_count', 'interval_count', 'actual_spacing', 'source_area', 'required_count', 'replacement_area', 'area_difference', 'area_change_percent', 'status']
}

function getPath(value, dotted) {
  return dotted.split('.').reduce((current, key) => current == null ? undefined : current[key], value)
}

function select(value, names) {
  return Object.fromEntries(names.map(name => [name, getPath(value, name)]))
}

const cases = JSON.parse(fs.readFileSync(inputPath, 'utf8'))
const results = cases.map(item => {
  try {
    const calculator = calculators[item.tool]
    if (!calculator) throw new Error(`Unsupported tool: ${item.tool}`)
    const result = calculator(item.input)
    return { id: item.id, tool: item.tool, ok: true, values: select(result.data, fields[item.tool]) }
  } catch (error) {
    return { id: item.id, tool: item.tool, ok: false, error: error?.message || String(error) }
  }
})

fs.writeFileSync(outputPath, JSON.stringify(results))
