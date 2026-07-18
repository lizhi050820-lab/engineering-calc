import { calculateBearingCapacity } from './bearing-capacity.js'
import { calculateShearCapacity } from './shear-capacity.js'

export function calculateSectionDesign(input) {
  const flexural = calculateBearingCapacity(input)
  const shear = calculateShearCapacity(input)
  flexural.data.message = flexural.message
  shear.data.message = shear.message
  return {
    data: { flexural: flexural.data, shear: shear.data },
    message: `正截面: ${flexural.message} | 斜截面: ${shear.message}`
  }
}
