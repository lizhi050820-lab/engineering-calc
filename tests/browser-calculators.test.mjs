import assert from 'node:assert/strict'
import { calculateSoilThreePhase } from '../utils/calculators/soil-three-phase.js'
import { calculateDarcyLaw } from '../utils/calculators/darcy-law.js'
import { calculateBeamForces } from '../utils/calculators/beam-forces.js'
import { calculateBearingCapacity } from '../utils/calculators/bearing-capacity.js'
import { calculateReinforcement } from '../utils/calculators/reinforcement.js'
import { calculateSectionDesign } from '../utils/calculators/section-design.js'
import { calculateSectionProperties } from '../utils/calculators/section-properties.js'
import { calculateCompositeSection } from '../utils/calculators/composite-section.js'
import { calculateBoltConnection } from '../utils/calculators/bolt-connection.js'
import { getAlpha1, getEpsilonCu, getXiB } from '../utils/calculators/materials.js'

const close=(actual,expected,tolerance=1e-9)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${actual} != ${expected}`)

const soil=calculateSoilThreePhase({Gs:2.7,w:.15,gamma:18.5}).data
close(soil.gamma_d,16.087,1e-4)
close(soil.e,.6465,1e-4)
close(soil.Sr,.6265,1e-4)
close(soil.gamma_sat,19.9388,1e-4)
assert.deepEqual(soil.missing,[])

const basic=calculateDarcyLaw({k:1e-4,i:.5,A:.02}).data
close(basic.v,5e-5)
close(basic.Q,1e-6)
close(basic.j,4.905)

const constant=calculateDarcyLaw({Q:.002,L:.2,A:.01,delta_h:1.5,t:600}).data
close(constant.k,4.4444444e-5,1e-12)
close(constant.i,7.5)
close(constant.v,.000333333333,1e-12)

const falling=calculateDarcyLaw({a:.785,L:.1,A:.005,h1:120,h2:80,t:3600}).data
close(falling.k,1.76828e-7,1e-12)
assert.throws(()=>calculateDarcyLaw({a:.785,L:.1,A:.005,h1:80,h2:120,t:3600}),/h₁ >.*h₂/)

const beam=calculateBeamForces({
  beam_type:'simply_supported',load_type:'combined',L:10,support_a:2,support_b:8,
  loads:[{type:'udl',value:5,x1:0,x2:10}],
}).data
close(beam.RA,25)
close(beam.RB,25)
close(beam.M_positive,12.5)
close(beam.M_negative,-10)

const combined=calculateBeamForces({
  beam_type:'simply_supported',load_type:'combined',L:10,
  loads:[
    {type:'point',value:20,x:2},
    {type:'udl',value:10,x1:4,x2:8},
    {type:'moment',value:30,x:6,direction:'clockwise'},
  ],
}).data
close(combined.RA,29)
close(combined.RB,31)
close(combined.Mmax,104)
close(combined.x_Mmax,6)

const rightFixed=calculateBeamForces({
  beam_type:'cantilever',load_type:'combined',L:6,fixed_end:'right',
  loads:[{type:'point',value:10,x:2}],
}).data
close(rightFixed.fixed_moment,-40)
close(rightFixed.Mmax,40)

const bearing=calculateBearingCapacity({
  b:300,h:600,concrete_grade:'C30',rebar_grade:'HRB400',a_s:40,
  as_type:'single',as_given:1256,
}).data
close(bearing.mu,229.381,1e-3)
assert.equal(bearing.status,'ok')
assert.equal(getAlpha1('C80'),.94)
close(getEpsilonCu('C80'),.003)
close(getXiB('C30','HRB400'),.517647,1e-6)

const doubleBearing=calculateBearingCapacity({
  b:300,h:600,concrete_grade:'C30',rebar_grade:'HRB400',a_s:40,a_s_prime:40,
  as_type:'double',as_given:1000,as_prime_given:800,
}).data
close(doubleBearing.mu,187.2,1e-3)
assert.equal(doubleBearing.status,'ok')

const rebar=calculateReinforcement({
  M:200,b:300,h:600,concrete_grade:'C30',rebar_grade:'HRB400',a_s:40,a_s_prime:40,
  bar_diameters:[14,16,18,20,22,25],
}).data
close(rebar.as_req,1079.4,.1)
assert.equal(rebar.need_double,false)
assert.ok(rebar.schemes.length>0)

const doubleRebar=calculateReinforcement({
  M:600,b:300,h:600,concrete_grade:'C30',rebar_grade:'HRB400',a_s:40,a_s_prime:40,
}).data
assert.equal(doubleRebar.need_double,true)
assert.ok(doubleRebar.as_prime_req>0)

const sectionDesign=calculateSectionDesign({
  b:300,h:600,concrete_grade:'C30',rebar_grade:'HRB400',stirrup_grade:'HPB300',
  a_s:40,a_s_prime:40,as_type:'single',load_type:'uniform',
  stirrup_diameter:8,stirrup_legs:2,stirrup_spacing:200,
}).data
close(sectionDesign.flexural.mu,516.165,.001)
close(sectionDesign.shear.V_c,168.168,.001)
close(sectionDesign.shear.V_cs,244.222,.001)

const rectangle=calculateSectionProperties({shape:'rectangle',b:200,h:400}).data
close(rectangle.A,80000)
close(rectangle.I_x,1066666667,1)
const circle=calculateSectionProperties({shape:'circle',d:200}).data
close(circle.A,31415.9,.1)
close(circle.I_x,78539816,1)
const annular=calculateSectionProperties({shape:'annular',D:200,d:100}).data
close(annular.A,23561.9,.1)
close(annular.I_x,73631078,1)
const iBeam=calculateSectionProperties({shape:'i-beam',b_f:300,h:400,t_f:20,t_w:12}).data
close(iBeam.A,16320,.1)
close(iBeam.I_x,480256000,1)
assert.throws(()=>calculateSectionProperties({shape:'annular',D:100,d:120}),/内径/)

const composite=calculateCompositeSection({blocks:[
  {b:100,h:100,y0:0,x0:0},
  {b:20,h:20,y0:40,x0:40,is_hole:true},
]}).data
close(composite.A,9600,.1)
close(composite.I_z,8320000,1)
close(composite.S_z,124000,1)

const ordinaryBolt=calculateBoltConnection({
  bolt_type:'ordinary',diameter:20,bolt_count:4,shear_planes:1,bolt_grade:'4.6',
  steel_grade:'Q235',connected_thickness:10,load:150,
}).data
close(ordinaryBolt.total_capacity,175.929,.001)
assert.equal(ordinaryBolt.passed,true)
const highStrengthBolt=calculateBoltConnection({
  bolt_type:'high_strength',diameter:20,bolt_count:4,shear_planes:1,bolt_grade:'8.8',
  steel_grade:'Q355',connected_thickness:10,slip_coefficient:.45,friction_surfaces:1,
  hole_type:'standard',load:300,
}).data
close(highStrengthBolt.total_capacity,202.5,.001)
assert.equal(highStrengthBolt.passed,false)

console.log('浏览器计算核心：现有九项计算工具全部通过')
