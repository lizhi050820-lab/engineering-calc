<template>
  <view class="page">
    <!-- ========== CAD 截面图 ========== -->
    <view class="card">
      <view class="cad-wrap">
        <view class="cad-dim-top">
          <view class="cad-tick"></view>
          <text class="cad-dim">b = {{ form.b || '?' }}</text>
          <view class="cad-tick"></view>
        </view>
        <view class="cad-row">
          <view class="cad-dim-left">
            <view class="cad-tick"></view>
            <text class="cad-dim-v">h = {{ form.h || '?' }}</text>
            <view class="cad-tick"></view>
          </view>
          <view class="cad-frame">
            <view v-if="form.as_type === 'double'" class="cad-bar-top">
              <view class="cad-dot"></view><view class="cad-dot"></view>
            </view>
            <view class="cad-bar-bot">
              <view class="cad-dot"></view><view class="cad-dot"></view><view class="cad-dot"></view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- ========== 截面尺寸与材料 ========== -->
    <view class="card">
      <view class="card-title">截面尺寸与材料</view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">截面宽度 b (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.b" placeholder="300" />
        </view>
        <view class="form-group">
          <text class="form-label">截面高度 h (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.h" placeholder="600" />
        </view>
      </view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">混凝土等级</text>
          <picker :range="concreteGrades" :value="concreteIndex" @change="onConcreteChange">
            <view class="form-picker">{{ form.concrete_grade }}</view>
          </picker>
        </view>
        <view class="form-group">
          <text class="form-label">纵筋牌号</text>
          <picker :range="rebarGrades" :value="rebarIndex" @change="onRebarChange">
            <view class="form-picker">{{ form.rebar_grade }}</view>
          </picker>
        </view>
      </view>
    </view>

    <!-- ========== 正截面配筋类型 ========== -->
    <view class="card">
      <view class="card-title">正截面配筋类型</view>
      <view class="type-toggle">
        <view class="type-btn" :class="{ active: form.as_type === 'single' }" @click="form.as_type = 'single'">单筋截面</view>
        <view class="type-btn" :class="{ active: form.as_type === 'double' }" @click="form.as_type = 'double'">双筋截面</view>
      </view>
      <view class="grid-2" style="margin-top: 20rpx;">
        <view class="form-group">
          <text class="form-label">受拉区 aₛ (mm)</text>
          <text class="form-hint">钢筋中心→截面底边</text>
          <input class="form-input" type="digit" v-model.number="form.a_s" placeholder="40" />
        </view>
        <view v-if="form.as_type === 'double'" class="form-group">
          <text class="form-label">受压区 a′ₛ (mm)</text>
          <text class="form-hint">钢筋中心→截面顶边</text>
          <input class="form-input" type="digit" v-model.number="form.a_s_prime" placeholder="40" />
        </view>
      </view>
    </view>

    <!-- ========== 斜截面参数 ========== -->
    <view class="card">
      <view class="card-title">斜截面 — 箍筋与荷载</view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">箍筋牌号</text>
          <picker :range="stirrupGrades" :value="stirrupIndex" @change="onStirrupChange">
            <view class="form-picker">{{ form.stirrup_grade }}</view>
          </picker>
        </view>
        <view class="form-group">
          <text class="form-label">荷载类型</text>
          <picker :range="['均布荷载', '集中荷载']" :value="form.load_type === 'uniform' ? 0 : 1" @change="onLoadTypeChange">
            <view class="form-picker">{{ form.load_type === 'uniform' ? '均布荷载' : '集中荷载' }}</view>
          </picker>
        </view>
      </view>
      <view class="form-group" v-if="form.load_type === 'concentrated'">
        <text class="form-label">剪跨比 λ (1.5~3.0)</text>
        <input class="form-input" type="digit" v-model.number="form.shear_span_ratio" placeholder="2.0" />
      </view>
    </view>

    <!-- ========== 计算模式 ========== -->
    <view class="card">
      <view class="card-title">计算模式</view>
      <view class="type-toggle">
        <view class="type-btn" :class="{ active: !checkMode }" @click="checkMode = false">设计模式</view>
        <view class="type-btn" :class="{ active: checkMode }" @click="checkMode = true">校核模式</view>
      </view>
      <view v-if="checkMode" style="margin-top: 24rpx;">
        <view class="form-group">
          <text class="form-label">受拉钢筋面积 As (mm²)</text>
          <text class="form-hint">如 4Φ20 = 1256</text>
          <input class="form-input" type="digit" v-model.number="form.as_given" placeholder="1256" />
        </view>
        <view v-if="form.as_type === 'double'" class="form-group">
          <text class="form-label">受压钢筋面积 As' (mm²)</text>
          <text class="form-hint">如 2Φ20 = 628</text>
          <input class="form-input" type="digit" v-model.number="form.as_prime_given" placeholder="628" />
        </view>
        <view style="font-size:26rpx;color:#333;font-weight:600;margin:20rpx 0 8rpx;">斜截面校核（箍筋信息）</view>
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">箍筋直径 (mm)</text>
            <picker :range="diameterOptions" :value="diameterIndex" @change="onDiameterChange">
              <view class="form-picker">{{ form.stirrup_diameter || '选择' }}</view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">箍筋肢数</text>
            <picker :range="legOptions" :value="legIndex" @change="onLegChange">
              <view class="form-picker">{{ form.stirrup_legs }} 肢</view>
            </picker>
          </view>
        </view>
        <view class="form-group">
          <text class="form-label">箍筋间距 (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.stirrup_spacing" placeholder="200" />
        </view>
      </view>
    </view>

    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中...' : '计算' }}
    </button>

    <!-- ========== 结果区 ========== -->
    <view v-if="result" class="results">

      <!-- 正截面 -->
      <view class="card" v-if="result.data.flexural">
        <view class="card-title">正截面承载力（受弯）</view>

        <view class="calc-hero">
          <text class="calc-hero-label">{{ checkMode ? '极限弯矩 Mᵤ' : '单筋最大承载力 Mᵤ,max' }}</text>
          <text class="calc-hero-value">{{ result.data.flexural.mu }}<text class="calc-hero-unit"> kN·m</text></text>
          <text class="status-tag" :class="statusFlexClass">{{ result.data.flexural.status === 'ok' ? '适筋' : result.data.flexural.status }}</text>
        </view>

        <view class="calc-process">
          <view class="calc-row">
            <text class="calc-key">材料参数</text>
            <text class="calc-val">fc = {{ result.data.flexural.fc }} MPa, fy = {{ result.data.flexural.fy }} MPa, α₁ = {{ result.data.flexural.alpha1 }}</text>
          </view>
          <view class="calc-hr"></view>

          <view class="calc-row">
            <text class="calc-key">有效高度</text>
            <text class="calc-val">h₀ = h − aₛ = {{ form.h }} − {{ form.a_s }} = {{ result.data.flexural.h0 }} mm</text>
          </view>
          <view class="calc-hr"></view>

          <view class="calc-row">
            <text class="calc-key">ξb</text>
            <text class="calc-val">{{ result.data.flexural.xi_b }}</text>
          </view>
          <view class="calc-hr"></view>

          <view class="calc-row">
            <text class="calc-key">ρmin / ρmax</text>
            <text class="calc-val">{{ result.data.flexural.rho_min }} / {{ result.data.flexural.rho_max }}</text>
          </view>
          <view class="calc-hr"></view>

          <!-- 校核模式 -->
          <template v-if="checkMode">
            <view class="calc-row">
              <text class="calc-key">受压区高度</text>
              <text class="calc-val">x = {{ result.data.flexural.x }} mm, ξ = {{ result.data.flexural.xi }}</text>
            </view>
            <view class="calc-hr"></view>
          </template>

          <!-- ===== 设计模式：配筋结果 ===== -->
          <template v-if="!checkMode">
            <!-- 单筋 -->
            <template v-if="form.as_type === 'single'">
              <view class="calc-row">
                <text class="calc-key">配筋范围 (受拉)</text>
                <text class="calc-val">Aₛ,min = {{ asMin }} ～ Aₛ,max = {{ asMax }} mm²</text>
              </view>
              <view class="calc-hr"></view>

              <!-- 选筋推荐 -->
              <view class="calc-section-label">推荐配筋方案：</view>
              <view v-for="s in rebarSchemes" :key="s.label" class="calc-row">
                <text class="calc-key">{{ s.label }}</text>
                <text class="calc-val">{{ s.desc }}（As = {{ s.area }} mm²{{ s.note ? '，' + s.note : '' }}）</text>
              </view>
              <view class="calc-hr"></view>
            </template>

            <!-- 双筋 -->
            <template v-if="form.as_type === 'double'">
              <view class="calc-row">
                <text class="calc-key">单筋上限 (受拉)</text>
                <text class="calc-val">Aₛ₁ = {{ result.data.flexural.as_req }} mm²（ρmax = {{ result.data.flexural.rho_max }}）</text>
              </view>
              <view class="calc-hr"></view>
              <template v-if="result.data.flexural.design_points">
                <view class="calc-section-label">超出上限后需双筋（受拉 As + 受压 As'）：</view>
                <view v-for="pt in result.data.flexural.design_points" :key="pt.label" class="calc-row">
                  <text class="calc-key">{{ pt.label }}</text>
                  <text class="calc-val">
                    <text style="color:#C62828;">A′ₛ = {{ pt.As_prime }}</text>
                    <text style="margin:0 6rpx;">+</text>
                    <text style="color:#2E7D32;">As = {{ pt.As }}</text>
                    <text> mm²</text>
                  </text>
                </view>
                <view class="calc-hr"></view>
              </template>
            </template>
          </template>
        </view>
      </view>

      <!-- 斜截面 -->
      <view class="card" v-if="result.data.shear">
        <view class="card-title">斜截面受剪承载力</view>

        <view class="calc-hero">
          <text class="calc-hero-label">受剪承载力 {{ form.stirrup_diameter ? 'V꜀ₛ' : 'V꜀' }}</text>
          <text class="calc-hero-value">{{ form.stirrup_diameter ? result.data.shear.V_cs : result.data.shear.V_c }}<text class="calc-hero-unit"> kN</text></text>
          <text class="status-tag" :class="statusShearClass">{{ result.data.shear.status === 'ok' ? '满足' : result.data.shear.status }}</text>
        </view>

        <view class="calc-process">
          <view class="calc-row">
            <text class="calc-key">材料参数</text>
            <text class="calc-val">f꜀ = {{ result.data.shear.fc }} MPa，fₜ = {{ result.data.shear.ft }} MPa，fᵧᵥ = {{ result.data.shear.f_yv }} MPa</text>
          </view>
          <view class="calc-hr"></view>

          <view class="calc-row">
            <text class="calc-key">截面限制</text>
            <text class="calc-val">Vmax = {{ result.data.shear.V_max }} kN（β꜀ = {{ result.data.shear.beta_c }}）</text>
          </view>
          <view class="calc-hr"></view>

          <view class="calc-row">
            <text class="calc-key">混凝土项 V꜀</text>
            <text class="calc-val">{{ result.data.shear.V_c }} kN（βₕ = {{ result.data.shear.beta_h }}）</text>
          </view>
          <view class="calc-hr"></view>

          <template v-if="result.data.shear.A_sv > 0">
            <view class="calc-row">
              <text class="calc-key">箍筋面积 Aₛᵥ</text>
              <text class="calc-val">{{ result.data.shear.A_sv }} mm²</text>
            </view>
            <view class="calc-hr"></view>
            <view class="calc-row">
              <text class="calc-key">配箍率</text>
              <text class="calc-val">ρₛᵥ = {{ result.data.shear.rho_sv }}（≥ ρₛᵥ,min = {{ result.data.shear.rho_sv_min }}）</text>
            </view>
            <view class="calc-hr"></view>
            <view v-if="result.data.shear.V_cs > 0" class="calc-row">
              <text class="calc-key">总承载力 V꜀ₛ</text>
              <text class="calc-val">{{ result.data.shear.V_cs }} kN</text>
            </view>
          </template>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { calcSectionDesign } from '@/utils/api.js'

// 常用钢筋组合（Φ14~Φ25，面积从大到小）
const REBAR_COMBOS = [
  { desc: '7Φ25', area: 3436 }, { desc: '8Φ22', area: 3040 }, { desc: '6Φ25', area: 2946 },
  { desc: '7Φ22', area: 2660 }, { desc: '5Φ25', area: 2454 }, { desc: '8Φ20', area: 2512 },
  { desc: '6Φ22', area: 2280 }, { desc: '7Φ20', area: 2198 }, { desc: '4Φ25', area: 1964 },
  { desc: '5Φ22', area: 1900 }, { desc: '6Φ20', area: 1884 }, { desc: '7Φ18', area: 1780 },
  { desc: '4Φ22', area: 1520 }, { desc: '5Φ20', area: 1570 }, { desc: '3Φ25', area: 1473 },
  { desc: '6Φ18', area: 1526 }, { desc: '4Φ20', area: 1256 }, { desc: '5Φ18', area: 1272 },
  { desc: '3Φ22', area: 1140 }, { desc: '4Φ18', area: 1018 }, { desc: '5Φ16', area: 1005 },
  { desc: '3Φ20', area: 942 }, { desc: '4Φ16', area: 804 }, { desc: '2Φ22', area: 760 },
  { desc: '2Φ20', area: 628 }, { desc: '3Φ16', area: 603 }, { desc: '2Φ18', area: 509 },
  { desc: '3Φ14', area: 461 }, { desc: '2Φ16', area: 402 }, { desc: '2Φ14', area: 308 },
]

function findClosestRebar(target) {
  let best = REBAR_COMBOS[0]
  for (const c of REBAR_COMBOS) {
    if (Math.abs(c.area - target) < Math.abs(best.area - target)) best = c
  }
  return best
}

export default {
  data() {
    return {
      form: {
        b: 300, h: 600,
        concrete_grade: 'C30', rebar_grade: 'HRB400', stirrup_grade: 'HPB300',
        a_s: 40, a_s_prime: 40, as_type: 'single',
        load_type: 'uniform', shear_span_ratio: null,
        as_given: null, as_prime_given: null,
        stirrup_diameter: null, stirrup_legs: 2, stirrup_spacing: null,
      },
      concreteGrades: ['C25','C30','C35','C40','C45','C50','C55','C60','C65','C70','C75','C80'],
      rebarGrades: ['HPB300','HRB400','HRB500'],
      stirrupGrades: ['HPB300','HRB400'],
      diameterOptions: [6,8,10,12], legOptions: [2,4],
      concreteIndex: 1, rebarIndex: 1, stirrupIndex: 0, diameterIndex: 1, legIndex: 0,
      checkMode: false, loading: false, result: null,
    }
  },
  computed: {
    asMin() {
      const d = this.result?.data?.flexural
      if (!d) return 0
      return (d.rho_min * this.form.b * this.form.h).toFixed(1)
    },
    asMax() {
      const d = this.result?.data?.flexural
      if (!d) return 0
      return (d.rho_max * this.form.b * d.h0).toFixed(1)
    },
    rebarSchemes() {
      const min = parseFloat(this.asMin)
      const max = parseFloat(this.asMax)
      if (!min || !max) return []

      // 找最接近 As_min、中间值、As_max 的方案
      const targets = [
        { label: '最小配筋', area: min },
        { label: '适中配筋', area: (min + max) / 2 },
        { label: '最大配筋 (单筋)', area: max },
      ]
      return targets.map(t => {
        const scheme = findClosestRebar(t.area)
        const diff = ((scheme.area - t.area) / t.area * 100)
        const note = diff >= 0 ? `超出 +${diff.toFixed(1)}%` : `不足 ${diff.toFixed(1)}%`
        return { ...t, ...scheme, note }
      })
    },
    statusFlexClass() {
      const s = this.result?.data?.flexural?.status
      if (s === 'ok') return 'status-ok'
      if (s === 'under_reinforced') return 'status-warn'
      return 'status-error'
    },
    statusShearClass() {
      const s = this.result?.data?.shear?.status
      if (s === 'ok') return 'status-ok'
      if (s === 'insufficient') return 'status-warn'
      return 'status-error'
    },
  },
  methods: {
    onConcreteChange(e) { this.concreteIndex = e.detail.value; this.form.concrete_grade = this.concreteGrades[e.detail.value] },
    onRebarChange(e) { this.rebarIndex = e.detail.value; this.form.rebar_grade = this.rebarGrades[e.detail.value] },
    onStirrupChange(e) { this.stirrupIndex = e.detail.value; this.form.stirrup_grade = this.stirrupGrades[e.detail.value] },
    onDiameterChange(e) { this.diameterIndex = e.detail.value; this.form.stirrup_diameter = this.diameterOptions[e.detail.value] },
    onLegChange(e) { this.legIndex = e.detail.value; this.form.stirrup_legs = this.legOptions[e.detail.value] },
    onLoadTypeChange(e) { this.form.load_type = e.detail.value === 0 ? 'uniform' : 'concentrated' },
    async doCalculate() {
      if (!this.form.b || !this.form.h) { uni.showToast({ title: '请填写截面尺寸', icon: 'none' }); return }
      if (this.form.load_type === 'concentrated' && !this.form.shear_span_ratio) { uni.showToast({ title: '集中荷载需填写剪跨比 λ', icon: 'none' }); return }
      this.loading = true; this.result = null
      try {
        const p = { ...this.form }
        if (!this.checkMode) { p.as_given = null; p.as_prime_given = null; p.stirrup_diameter = null; p.stirrup_spacing = null }
        this.result = await calcSectionDesign(p)
      } catch (e) { console.error('计算失败:', e) }
      finally { this.loading = false }
    },
  },
}
</script>

<style scoped>
.page { padding: 16px; }
.results { margin-top: 16px; }

/* ========== CAD 图 ========== */
.cad-wrap { display: flex; flex-direction: column; align-items: center; }
.cad-dim-top { display: flex; align-items: center; margin-bottom: 2rpx; }
.cad-dim { font-size: 22rpx; color: #555; padding: 0 12rpx; }
.cad-row { display: flex; align-items: center; }
.cad-dim-left { display: flex; flex-direction: column; align-items: center; padding-right: 12rpx; }
.cad-dim-v { font-size: 22rpx; color: #555; writing-mode: vertical-rl; padding: 10rpx 0; }
.cad-tick { background: #666; }
.cad-dim-top .cad-tick, .cad-dim-left .cad-tick { width: 1rpx; height: 14rpx; }
.cad-dim-left .cad-tick { width: 14rpx; height: 1rpx; }
.cad-frame {
  width: 260rpx;
  border: 2rpx solid #333;
  display: flex; flex-direction: column; justify-content: space-between;
  min-height: 200rpx;
}
.cad-bar-top, .cad-bar-bot { display: flex; align-items: center; gap: 12rpx; padding: 14rpx 16rpx; }
.cad-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #333; flex-shrink: 0; }

/* ========== 通用 ========== */
.card-title { font-size: 30rpx; font-weight: 600; color: #222; margin-bottom: 20rpx; padding-bottom: 12rpx; border-bottom: 1rpx solid #eee; }
.form-label { display: block; font-size: 26rpx; color: #333; margin-bottom: 6rpx; font-weight: 500; }
.form-hint { display: block; font-size: 22rpx; color: #999; margin-bottom: 8rpx; }
.form-picker { display: flex; justify-content: space-between; align-items: center; width: 100%; height: 80rpx; background: #F0EFEB; border-radius: 15rpx; padding: 0 24rpx; font-size: 30rpx; }
.type-toggle { display: flex; background: #E5E9E6; border-radius: 14rpx; padding: 5rpx; }
.type-btn { flex: 1; text-align: center; padding: 20rpx 0; font-size: 28rpx; color: #666; border-radius: 8rpx; }
.type-btn.active { background: #14575B; color: #fff; font-weight: 600; }

/* ========== 结果 ========== */
.calc-hero { text-align: center; padding: 16rpx 0 24rpx; }
.calc-hero-label { display: block; font-size: 26rpx; color: #666; margin-bottom: 8rpx; }
.calc-hero-value { display: block; font-size: 56rpx; font-weight: 800; color: #111; margin-bottom: 12rpx; }
.calc-hero-unit { font-size: 28rpx; font-weight: 500; color: #999; }
.calc-process { margin-top: 8rpx; }
.calc-row { display: flex; align-items: baseline; padding: 16rpx 0; }
.calc-key { width:170rpx;flex-shrink:0;font-size:24rpx;color:#526B6C;font-weight:600;padding-top:5rpx; }
.calc-val { flex:1;font-size:28rpx;color:#17383A;line-height:1.75;font-variant-numeric:lining-nums tabular-nums;letter-spacing:.3rpx; }
.calc-hr { height: 1rpx; background: #E8E8E8; }
.calc-section-label { font-size: 26rpx; color: #333; font-weight: 600; padding: 12rpx 0 4rpx; }
</style>
