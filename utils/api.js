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
