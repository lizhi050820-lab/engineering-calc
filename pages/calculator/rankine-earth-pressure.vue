<template>
  <view class="container">
    <view class="hero">
      <view class="hero-kicker">RANKINE EARTH PRESSURE</view>
      <view class="hero-title">朗肯土压力</view>
      <view class="hero-desc">按“类型 → 土层 → 水位”填写，得到压力分布、合力与作用点</view>
      <view class="mode-tabs">
        <view v-for="item in modes" :key="item.value" class="mode-tab"
          :class="{ active: form.mode === item.value }" @click="form.mode = item.value">
          {{ item.label }}
        </view>
      </view>
    </view>

    <view class="guide-strip">
      <view class="guide-dot"></view>
      <text>{{ modeHint }}</text>
    </view>

    <view class="card">
      <view class="card-head">
        <view>
          <view class="card-title">墙后土层</view>
          <view class="card-hint">从地表向下依次填写，最多 8 层</view>
        </view>
        <view class="layer-count">{{ form.layers.length }} 层</view>
      </view>

      <view v-for="(layer, index) in form.layers" :key="layer.id" class="layer-card">
        <view class="layer-head">
          <text class="layer-title">第 {{ index + 1 }} 层</text>
          <text v-if="form.layers.length > 1" class="remove-btn" @click="removeLayer(index)">删除</text>
        </view>
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">厚度 h (m)</text>
            <input class="form-input" type="digit" v-model="layer.h" placeholder="如 6" />
          </view>
          <view class="form-group">
            <text class="form-label">天然重度 γ (kN/m³)</text>
            <input class="form-input" type="digit" v-model="layer.gamma" placeholder="如 18" />
          </view>
          <view class="form-group">
            <text class="form-label">内摩擦角 φ (°)</text>
            <input class="form-input" type="digit" v-model="layer.phi" placeholder="如 30" />
          </view>
          <view class="form-group">
            <text class="form-label">黏聚力 c (kPa)</text>
            <input class="form-input" type="digit" v-model="layer.c" placeholder="砂土填 0" />
          </view>
          <view v-if="waterEnabled" class="form-group full">
            <text class="form-label">饱和重度 γₛₐₜ (kN/m³)</text>
            <input class="form-input" type="digit" v-model="layer.gamma_sat" placeholder="如 20" />
          </view>
        </view>
      </view>

      <view class="add-layer" @click="addLayer">＋ 添加一层土</view>
    </view>

    <view class="card">
      <view class="card-title">地表荷载与地下水</view>
      <view class="form-group">
        <text class="form-label">地面均布荷载 q (kPa)</text>
        <input class="form-input" type="digit" v-model="form.q" placeholder="无荷载填 0" />
      </view>

      <view class="switch-row" @click="waterEnabled = !waterEnabled">
        <view>
          <view class="switch-title">考虑地下水</view>
          <view class="switch-desc">开启后填写地下水位和各层饱和重度</view>
        </view>
        <switch color="#E9794A" :checked="waterEnabled" @change="waterEnabled = $event.detail.value" />
      </view>

      <template v-if="waterEnabled">
        <view class="grid-2 water-inputs">
          <view class="form-group">
            <text class="form-label">水位距地表 (m)</text>
            <input class="form-input" type="digit" v-model="form.water_table" placeholder="如 2" />
          </view>
          <view class="form-group">
            <text class="form-label">水的重度 γw</text>
            <input class="form-input" type="digit" v-model="form.gamma_w" placeholder="9.81" />
          </view>
        </view>
        <view class="water-tabs">
          <view class="water-tab" :class="{ active: form.water_method === 'separate' }"
            @click="form.water_method = 'separate'">水土分算</view>
          <view class="water-tab" :class="{ active: form.water_method === 'combined' }"
            @click="form.water_method = 'combined'">水土合算</view>
        </view>
        <view class="method-note">
          {{ form.water_method === 'separate'
            ? '土压力采用有效重度，孔隙水压力另行计算后叠加。通常用于砂土、粉土。'
            : '地下水以下采用饱和重度计算总土压力，不再单独叠加水压力。采用总应力强度指标时使用。' }}
        </view>
      </template>
    </view>

    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中…' : '开始计算' }}
    </button>

    <view v-if="result" class="card result-card">
      <view class="result-hero">
        <text class="result-label">总侧压力 E</text>
        <text class="result-value">{{ result.total_resultant }}<text class="result-unit"> kN/m</text></text>
        <text class="result-sub">作用点距墙底 {{ result.action_height }} m</text>
      </view>

      <view class="summary-grid">
        <view class="summary-item">
          <text class="summary-label">土压力合力</text>
          <text class="summary-value">{{ result.earth_resultant }} kN/m</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">水压力合力</text>
          <text class="summary-value">{{ result.water_resultant }} kN/m</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">墙高</text>
          <text class="summary-value">{{ result.total_height }} m</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">最大侧压力</text>
          <text class="summary-value">{{ result.max_pressure }} kPa</text>
        </view>
      </view>

      <view class="section-title">侧压力分布</view>
      <view class="pressure-chart">
        <view v-for="(segment, index) in result.segments" :key="index" class="pressure-segment">
          <view class="depth-label">{{ segment.z1 }}–{{ segment.z2 }} m</view>
          <view class="bar-area">
            <view class="pressure-bar" :style="{ width: barWidth(segment.p2) }"></view>
          </view>
          <view class="pressure-value">{{ segment.p1 }} → {{ segment.p2 }} kPa</view>
        </view>
      </view>

      <view class="section-title">分层系数</view>
      <view v-for="item in result.coefficients" :key="item.layer" class="coefficient-row">
        <text>第 {{ item.layer }} 层　φ={{ item.phi }}°</text>
        <text>K={{ item.K }}</text>
      </view>

      <view class="section-title">计算步骤</view>
      <view v-for="(step, index) in result.steps" :key="'s' + index" class="step-row">
        <view class="step-index">{{ index + 1 }}</view>
        <text class="step-text">{{ step }}</text>
      </view>
    </view>

    <view class="card source-card">
      <view class="card-title">计算依据与适用范围</view>
      <view class="source-line">经典朗肯理论：Kₐ = tan²(45°−φ/2)，Kₚ = tan²(45°+φ/2)，K₀ = 1−sinφ。</view>
      <view class="source-line">适用前提：墙背竖直、填土面水平、墙背光滑，按每延米墙长计算。</view>
      <view class="source-line warn">倾斜墙背、倾斜填土、墙土摩擦、地震作用及支护结构变形明显时，不应直接套用本结果。</view>
      <view class="source-ref">参考：GB 50007—2011 第6.7.3条；武汉理工大学《土压力》公开课件例题2。</view>
    </view>
  </view>
