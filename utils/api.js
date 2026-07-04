/**
 * API 工具模块
 *
 * 封装与 Python FastAPI 后端的通信。
 *
 * 开发阶段：
 *   - 微信开发者工具中需勾选「不校验合法域名」
 *   - 真机调试需要通过内网穿透（如 ngrok）暴露后端
 *   - 上线后改为正式的 HTTPS 域名
 */

// ⚠ 开发时改为你的实际地址：
//    - 模拟器: http://127.0.0.1:8000
//    - 真机(同WiFi): http://192.168.x.x:8000
//    - 内网穿透: https://xxx.ngrok-free.app
const BASE_URL = 'http://127.0.0.1:8000'

/**
 * 通用请求函数
 */
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header,
      },
      timeout: 15000,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          uni.showToast({
            title: res.data?.detail || '请求失败',
            icon: 'none',
          })
          reject(res)
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络连接失败，请检查后端服务',
          icon: 'none',
          duration: 2500,
        })
        reject(err)
      },
    })
  })
}

/**
 * 获取材料参数参考表（混凝土、钢筋数据）
 */
export function getReferences() {
  return request('/api/references')
}

/**
 * 正截面承载力计算
 * @param {Object} params
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 钢筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {string} params.as_type - "single" | "double"
 * @param {number} [params.as_given] - 已知受拉钢筋面积（校核模式）
 * @param {number} [params.as_prime_given] - 已知受压钢筋面积（双筋校核）
 */
export function calcBearingCapacity(params) {
  return request('/api/calculate/bearing-capacity', {
    method: 'POST',
    data: params,
  })
}

/**
 * 配筋计算
 * @param {Object} params
 * @param {number} params.M - 设计弯矩 (kN·m)
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 钢筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {number[]} [params.bar_diameters] - 可选钢筋直径
 */
export function calcReinforcement(params) {
  return request('/api/calculate/reinforcement', {
    method: 'POST',
    data: params,
  })
}

/**
 * 截面统一设计（正截面 + 斜截面）
 * @param {Object} params
 * @param {number} params.b - 截面宽度 (mm)
 * @param {number} params.h - 截面高度 (mm)
 * @param {string} params.concrete_grade - 混凝土强度等级
 * @param {string} params.rebar_grade - 纵筋牌号
 * @param {string} params.stirrup_grade - 箍筋牌号
 * @param {number} params.a_s - 保护层厚度 (mm)
 * @param {string} params.load_type - "uniform" | "concentrated"
 * @param {number} [params.shear_span_ratio] - 剪跨比
 * @param {number} [params.as_given] - 已知受拉钢筋面积
 * @param {number} [params.stirrup_diameter] - 箍筋直径
 * @param {number} [params.stirrup_legs] - 箍筋肢数
 * @param {number} [params.stirrup_spacing] - 箍筋间距
 */
export function calcSectionDesign(params) {
  return request('/api/calculate/section-design', {
    method: 'POST',
    data: params,
  })
}

/**
 * 截面几何性质计算
 * @param {Object} params
 * @param {string} params.shape - 截面形状: "rectangle"|"t-section"|"circle"|"annular"|"i-beam"
 * @param {number} [params.b] - 宽度 (mm) — 矩形
 * @param {number} [params.h] - 高度 (mm) — 矩形/T形/工字钢
 * @param {number} [params.b_f] - 翼缘宽度 (mm) — T形/工字钢
 * @param {number} [params.h_f] - 翼缘厚度 (mm) — T形
 * @param {number} [params.b_w] - 腹板宽度 (mm) — T形
 * @param {number} [params.t_f] - 翼缘厚度 (mm) — 工字钢
 * @param {number} [params.t_w] - 腹板厚度 (mm) — 工字钢
 * @param {number} [params.d] - 直径 (mm) — 圆形; 内径 (mm) — 环形
 * @param {number} [params.D] - 外径 (mm) — 环形
 */
export function calcSectionProperties(params) {
  return request('/api/calculate/section-properties', {
    method: 'POST',
    data: params,
  })
}

/**
 * 组合截面几何性质计算（平行移轴公式）
 * @param {Object[]} params.blocks - 矩形分块列表
 * @param {number} params.blocks[].b - 宽度 (mm)
 * @param {number} params.blocks[].h - 高度 (mm)
 * @param {number} params.blocks[].y0 - 底边距参考轴距离 (mm)
 * @param {number} [params.blocks[].x0] - 左边距参考轴距离 (mm)，默认 0
 * @param {boolean} [params.blocks[].is_hole] - 是否为孔洞
 * @param {string} [params.blocks[].label] - 分块名称
 */
export function calcCompositeSection(params) {
  return request('/api/calculate/composite-section', {
    method: 'POST',
    data: params,
  })
}

/**
 * 土力学三相比例指标计算
 * @param {Object} params - 已知指标（任意子集，通常 ≥3 个）
 * @param {number} [params.Gs] - 土粒比重
 * @param {number} [params.w] - 含水量（小数）
 * @param {number} [params.gamma] - 天然重度 (kN/m³)
 * @param {number} [params.gamma_d] - 干重度 (kN/m³)
 * @param {number} [params.gamma_sat] - 饱和重度 (kN/m³)
 * @param {number} [params.gamma_prime] - 有效重度 (kN/m³)
 * @param {number} [params.e] - 孔隙比
 * @param {number} [params.n] - 孔隙率（小数）
 * @param {number} [params.Sr] - 饱和度（小数）
 * @param {number} [params.rho] - 天然密度 (g/cm³)
 * @param {number} [params.rho_d] - 干密度 (g/cm³)
 * @param {number} [params.rho_sat] - 饱和密度 (g/cm³)
 * @param {number} [params.gamma_w] - 水的重度，默认 9.81
 */
export function calcSoilThreePhase(params) {
  return request('/api/calculate/soil-three-phase', {
    method: 'POST',
    data: params,
  })
}

/**
 * 达西定律渗透计算
 * @param {Object} params - 已知参数（任意子集）
 */
export function calcDarcyLaw(params) {
  return request('/api/calculate/darcy-law', {
    method: 'POST',
    data: params,
  })
}
