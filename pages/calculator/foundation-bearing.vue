<template>
  <view class="container">
    <view class="hero">
      <view class="hero-kicker">FOUNDATION BEARING</view>
      <view class="hero-title">地基承载力验算</view>
      <view class="hero-desc">按“承载力 → 基础 → 荷载”填写，快速判断平均压力、边缘压力和基底脱空</view>
    </view>

    <view class="guide-strip"><view class="guide-dot"></view><text>{{ guideText }}</text></view>

    <view class="card">
      <view class="card-title">① 持力层与承载力</view>
      <view class="form-group full">
        <text class="form-label">持力层土类别（GB 50007 表5.2.4）</text>
        <picker :range="soilLabels" :value="soilIndex" @change="changeSoil">
          <view class="picker-box">{{ soilOptions[soilIndex].label }}<text>⌄</text></view>
        </picker>
      </view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">fₐₖ (kPa)</text>
          <input class="form-input" type="digit" v-model="form.fak" placeholder="如 180" />
        </view>
        <view class="form-group">
          <text class="form-label">埋深 d (m)</text>
          <input class="form-input" type="digit" v-model="form.d" placeholder="如 1.6" />
        </view>
        <view class="form-group">
          <text class="form-label">基底以下 γ (kN/m³)</text>
          <input class="form-input" type="digit" v-model="form.gamma" placeholder="地下水下取浮重度" />
        </view>
        <view class="form-group">
          <text class="form-label">基底以上 γm (kN/m³)</text>
          <input class="form-input" type="digit" v-model="form.gamma_m" placeholder="加权平均重度" />
        </view>
        <template v-if="form.soil_category === 'custom'">
          <view class="form-group">
            <text class="form-label">宽度修正 ηb</text>
            <input class="form-input" type="digit" v-model="form.eta_b" />
          </view>
          <view class="form-group">
            <text class="form-label">深度修正 ηd</text>
            <input class="form-input" type="digit" v-model="form.eta_d" />
          </view>
        </template>
      </view>
      <view class="method-note">fₐₖ 必须来自勘察、载荷试验、原位测试或当地工程经验，本页只做规范宽深修正与压力验算。</view>
    </view>

    <view class="card">
      <view class="card-title">② 矩形基础</view>
      <view class="foundation-sketch">
        <view class="sketch-base"><text>l</text><view class="sketch-arrow">Mᵧ → b</view></view>
        <view class="sketch-note">Mₓ 沿 l 方向改变压力，Mᵧ 沿 b 方向改变压力</view>
      </view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">宽度 b (m)</text>
          <input class="form-input" type="digit" v-model="form.b" />
        </view>
        <view class="form-group">
          <text class="form-label">长度 l (m)</text>
          <input class="form-input" type="digit" v-model="form.l" />
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head">
        <view>
          <view class="card-title">③ 标准组合荷载</view>
          <view class="card-hint">弯矩填写基础底面形心处数值，正负号不影响最大值验算</view>
        </view>
      </view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">上部竖向力 Fₖ (kN)</text>
          <input class="form-input" type="digit" v-model="form.Fk" />
        </view>
        <view class="form-group">
          <text class="form-label">Mₓ (kN·m)</text>
          <input class="form-input" type="digit" v-model="form.Mx" />
        </view>
        <view class="form-group">
          <text class="form-label">Mᵧ (kN·m)</text>
          <input class="form-input" type="digit" v-model="form.My" />
        </view>
      </view>

      <view class="weight-tabs">
        <view class="weight-tab" :class="{ active: weightMode === 'auto' }" @click="weightMode = 'auto'">自动估算 Gₖ</view>
        <view class="weight-tab" :class="{ active: weightMode === 'manual' }" @click="weightMode = 'manual'">手动输入 Gₖ</view>
      </view>
      <view class="form-group weight-input">
        <text class="form-label">{{ weightMode === 'auto' ? '单位面积基础及覆土重 (kPa)' : '基础及覆土重 Gₖ (kN)' }}</text>
        <input v-if="weightMode === 'auto'" class="form-input" type="digit" v-model="form.foundation_weight_pressure" />
        <input v-else class="form-input" type="digit" v-model="form.Gk" />
      </view>
    </view>

    <button class="btn-primary" :disabled="loading" @click="doCalculate">{{ loading ? '计算中…' : '开始验算' }}</button>

    <view v-if="result" class="card result-card">
      <view class="result-hero" :class="{ fail: !result.overall_pass, review: result.pressure_mode === 'biaxial_separation_review' }">
        <text class="result-label">验算结论</text>
        <text class="result-value">{{ resultTitle }}</text>
        <text class="result-sub">平均压力利用率 {{ percent(result.mean_utilization) }}</text>
      </view>

      <view class="check-list">
        <view class="check-row" :class="{ bad: !result.mean_pass }">
          <text>平均压力</text><text>pₖ={{ result.pk }} {{ result.mean_pass ? '≤' : '＞' }} fₐ={{ result.fa }} kPa</text>
        </view>
        <view class="check-row" :class="{ bad: result.edge_pass === false, review: result.edge_pass === null }">
          <text>边缘压力</text>
          <text v-if="result.edge_pass !== null">pₖ,max={{ result.pmax }} {{ result.edge_pass ? '≤' : '＞' }} {{ onePointTwoFa }} kPa</text>
          <text v-else>需要专项复核</text>
        </view>
        <view class="check-row" :class="{ bad: !result.stable, review: !result.supported && result.stable }">
          <text>基底接触</text><text>{{ contactText }}</text>
        </view>
      </view>

      <view class="summary-grid">
        <view class="summary-item"><text class="summary-label">修正后 fₐ</text><text class="summary-value">{{ result.fa }} kPa</text></view>
        <view class="summary-item"><text class="summary-label">平均 pₖ</text><text class="summary-value">{{ result.pk }} kPa</text></view>
        <view class="summary-item"><text class="summary-label">最大 pₖ,max</text><text class="summary-value">{{ result.pmax ?? '—' }} kPa</text></view>
        <view class="summary-item"><text class="summary-label">最小 pₖ,min</text><text class="summary-value">{{ result.pmin ?? '—' }} kPa</text></view>
      </view>

      <view class="section-title">基底压力示意</view>
      <view class="pressure-box">
        <view class="corner"><text>左上</text><strong>{{ result.corners.top_left }}</strong></view>
        <view class="corner right"><text>右上</text><strong>{{ result.corners.top_right }}</strong></view>
        <view class="corner bottom"><text>左下</text><strong>{{ result.corners.bottom_left }}</strong></view>
        <view class="corner right bottom"><text>右下</text><strong>{{ result.corners.bottom_right }}</strong></view>
        <view class="pressure-center">kPa</view>
      </view>
      <view v-if="result.pressure_mode === 'uniaxial_triangular_contact'" class="result-note">
        单向大偏心采用三角形接触压力，受压宽度 3a={{ result.contact_width }} m。
      </view>
      <view v-if="result.pressure_mode === 'biaxial_separation_review'" class="result-note warn">
        双向偏心已有角点拉应力，线性角点数值仅用于识别脱空，不能作为真实接触压力。
      </view>

      <view class="section-title">计算步骤</view>
      <view v-for="(step, index) in result.steps" :key="index" class="step-row">
        <view class="step-index">{{ index + 1 }}</view><text class="step-text">{{ step }}</text>
      </view>
    </view>

    <view class="card source-card">
      <view class="card-title">依据与适用范围</view>
      <view class="source-line">GB 50007—2011 第5.2.1、5.2.2、5.2.4条。</view>
      <view class="source-line">fₐ = fₐₖ＋ηbγ(b－3)＋ηdγm(d－0.5)，宽度修正取 3～6 m。</view>
      <view class="source-line warn">结果不包含沉降、软弱下卧层、抗滑、抗倾覆、冲切和配筋；正式工程仍须由专业人员结合勘察报告复核。</view>
      <view class="source-ref">固定算例：江苏建筑职业技术学院公开独立基础计算书，第6～7页。</view>
    </view>
  </view>