</template>

<script>
import { calcRankineEarthPressure } from '../../utils/api.js'

let nextLayerId = 3
const newLayer = (values = {}) => ({
  id: nextLayerId++,
  h: values.h ?? '',
  gamma: values.gamma ?? '18',
  gamma_sat: values.gamma_sat ?? '20',
  phi: values.phi ?? '30',
  c: values.c ?? '0'
})

export default {
  data() {
    return {
      loading: false,
      waterEnabled: false,
      result: null,
      modes: [
        { value: 'active', label: '主动' },
        { value: 'passive', label: '被动' },
        { value: 'at_rest', label: '静止' }
      ],
      form: {
        mode: 'active',
        q: '20',
        water_table: '2',
        water_method: 'separate',
        gamma_w: '9.81',
        layers: [
          { id: 1, h: '6', gamma: '18', gamma_sat: '20', phi: '30', c: '0' },
          { id: 2, h: '4', gamma: '20', gamma_sat: '21', phi: '35', c: '0' }
        ]
      }
    }
  },
  computed: {
    modeHint() {
      if (this.form.mode === 'active') return '墙体背离填土移动，土体达到主动极限平衡状态。'
      if (this.form.mode === 'passive') return '墙体挤向填土，需较大位移才能达到被动极限状态。'
      return '墙体基本不发生侧向位移，按静止土压力估算。'
    }
  },
  methods: {
    addLayer() {
      if (this.form.layers.length >= 8) return uni.showToast({ title: '最多支持 8 层土', icon: 'none' })
      this.form.layers.push(newLayer())
    },
    removeLayer(index) {
      if (this.form.layers.length > 1) this.form.layers.splice(index, 1)
    },
    number(value, label, allowZero = false) {
      const parsed = parseFloat(value)
      if (!Number.isFinite(parsed) || (allowZero ? parsed < 0 : parsed <= 0)) throw new Error(`请填写有效的${label}`)
      return parsed
    },
    async doCalculate() {
      try {
        const layers = this.form.layers.map((layer, index) => ({
          h: this.number(layer.h, `第${index + 1}层厚度`),
          gamma: this.number(layer.gamma, `第${index + 1}层天然重度`),
          gamma_sat: this.waterEnabled ? this.number(layer.gamma_sat, `第${index + 1}层饱和重度`) : undefined,
          phi: this.number(layer.phi, `第${index + 1}层内摩擦角`, true),
          c: this.number(layer.c || '0', `第${index + 1}层黏聚力`, true)
        }))
        const params = {
          mode: this.form.mode,
          q: this.number(this.form.q || '0', '地面均布荷载', true),
          water_method: this.form.water_method,
          gamma_w: this.number(this.form.gamma_w, '水的重度'),
          water_table: this.waterEnabled ? this.number(this.form.water_table, '地下水位', true) : null,
          layers
        }
        this.loading = true
        this.result = (await calcRankineEarthPressure(params)).data
      } catch (error) {
        uni.showToast({ title: error.message || '请检查输入参数', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    barWidth(value) {
      if (!this.result?.max_pressure) return '0%'
      return `${Math.max(2, value / this.result.max_pressure * 100).toFixed(1)}%`
    }
  }
}
</script>

<style scoped>
.container { padding-bottom: 44rpx; }
.hero { background:#123F43;color:#fff;padding:40rpx 28rpx 30rpx;border-radius:0 0 30rpx 30rpx; }
.hero-kicker { font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.45); }
.hero-title { font-size:46rpx;font-weight:780;margin-top:8rpx; }
.hero-desc { font-size:24rpx;line-height:1.6;color:rgba(255,255,255,.66);margin-top:8rpx; }
.mode-tabs { display:flex;gap:12rpx;margin-top:26rpx; }
.mode-tab { flex:1;text-align:center;padding:18rpx 8rpx;border:1rpx solid rgba(255,255,255,.2);border-radius:16rpx;font-size:26rpx;color:rgba(255,255,255,.72); }
.mode-tab.active { background:#F0784D;border-color:#F0784D;color:#fff;font-weight:700; }
.guide-strip { margin:20rpx 20rpx 0;padding:18rpx 20rpx;background:#DDEDEA;border-radius:16rpx;color:#356466;font-size:23rpx;display:flex;align-items:center;line-height:1.5; }
.guide-dot { width:12rpx;height:12rpx;border-radius:50%;background:#2A9B92;margin-right:14rpx;flex-shrink:0; }
.card { margin:20rpx;background:#FAF8F3;border-radius:24rpx;padding:26rpx;box-shadow:0 8rpx 26rpx rgba(18,63,67,.06); }
.card-head,.layer-head,.switch-row,.coefficient-row { display:flex;align-items:center;justify-content:space-between; }
.card-title { font-size:31rpx;font-weight:700;color:#17383A; }
.card-hint { font-size:22rpx;color:#8A9694;margin-top:5rpx; }
.layer-count { font-size:22rpx;color:#E16B42;background:#FFF0E8;padding:8rpx 16rpx;border-radius:99rpx; }
.layer-card { margin-top:22rpx;padding:22rpx;background:#F0F2EF;border-radius:18rpx;border-left:5rpx solid #2A9B92; }
.layer-title { font-size:26rpx;font-weight:700;color:#31585A; }
.remove-btn { font-size:22rpx;color:#C65B42;padding:8rpx; }
.grid-2 { display:grid;grid-template-columns:1fr 1fr;gap:18rpx;margin-top:18rpx; }
.form-group.full { grid-column:1 / -1; }
.form-label { display:block;font-size:23rpx;color:#526B6C;margin-bottom:8rpx; }
.form-input { height:74rpx;background:#FFF;border:1rpx solid #DDE3DF;border-radius:13rpx;padding:0 18rpx;font-size:28rpx;color:#17383A;box-sizing:border-box; }
.add-layer { margin-top:20rpx;padding:19rpx;text-align:center;border:2rpx dashed #8BB9B4;border-radius:16rpx;color:#21766F;font-size:25rpx; }
.switch-row { margin-top:22rpx;padding:20rpx 0;border-top:1rpx solid #E4E6E2; }
.switch-title { font-size:26rpx;font-weight:650;color:#17383A; }
.switch-desc { font-size:21rpx;color:#8A9694;margin-top:5rpx; }
.water-inputs { margin-top:5rpx; }
.water-tabs { display:flex;background:#E6EAE7;border-radius:14rpx;padding:5rpx;margin-top:20rpx; }
.water-tab { flex:1;text-align:center;padding:16rpx;font-size:24rpx;color:#667573;border-radius:11rpx; }
.water-tab.active { background:#14575B;color:#fff;font-weight:650; }
.method-note { margin-top:14rpx;padding:17rpx;background:#E5F1EF;border-radius:13rpx;font-size:22rpx;line-height:1.6;color:#3F6868; }
.btn-primary { margin:24rpx 20rpx 0;background:#F0784D;color:#fff;border-radius:18rpx;font-size:31rpx;font-weight:700;box-shadow:0 10rpx 24rpx rgba(240,120,77,.25); }
.result-card { padding:0 26rpx 28rpx;overflow:hidden; }
.result-hero { margin:0 -26rpx;padding:30rpx;text-align:center;background:#123F43;color:#fff; }
.result-label,.result-sub { display:block;font-size:23rpx;color:rgba(255,255,255,.66); }
.result-value { display:block;font-size:58rpx;font-weight:800;margin:8rpx 0; }
.result-unit { font-size:26rpx;font-weight:500; }
.summary-grid { display:grid;grid-template-columns:1fr 1fr;gap:12rpx;margin-top:22rpx; }
.summary-item { background:#EFF2EF;border-radius:14rpx;padding:18rpx; }
.summary-label { display:block;font-size:21rpx;color:#84908E; }
.summary-value { display:block;font-size:27rpx;font-weight:700;color:#17383A;margin-top:6rpx; }
.section-title { font-size:27rpx;font-weight:700;color:#17383A;margin:28rpx 0 14rpx;padding-left:13rpx;border-left:5rpx solid #F0784D; }
.pressure-segment { display:grid;grid-template-columns:120rpx 1fr 190rpx;gap:10rpx;align-items:center;margin:12rpx 0; }
.depth-label,.pressure-value { font-size:20rpx;color:#73817F; }
.pressure-value { text-align:right; }
.bar-area { height:18rpx;background:#E4E9E6;border-radius:99rpx;overflow:hidden; }
.pressure-bar { height:100%;background:linear-gradient(90deg,#2A9B92,#F0784D);border-radius:99rpx; }
.coefficient-row { padding:14rpx 4rpx;border-bottom:1rpx solid #E7E8E5;font-size:24rpx;color:#496364; }
.step-row { display:flex;align-items:flex-start;margin:14rpx 0; }
.step-index { width:36rpx;height:36rpx;border-radius:50%;background:#DCECEA;color:#146C67;font-size:20rpx;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-right:14rpx; }
.step-text { flex:1;font-size:24rpx;line-height:1.65;color:#40595A; }
.source-line { font-size:23rpx;color:#546765;line-height:1.7;margin-top:12rpx; }
.source-line.warn { color:#9A542F;background:#FFF0E7;padding:14rpx;border-radius:12rpx; }
.source-ref { margin-top:16rpx;font-size:20rpx;color:#929C9A;line-height:1.6; }
</style>
