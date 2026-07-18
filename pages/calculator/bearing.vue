<template>
  <view class="container">
    <!-- ========== CAD 截面图（纯线条+点，无文字）========== -->
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
            <view v-if="asType === 'double'" class="cad-bar-top">
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
          <input class="form-input" v-model.number="form.b" type="digit" placeholder="300" />
        </view>
        <view class="form-group">
          <text class="form-label">截面高度 h (mm)</text>
          <input class="form-input" v-model.number="form.h" type="digit" placeholder="600" />
        </view>
      </view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">混凝土强度等级</text>
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

    <!-- ========== 配筋类型 ========== -->
    <view class="card">
      <view class="card-title">配筋类型</view>
      <view class="type-toggle">
        <view class="type-btn" :class="{ active: asType === 'single' }" @click="asType = 'single'">单筋截面</view>
        <view class="type-btn" :class="{ active: asType === 'double' }" @click="asType = 'double'">双筋截面</view>
      </view>
    </view>

    <!-- ========== 保护层 ========== -->
    <view class="card">
      <view class="card-title">保护层厚度</view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">受拉区 aₛ (mm)</text>
          <text class="form-hint">钢筋中心→截面底边</text>
          <input class="form-input" v-model.number="form.a_s" type="digit" placeholder="40" />
        </view>
        <view v-if="asType === 'double'" class="form-group">
          <text class="form-label">受压区 a′ₛ (mm)</text>
          <text class="form-hint">钢筋中心→截面顶边</text>
          <input class="form-input" v-model.number="form.a_s_prime" type="digit" placeholder="40" />
        </view>
      </view>
    </view>

    <!-- ========== 计算模式 ========== -->
    <view class="card">
      <view class="card-title">计算模式</view>
      <view class="type-toggle">
        <view class="type-btn" :class="{ active: mode === 'design' }" @click="mode = 'design'">设计模式</view>
        <view class="type-btn" :class="{ active: mode === 'check' }" @click="mode = 'check'">校核模式</view>
      </view>
      <view v-if="mode === 'check'" style="margin-top: 24rpx;">
        <view class="form-group">
          <text class="form-label">受拉钢筋面积 As (mm²)</text>
          <text class="form-hint">如 4Φ20 = 1256</text>
          <input class="form-input" v-model.number="form.as_given" type="digit" placeholder="1256" />
        </view>
        <view v-if="asType === 'double'" class="form-group">
          <text class="form-label">受压钢筋面积 As' (mm²)</text>
          <text class="form-hint">如 2Φ20 = 628</text>
          <input class="form-input" v-model.number="form.as_prime_given" type="digit" placeholder="628" />
        </view>
      </view>
    </view>

    <button class="btn-primary" @click="doCalculate" :disabled="loading">
      {{ loading ? '计算中...' : '开始计算' }}
    </button>

    <!-- ========== 结果 ========== -->
    <view class="card" v-if="result">
      <view class="calc-hero">
        <text class="calc-hero-label">{{ mode === 'check' ? '极限弯矩 Mᵤ' : '单筋最大承载力 Mᵤ,max' }}</text>
        <text class="calc-hero-value">{{ result.data.mu }}<text class="calc-hero-unit"> kN·m</text></text>
        <text class="status-tag" :class="statusClass">{{ result.message }}</text>
      </view>

      <view class="calc-process">
        <view class="calc-row">
          <text class="calc-key">材料参数</text>
          <text class="calc-val">fc = {{ result.data.fc }} MPa, fy = {{ result.data.fy }} MPa, α₁ = {{ result.data.alpha1 }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">有效高度</text>
          <text class="calc-val">h₀ = h − aₛ = {{ form.h }} − {{ form.a_s }} = {{ result.data.h0 }} mm</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">ξb</text>
          <text class="calc-val">{{ result.data.xi_b }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">ρmin / ρmax</text>
          <text class="calc-val">{{ result.data.rho_min }} / {{ result.data.rho_max }}</text>
        </view>
        <view class="calc-hr"></view>

        <!-- 校核模式 -->
        <template v-if="mode === 'check'">
          <view class="calc-row">
            <text class="calc-key">受压区高度</text>
            <text class="calc-val">x = {{ result.data.x }} mm, ξ = {{ result.data.xi }}</text>
          </view>
          <view class="calc-hr"></view>
        </template>

        <!-- ===== 配筋结果（设计模式）===== -->
        <template v-if="mode === 'design'">
          <!-- 单筋 -->
          <template v-if="asType === 'single'">
            <view class="calc-row">
              <text class="calc-key">配筋范围</text>
              <text class="calc-val">Aₛ,min = {{ asMin }} ～ Aₛ,max = {{ asMax }} mm²</text>
            </view>
            <view class="calc-hr"></view>

            <view class="calc-section-label">推荐配筋方案：</view>
            <view v-for="s in rebarSchemes" :key="s.label" class="calc-row">
              <text class="calc-key">{{ s.label }}</text>
              <text class="calc-val">{{ s.desc }}（As = {{ s.area }} mm²{{ s.note ? '，' + s.note : '' }}）</text>
            </view>
            <view class="calc-hr"></view>
          </template>

          <!-- 双筋 -->
          <template v-if="asType === 'double'">
            <view class="calc-row">
              <text class="calc-key">单筋上限</text>
              <text class="calc-val">Aₛ₁ = {{ result.data.as_req }} mm²（受拉），Mᵤ,max = {{ result.data.mu }} kN·m</text>
            </view>
            <view class="calc-hr"></view>
            <template v-if="result.data.design_points">
              <view class="calc-section-label">超出上限后需配双筋：</view>
              <view v-for="pt in result.data.design_points" :key="pt.label" class="calc-row">
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

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script>
import { calcBearingCapacity } from '@/utils/api.js'

// 常用钢筋组合
const REBAR_COMBOS = [
  { desc: '7Φ25', area: 3436 }, { desc: '8Φ22', area: 3040 }, { desc: '6Φ25', area: 2946 },
  { desc: '7Φ22', area: 2660 }, { desc: '5Φ25', area: 2454 }, { desc: '6Φ22', area: 2280 },
  { desc: '7Φ20', area: 2198 }, { desc: '4Φ25', area: 1964 }, { desc: '5Φ22', area: 1900 },
  { desc: '6Φ20', area: 1884 }, { desc: '7Φ18', area: 1780 }, { desc: '5Φ20', area: 1570 },
  { desc: '4Φ22', area: 1520 }, { desc: '3Φ25', area: 1473 }, { desc: '4Φ20', area: 1256 },
  { desc: '5Φ18', area: 1272 }, { desc: '3Φ22', area: 1140 }, { desc: '4Φ18', area: 1018 },
  { desc: '5Φ16', area: 1005 }, { desc: '3Φ20', area: 942 }, { desc: '4Φ16', area: 804 },
  { desc: '2Φ20', area: 628 }, { desc: '3Φ16', area: 603 }, { desc: '2Φ18', area: 509 },
  { desc: '3Φ14', area: 461 }, { desc: '2Φ16', area: 402 }, { desc: '2Φ14', area: 308 },
]
function findClosestRebar(target) {
  let best = REBAR_COMBOS[0]
  for (const c of REBAR_COMBOS) { if (Math.abs(c.area - target) < Math.abs(best.area - target)) best = c }
  return best
}

export default {
  data() {
    return {
      asType: 'single', mode: 'design',
      form: { b: 300, h: 600, concrete_grade: 'C30', rebar_grade: 'HRB400', a_s: 40, a_s_prime: 40, as_given: null, as_prime_given: null },
      concreteGrades: ['C25','C30','C35','C40','C45','C50','C55','C60','C65','C70','C75','C80'],
      rebarGrades: ['HPB300','HRB400','HRB500'],
      concreteIndex: 1, rebarIndex: 1,
      loading: false, result: null,
    }
  },
  computed: {
    asMin() { const d = this.result?.data; if (!d) return 0; return (d.rho_min * this.form.b * this.form.h).toFixed(1) },
    asMax() { const d = this.result?.data; if (!d) return 0; return (d.rho_max * this.form.b * d.h0).toFixed(1) },
    rebarSchemes() {
      const min = parseFloat(this.asMin), max = parseFloat(this.asMax)
      if (!min || !max) return []
      return [
        { label: '最小配筋', area: min },
        { label: '适中配筋', area: (min + max) / 2 },
        { label: '最大配筋', area: max },
      ].map(t => {
        const s = findClosestRebar(t.area)
        const diff = ((s.area - t.area) / t.area * 100)
        const note = diff >= 0 ? `超出 +${diff.toFixed(1)}%` : `不足 ${diff.toFixed(1)}%`
        return { ...t, ...s, note }
      })
    },
    statusClass() {
      if (!this.result) return ''
      const s = this.result.data.status
      if (s === 'ok') return 'status-ok'
      if (s === 'over_reinforced') return 'status-error'
      return 'status-warn'
    },
  },
  methods: {
    onConcreteChange(e) { this.concreteIndex = e.detail.value; this.form.concrete_grade = this.concreteGrades[e.detail.value] },
    onRebarChange(e) { this.rebarIndex = e.detail.value; this.form.rebar_grade = this.rebarGrades[e.detail.value] },
    async doCalculate() {
      if (!this.form.b || !this.form.h) { uni.showToast({ title: '请填写截面尺寸', icon: 'none' }); return }
      if (this.mode === 'check') {
        if (!this.form.as_given) { uni.showToast({ title: '校核模式请输入受拉钢筋面积 As', icon: 'none' }); return }
        if (this.asType === 'double' && !this.form.as_prime_given) { uni.showToast({ title: '双筋校核请输入受压钢筋面积 As\'', icon: 'none' }); return }
      }
      this.loading = true; this.result = null
      try {
        const p = { b: this.form.b, h: this.form.h, concrete_grade: this.form.concrete_grade, rebar_grade: this.form.rebar_grade, a_s: this.form.a_s, as_type: this.asType }
        if (this.asType === 'double') p.a_s_prime = this.form.a_s_prime
        if (this.mode === 'check') { p.as_given = this.form.as_given; if (this.asType === 'double') p.as_prime_given = this.form.as_prime_given }
        this.result = await calcBearingCapacity(p)
      } catch (e) { console.error('计算失败:', e) }
      finally { this.loading = false }
    },
  },
}
</script>

<style scoped>
.container { padding-bottom: 40rpx; }

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
.cad-bar-top, .cad-bar-bot {
  display: flex; align-items: center; gap: 12rpx;
  padding: 14rpx 16rpx;
}
.cad-dot {
  width: 16rpx; height: 16rpx; border-radius: 50%;
  background: #333; flex-shrink: 0;
}

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