</template>

<script>
import { calcFoundationBearing } from '../../utils/api.js'
import { SOIL_CORRECTION_PRESETS } from '../../utils/calculators/foundation-bearing.js'

export default {
  data() {
    const soilOptions = Object.entries(SOIL_CORRECTION_PRESETS).map(([value, item]) => ({ value, ...item }))
    return {
      loading: false,
      result: null,
      weightMode: 'manual',
      soilOptions,
      soilIndex: soilOptions.findIndex(item => item.value === 'cohesive_firm'),
      form: {
        b: '1.7', l: '1.7', d: '1.6', fak: '180',
        gamma: '20', gamma_m: '20', soil_category: 'cohesive_firm',
        eta_b: '0.3', eta_d: '1.6',
        Fk: '72.8', Gk: '69.36', foundation_weight_pressure: '20',
        Mx: '4.78', My: '28.81'
      }
    }
  },
  computed: {
    soilLabels() { return this.soilOptions.map(item => item.label) },
    guideText() {
      if (!this.result) return '先确认 fₐₖ 的勘察来源，再输入基础尺寸和标准组合荷载。'
      if (this.result.pressure_mode === 'biaxial_separation_review') return '已识别双向偏心脱空，本页不会继续给出虚假的最大接触压力。'
      return this.result.overall_pass ? '当前三个检查项均满足，仍需另做沉降等完整验算。' : '请先查看红色检查项，不能只看修正后的承载力。'
    },
    resultTitle() {
      if (!this.result) return ''
      if (this.result.pressure_mode === 'biaxial_separation_review') return '需专项复核'
      if (!this.result.stable) return '存在失稳风险'
      return this.result.overall_pass ? '承载力满足' : '承载力不满足'
    },
    contactText() {
      if (!this.result) return ''
      if (!this.result.stable) return '合力作用线超出基础'
      if (this.result.pressure_mode === 'biaxial_separation_review') return '双向偏心脱空'
      if (this.result.full_contact) return '全截面受压'
      return '单向部分受压'
    },
    onePointTwoFa() { return this.result ? (this.result.fa * 1.2).toFixed(3) : '0.000' }
  },
  methods: {
    changeSoil(event) {
      this.soilIndex = Number(event.detail.value)
      const selected = this.soilOptions[this.soilIndex]
      this.form.soil_category = selected.value
      if (selected.value !== 'custom') {
        this.form.eta_b = String(selected.eta_b)
        this.form.eta_d = String(selected.eta_d)
      }
      this.result = null
    },
    number(value, label, allowZero = false) {
      const parsed = parseFloat(value)
      if (!Number.isFinite(parsed) || (allowZero ? parsed < 0 : parsed <= 0)) throw new Error(`请填写有效的${label}`)
      return parsed
    },
    signed(value, label) {
      const parsed = parseFloat(value || '0')
      if (!Number.isFinite(parsed)) throw new Error(`请填写有效的${label}`)
      return parsed
    },
    percent(value) { return `${(value * 100).toFixed(1)}%` },
    async doCalculate() {
      try {
        const params = {
          b: this.number(this.form.b, '基础宽度'),
          l: this.number(this.form.l, '基础长度'),
          d: this.number(this.form.d, '基础埋深', true),
          fak: this.number(this.form.fak, 'fak'),
          gamma: this.number(this.form.gamma, '基底以下土重度'),
          gamma_m: this.number(this.form.gamma_m, '基底以上平均重度'),
          soil_category: this.form.soil_category,
          Fk: this.number(this.form.Fk, '竖向力 Fk', true),
          Mx: this.signed(this.form.Mx, 'Mx'),
          My: this.signed(this.form.My, 'My')
        }
        if (this.form.soil_category === 'custom') {
          params.eta_b = this.number(this.form.eta_b, 'ηb', true)
          params.eta_d = this.number(this.form.eta_d, 'ηd', true)
        }
        if (this.weightMode === 'manual') params.Gk = this.number(this.form.Gk, 'Gk', true)
        else params.foundation_weight_pressure = this.number(this.form.foundation_weight_pressure, '单位面积基础及覆土重')
        this.loading = true
        const response = await calcFoundationBearing(params)
        this.result = response.data
        this.$nextTick(() => uni.pageScrollTo({ selector: '.result-card', duration: 300 }))
      } catch (error) {
        uni.showToast({ title: error?.data?.detail || error.message || '计算失败', icon: 'none', duration: 3000 })
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.container{min-height:100vh;background:#EEF1EF;padding-bottom:54rpx;color:#17383A}.hero{background:#123F43;color:#fff;padding:46rpx 32rpx 34rpx;border-radius:0 0 30rpx 30rpx}.hero-kicker{font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.45)}.hero-title{font-size:43rpx;font-weight:760;margin-top:10rpx}.hero-desc{font-size:23rpx;color:rgba(255,255,255,.66);line-height:1.6;margin-top:9rpx}.guide-strip{margin:18rpx 20rpx 0;padding:17rpx 20rpx;background:#DCEEEB;border-radius:14rpx;font-size:22rpx;line-height:1.6;color:#356765;display:flex}.guide-dot{width:13rpx;height:13rpx;border-radius:50%;background:#2A9B92;margin:9rpx 12rpx 0 0;flex-shrink:0}.card{margin:20rpx 20rpx 0;background:#FAF8F3;border-radius:22rpx;padding:26rpx;box-shadow:0 8rpx 24rpx rgba(18,63,67,.05)}.card-title{font-size:29rpx;font-weight:730;color:#17383A}.card-hint{font-size:20rpx;color:#8B9693;margin-top:5rpx}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:18rpx;margin-top:20rpx}.form-group.full{margin-top:20rpx}.form-label{display:block;font-size:22rpx;color:#526B6C;margin-bottom:8rpx;line-height:1.4}.form-input,.picker-box{height:74rpx;background:#fff;border:1rpx solid #DDE3DF;border-radius:13rpx;padding:0 18rpx;font-size:27rpx;color:#17383A;box-sizing:border-box}.picker-box{display:flex;align-items:center;justify-content:space-between}.method-note{margin-top:20rpx;padding:16rpx;background:#E4F0EE;border-radius:13rpx;font-size:21rpx;line-height:1.65;color:#416867}.foundation-sketch{margin-top:20rpx;padding:20rpx;background:#E8EFEC;border-radius:16rpx}.sketch-base{width:70%;height:90rpx;margin:auto;border:4rpx solid #2B716E;transform:skewY(-4deg);display:flex;align-items:center;justify-content:space-between;padding:0 18rpx;box-sizing:border-box;color:#215B59;font-weight:700}.sketch-arrow{font-size:21rpx}.sketch-note{text-align:center;font-size:19rpx;color:#798886;margin-top:18rpx}.weight-tabs{display:flex;background:#E6EAE7;border-radius:14rpx;padding:5rpx;margin-top:24rpx}.weight-tab{flex:1;text-align:center;padding:15rpx;font-size:23rpx;color:#667573;border-radius:11rpx}.weight-tab.active{background:#14575B;color:#fff;font-weight:650}.weight-input{margin-top:18rpx}.btn-primary{margin:24rpx 20rpx 0;background:#F0784D;color:#fff;border-radius:18rpx;font-size:30rpx;font-weight:700;box-shadow:0 10rpx 24rpx rgba(240,120,77,.25)}.result-card{padding:0 26rpx 28rpx;overflow:hidden}.result-hero{margin:0 -26rpx;padding:29rpx;text-align:center;background:#176B63;color:#fff}.result-hero.fail{background:#A5523E}.result-hero.review{background:#9A6A33}.result-label,.result-sub{display:block;font-size:22rpx;color:rgba(255,255,255,.7)}.result-value{display:block;font-size:42rpx;font-weight:800;margin:8rpx}.check-list{margin-top:20rpx}.check-row{display:flex;justify-content:space-between;gap:15rpx;padding:15rpx;border-radius:12rpx;margin-bottom:9rpx;background:#E5F1EB;color:#286052;font-size:22rpx}.check-row.bad{background:#FCE5DF;color:#9A4434}.check-row.review{background:#FFF0D7;color:#896025}.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:12rpx;margin-top:20rpx}.summary-item{background:#EFF2EF;border-radius:14rpx;padding:17rpx}.summary-label{display:block;font-size:20rpx;color:#84908E}.summary-value{display:block;font-size:26rpx;font-weight:700;color:#17383A;margin-top:6rpx}.section-title{font-size:27rpx;font-weight:700;margin:28rpx 0 14rpx;padding-left:13rpx;border-left:5rpx solid #F0784D}.pressure-box{position:relative;height:220rpx;border:3rpx solid #276D69;border-radius:12rpx;background:linear-gradient(135deg,#DCEDEA,#F7E4D8);display:grid;grid-template-columns:1fr 1fr}.corner{padding:18rpx;display:flex;flex-direction:column;font-size:19rpx;color:#6C7E7B}.corner.right{text-align:right}.corner.bottom{justify-content:flex-end}.corner strong{font-size:27rpx;color:#174A4B;margin-top:4rpx}.pressure-center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);padding:8rpx 13rpx;background:#fff;border-radius:20rpx;color:#7A8986;font-size:20rpx}.result-note{margin-top:14rpx;padding:15rpx;background:#E4F0EE;border-radius:12rpx;font-size:21rpx;color:#416867}.result-note.warn{background:#FFF0E4;color:#91543A}.step-row{display:flex;align-items:flex-start;margin:14rpx 0}.step-index{width:36rpx;height:36rpx;border-radius:50%;background:#DCECEA;color:#146C67;font-size:20rpx;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-right:14rpx}.step-text{flex:1;font-size:23rpx;line-height:1.65;color:#40595A}.source-line{font-size:22rpx;color:#546765;line-height:1.7;margin-top:12rpx}.source-line.warn{color:#9A542F;background:#FFF0E7;padding:14rpx;border-radius:12rpx}.source-ref{margin-top:16rpx;font-size:19rpx;color:#929C9A;line-height:1.6}
</style>
