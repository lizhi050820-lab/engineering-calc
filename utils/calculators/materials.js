export const CONCRETE_FC = {
  C20: 9.6, C25: 11.9, C30: 14.3, C35: 16.7, C40: 19.1, C45: 21.1,
  C50: 23.1, C55: 25.3, C60: 27.5, C65: 29.7, C70: 31.8, C75: 33.8, C80: 35.9
}

export const CONCRETE_FT = {
  C20: 1.10, C25: 1.27, C30: 1.43, C35: 1.57, C40: 1.71, C45: 1.80,
  C50: 1.89, C55: 1.96, C60: 2.04, C65: 2.09, C70: 2.14, C75: 2.18, C80: 2.22
}

export const REBAR_FY = { HPB300: 270, HRB400: 360, HRB500: 435 }
export const REBAR_ES = { HPB300: 2.10, HRB400: 2.00, HRB500: 2.00 }
export const REBAR_AREA = {
  6: 28.3, 8: 50.3, 10: 78.5, 12: 113.1, 14: 153.9, 16: 201.1,
  18: 254.5, 20: 314.2, 22: 380.1, 25: 490.9, 28: 615.8,
  32: 804.2, 36: 1017.9, 40: 1256.6
}

export const STIRRUP_FYV = { HPB300: 270, HRB400: 360 }

export function getAlpha1(grade) {
  const strength = Number(String(grade).slice(1))
  return strength <= 50 ? 1 : Math.round((1 - (strength - 50) * 0.06 / 30) * 100) / 100
}

export function getBeta1(grade) {
  const strength = Number(String(grade).slice(1))
  return strength <= 50 ? 0.8 : Math.max(0.74, 0.8 - (strength - 50) * 0.002)
}

export function getEpsilonCu(grade) {
  const strength = Number(String(grade).slice(1))
  return strength <= 50 ? 0.0033 : 0.0033 - (strength - 50) * 1e-5
}

export function getXiB(concreteGrade, rebarGrade) {
  const fy = REBAR_FY[rebarGrade]
  return getBeta1(concreteGrade) / (1 + fy / (REBAR_ES[rebarGrade] * 1e5 * getEpsilonCu(concreteGrade)))
}

export function materialReferences() {
  return {
    success: true,
    concrete: { grades: Object.keys(CONCRETE_FC), fc: CONCRETE_FC, ft: CONCRETE_FT },
    rebar: { grades: Object.keys(REBAR_FY), fy: REBAR_FY, es: REBAR_ES },
    rebar_areas: Object.fromEntries(Object.entries(REBAR_AREA).map(([key, value]) => [String(key), value]))
  }
}
