export const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key)

export function roundTo(value, digits = 3) {
  if (value === null || value === undefined || !Number.isFinite(value)) return value
  const factor = 10 ** digits
  const rounded = Math.round((value + Number.EPSILON) * factor) / factor
  return Object.is(rounded, -0) ? 0 : rounded
}

export function requirePositive(value, label) {
  const number = Number(value)
  if (!Number.isFinite(number) || number <= 0) throw new Error(`请填写有效的${label}`)
  return number
}

export function localApi(calculator, params) {
  return Promise.resolve().then(() => {
    const result = calculator(params || {})
    return { success: true, data: result.data, message: result.message }
  }).catch(error => {
    error.data = { detail: error.message || '本地计算失败' }
    throw error
  })
}
