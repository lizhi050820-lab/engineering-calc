import { roundTo, requirePositive } from './common.js'

const SHAPE_NAMES = { rectangle: '矩形', 't-section': 'T形', circle: '圆形', annular: '环形', 'i-beam': '工字钢' }

function finish(shape, values, steps) {
  const [A, I_x, I_y, W_x, W_y, i_x, i_y, S_x, y_c, I_p] = values
  return {
    data: {
      shape, A: roundTo(A, 1), I_x: roundTo(I_x, 0), I_y: roundTo(I_y, 0),
      W_x: roundTo(W_x, 0), W_y: roundTo(W_y, 0), i_x: roundTo(i_x, 1),
      i_y: roundTo(i_y, 1), S_x: roundTo(S_x, 0), y_c: roundTo(y_c, 1),
      I_p: roundTo(I_p, 0), steps, status: 'ok'
    },
    message: `${SHAPE_NAMES[shape]}截面几何性质计算完成`
  }
}

export function calculateSectionProperties(input) {
  const shape = String(input.shape || '').toLowerCase().trim()
  if (!SHAPE_NAMES[shape]) throw new Error(`不支持的截面形状: ${shape}`)
  const steps = [`=== ${SHAPE_NAMES[shape]}截面几何性质计算 ===`]
  let values

  if (shape === 'rectangle') {
    const b = requirePositive(input.b, '宽度 b'), h = requirePositive(input.h, '高度 h')
    const A = b * h, Ix = b * h ** 3 / 12, Iy = h * b ** 3 / 12
    values = [A, Ix, Iy, b * h ** 2 / 6, h * b ** 2 / 6, h / Math.sqrt(12), b / Math.sqrt(12), b * h ** 2 / 8, h / 2, Ix + Iy]
    steps.push(`面积 A = b·h = ${b}×${h} = ${A.toFixed(1)} mm²`, `惯性矩 Iₓ = b·h³/12 = ${Ix.toFixed(0)} mm⁴`, `惯性矩 Iᵧ = h·b³/12 = ${Iy.toFixed(0)} mm⁴`)
  } else if (shape === 't-section') {
    const bf = requirePositive(input.b_f, '翼缘宽度 b_f'), hf = requirePositive(input.h_f, '翼缘厚度 h_f')
    const bw = requirePositive(input.b_w, '腹板宽度 b_w'), h = requirePositive(input.h, '总高度 h')
    if (hf >= h) throw new Error('T形截面：翼缘厚度 h_f 应小于总高度 h')
    if (bw > bf) throw new Error('T形截面：腹板宽度 b_w 应不大于翼缘宽度 b_f')
    const Af = bf * hf, Aw = bw * (h - hf), A = Af + Aw
    const yf = h - hf / 2, yw = (h - hf) / 2, yc = (Af * yf + Aw * yw) / A
    const Ix = bf * hf ** 3 / 12 + Af * (yf - yc) ** 2 + bw * (h - hf) ** 3 / 12 + Aw * (yc - yw) ** 2
    const Iy = hf * bf ** 3 / 12 + (h - hf) * bw ** 3 / 12
    const yTop = h - yc, Wx = Math.min(Ix / yTop, Ix / yc), Wy = Iy / (bf / 2)
    let Sx
    if (yTop <= hf) Sx = bf * yTop ** 2 / 2
    else Sx = Math.max(bf * hf * (yTop - hf / 2) + bw * (yTop - hf) ** 2 / 2, bw * yc ** 2 / 2)
    values = [A, Ix, Iy, Wx, Wy, Math.sqrt(Ix / A), Math.sqrt(Iy / A), Sx, yc, Ix + Iy]
    steps.push(`翼缘面积 A_f = ${Af.toFixed(1)} mm²`, `腹板面积 A_w = ${Aw.toFixed(1)} mm²`, `总面积 A = ${A.toFixed(1)} mm²`, `形心距底边 y_c = ${yc.toFixed(1)} mm`, `惯性矩 Iₓ（平行移轴）= ${Ix.toFixed(0)} mm⁴`)
  } else if (shape === 'circle') {
    const d = requirePositive(input.d, '直径 d'), A = Math.PI * d ** 2 / 4, I = Math.PI * d ** 4 / 64
    values = [A, I, I, Math.PI * d ** 3 / 32, Math.PI * d ** 3 / 32, d / 4, d / 4, d ** 3 / 12, d / 2, 2 * I]
    steps.push(`面积 A = π·d²/4 = ${A.toFixed(1)} mm²`, `惯性矩 Iₓ = Iᵧ = π·d⁴/64 = ${I.toFixed(0)} mm⁴`)
  } else if (shape === 'annular') {
    const D = requirePositive(input.D, '外径 D'), d = requirePositive(input.d, '内径 d')
    if (d >= D) throw new Error('环形截面：内径 d 应小于外径 D')
    const A = Math.PI * (D ** 2 - d ** 2) / 4, I = Math.PI * (D ** 4 - d ** 4) / 64
    const W = Math.PI * (D ** 4 - d ** 4) / (32 * D), i = Math.sqrt(D ** 2 + d ** 2) / 4
    values = [A, I, I, W, W, i, i, (D ** 3 - d ** 3) / 12, D / 2, 2 * I]
    steps.push(`面积 A = π·(D²−d²)/4 = ${A.toFixed(1)} mm²`, `惯性矩 Iₓ = Iᵧ = π·(D⁴−d⁴)/64 = ${I.toFixed(0)} mm⁴`)
  } else {
    const bf = requirePositive(input.b_f, '翼缘宽度 b_f'), h = requirePositive(input.h, '总高度 h')
    const tf = requirePositive(input.t_f, '翼缘厚度 t_f'), tw = requirePositive(input.t_w, '腹板厚度 t_w')
    if (2 * tf >= h) throw new Error('工字钢截面：翼缘总厚 2·t_f 应小于总高度 h')
    if (tw > bf) throw new Error('工字钢截面：腹板厚度 t_w 应不大于翼缘宽度 b_f')
    const hw = h - 2 * tf, A = 2 * bf * tf + hw * tw
    const Ix = bf * h ** 3 / 12 - (bf - tw) * hw ** 3 / 12
    const Iy = 2 * tf * bf ** 3 / 12 + hw * tw ** 3 / 12
    const Sx = bf * tf * (h / 2 - tf / 2) + tw * (hw / 2) * (hw / 4)
    values = [A, Ix, Iy, Ix / (h / 2), Iy / (bf / 2), Math.sqrt(Ix / A), Math.sqrt(Iy / A), Sx, h / 2, Ix + Iy]
    steps.push(`腹板净高 h_w = ${hw.toFixed(0)} mm`, `面积 A = ${A.toFixed(1)} mm²`, `惯性矩 Iₓ（强轴）= ${Ix.toFixed(0)} mm⁴`, `惯性矩 Iᵧ（弱轴）= ${Iy.toFixed(0)} mm⁴`)
  }
  return finish(shape, values, steps)
}
