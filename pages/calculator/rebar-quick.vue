<template>
  <view class="container">
    <view class="hero">
      <view class="hero-kicker">REBAR QUICK CALCULATOR</view>
      <view class="hero-title">钢筋工程速算</view>
      <view class="hero-desc">查表、互算、排布与代换，结果按步骤清晰复核</view>
      <view class="mode-grid">
        <view v-for="item in operations" :key="item.value" class="mode-item"
          :class="{ active: form.operation === item.value }" @click="selectOperation(item.value)">
          <text class="mode-name">{{ item.label }}</text>
          <text class="mode-desc">{{ item.short }}</text>
        </view>
      </view>
    </view>

    <view class="guide-strip">
      <view class="guide-dot"></view>
      <text>{{ operationHint }}</text>
    </view>

    <view class="card">
      <view class="card-title">{{ form.operation === 'equivalent' ? '选择原配筋与替换规格' : '选择钢筋规格' }}</view>

      <template v-if="form.operation !== 'equivalent'">
        <view class="field-label">公称直径 d (mm)</view>
        <scroll-view scroll-x class="diameter-scroll" :show-scrollbar="false">
          <view class="diameter-row">
            <view v-for="item in diameters" :key="item" class="diameter-chip"
              :class="{ active: form.diameter === item }" @click="form.diameter = item; result = null">
              Φ{{ item }}
            </view>
          </view>
        </scroll-view>
        <view class="lookup-strip">
          <view><text class="lookup-label">公称面积</text><text class="lookup-value">{{ selectedBar.area }} mm²</text></view>
          <view><text class="lookup-label">理论重量</text><text class="lookup-value">{{ weightText(selectedBar.unit_weight) }} kg/m</text></view>
        </view>
      </template>

      <template v-else>
        <view class="field-label">原钢筋直径</view>
        <scroll-view scroll-x class="diameter-scroll" :show-scrollbar="false">
          <view class="diameter-row">
            <view v-for="item in diameters" :key="'s' + item" class="diameter-chip"
              :class="{ active: form.source_diameter === item }" @click="form.source_diameter = item; result = null">
              Φ{{ item }}
            </view>
          </view>
        </scroll-view>
        <view class="field-label second-label">替换钢筋直径</view>
        <scroll-view scroll-x class="diameter-scroll" :show-scrollbar="false">
          <view class="diameter-row">
            <view v-for="item in diameters" :key="'t' + item" class="diameter-chip"
              :class="{ active: form.target_diameter === item }" @click="form.target_diameter = item; result = null">
              Φ{{ item }}
            </view>
          </view>
        </scroll-view>
      </template>
    </view>

    <view class="card">
      <view class="card-title">填写计算参数</view>
      <view v-if="form.operation === 'quantity'" class="grid-2">
        <view class="form-group">
          <text class="form-label">单根长度 (m)</text>
          <input class="form-input" type="digit" v-model="form.bar_length" placeholder="如 6" />
        </view>
        <view class="form-group">
          <text class="form-label">钢筋根数</text>
          <input class="form-input" type="number" v-model="form.bar_count" placeholder="如 25" />
        </view>
      </view>

      <view v-else-if="form.operation === 'weight_to_length'" class="form-group">
        <text class="form-label">钢筋总重量 (kg)</text>
        <input class="form-input" type="digit" v-model="form.total_weight" placeholder="如 1000" />
      </view>

      <view v-else-if="form.operation === 'spacing'" class="grid-2">
        <view class="form-group">
          <text class="form-label">首末筋中心布置长度 (mm)</text>
          <input class="form-input" type="digit" v-model="form.layout_length" placeholder="如 5100" />
        </view>
        <view class="form-group">
          <text class="form-label">允许最大间距 (mm)</text>
          <input class="form-input" type="digit" v-model="form.max_spacing" placeholder="如 200" />
        </view>
        <view class="form-group full">
          <text class="form-label">每根钢筋长度 (m)</text>
          <input class="form-input" type="digit" v-model="form.bar_length" placeholder="如 6" />
        </view>
      </view>

      <view v-else class="form-group">
        <text class="form-label">原钢筋根数</text>
        <input class="form-input" type="number" v-model="form.source_count" placeholder="如 4" />
      </view>

      <view v-if="form.operation === 'spacing'" class="input-note">
        布置长度指第一根与最后一根钢筋中心之间的距离；程序按“间距不得大于输入值”向上取整间隔数。
      </view>
    </view>

    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中…' : '开始计算' }}
    </button>

    <view v-if="result" class="card result-card">
      <view class="result-head">
        <view>
          <view class="result-kicker">{{ resultTitle }}</view>
          <view class="result-main">{{ resultMain }}</view>
        </view>
        <view class="result-badge">已查表</view>
      </view>

      <view class="summary-grid">
        <view v-if="result.total_length !== null" class="summary-item">
          <text class="summary-label">总长度</text>
          <text class="summary-value">{{ fixed(result.total_length, 3) }} m</text>
        </view>
        <view v-if="result.total_weight !== null" class="summary-item">
          <text class="summary-label">总重量</text>
          <text class="summary-value">{{ fixed(result.total_weight, 3) }} kg</text>
        </view>
        <view v-if="result.bar_count !== null && form.operation !== 'equivalent'" class="summary-item">
          <text class="summary-label">钢筋根数</text>
          <text class="summary-value">{{ result.bar_count }} 根</text>
        </view>
        <view v-if="result.actual_spacing !== null" class="summary-item">
          <text class="summary-label">实际间距</text>
          <text class="summary-value">{{ fixed(result.actual_spacing, 3) }} mm</text>
        </view>
        <view v-if="result.source_area !== null" class="summary-item">
          <text class="summary-label">原配筋面积</text>
          <text class="summary-value">{{ fixed(result.source_area, 1) }} mm²</text>
        </view>
        <view v-if="result.replacement_area !== null" class="summary-item">
          <text class="summary-label">替换后面积</text>
          <text class="summary-value">{{ fixed(result.replacement_area, 1) }} mm²</text>
        </view>
      </view>

      <view class="section-title">计算步骤</view>
      <view v-for="(step, index) in result.steps" :key="index" class="step-row">
        <view class="step-index">{{ index + 1 }}</view>
        <text class="step-text">{{ step }}</text>
      </view>
    </view>

    <view class="card source-card">
      <view class="card-title">依据与使用边界</view>
      <view class="source-line">公称面积和理论单位重量采用 GB 1499.1—2024、GB 1499.2—2024 表2，理论重量按钢密度 7.85 g/cm³确定。</view>
      <view class="source-line">理论重量用于快速估算，进场验收、结算和重量偏差判断应以合同、实测重量及相应标准为准。</view>
      <view class="source-line warn">等面积代换不等于设计变更；还必须复核钢筋间距、净距、锚固、搭接、裂缝、最小配筋和构造要求。</view>
    </view>
  </view>
</template>

<script>
import { calcRebarQuick } from '../../utils/api.js'
import { STANDARD_REBARS } from '../../utils/calculators/rebar-quick.js'

export default {
  data() {
    return {
      loading: false,
      result: null,
      operations: [
        { value: 'quantity', label: '用量', short: '长度×根数' },
        { value: 'weight_to_length', label: '反算', short: '重量→长度' },
        { value: 'spacing', label: '排布', short: '间距→根数' },
        { value: 'equivalent', label: '代换', short: '等面积' }
      ],
      diameters: STANDARD_REBARS.map(item => item.diameter),
      form: {
        operation: 'quantity',
        diameter: 16,
        bar_length: '6',
        bar_count: '25',
        total_weight: '1000',
        layout_length: '5100',
        max_spacing: '200',
        source_diameter: 20,
        source_count: '4',
        target_diameter: 18
      }
    }
  },
  computed: {
    selectedBar() {
      return STANDARD_REBARS.find(item => item.diameter === this.form.diameter)
    },
    operationHint() {
      const hints = {
        quantity: '适合下料单、现场盘点和材料计划的理论重量估算。',
        weight_to_length: '把已知重量换算为该规格钢筋的等效总长度。',
        spacing: '按最大允许间距计算所需根数，保证实际间距不超限。',
        equivalent: '只做公称截面面积比较，设计与构造条件仍须单独复核。'
      }
      return hints[this.form.operation]
    },
    resultTitle() {
      return this.form.operation === 'equivalent' ? '建议替换方案' : '计算结果'
    },
    resultMain() {
      if (!this.result) return ''
      if (this.form.operation === 'weight_to_length') return `${this.fixed(this.result.total_length, 3)} m`
      if (this.form.operation === 'equivalent') return `${this.result.required_count} 根 Φ${this.result.diameter}`
      if (this.form.operation === 'spacing') return `${this.result.bar_count} 根 @ ${this.fixed(this.result.actual_spacing, 3)}`
      return `${this.fixed(this.result.total_weight, 3)} kg`
    }
  },
  methods: {
    selectOperation(value) {
      this.form.operation = value
      this.result = null
    },
    fixed(value, digits) {
      return Number(value).toFixed(digits)
    },
    weightText(value) {
      return Number(value).toFixed(3)
    },
    number(value) {
      const parsed = parseFloat(value)
      return Number.isFinite(parsed) ? parsed : value
    },
    async doCalculate() {
      try {
        const params = { operation: this.form.operation }
        if (this.form.operation === 'equivalent') {
          Object.assign(params, {
            source_diameter: this.form.source_diameter,
            source_count: this.number(this.form.source_count),
            target_diameter: this.form.target_diameter
          })
        } else {
          params.diameter = this.form.diameter
          if (this.form.operation === 'quantity') {
            params.bar_length = this.number(this.form.bar_length)
            params.bar_count = this.number(this.form.bar_count)
          } else if (this.form.operation === 'weight_to_length') {
            params.total_weight = this.number(this.form.total_weight)
          } else {
            params.layout_length = this.number(this.form.layout_length)
            params.max_spacing = this.number(this.form.max_spacing)
            params.bar_length = this.number(this.form.bar_length)
          }
        }
        this.loading = true
        this.result = (await calcRebarQuick(params)).data
      } catch (error) {
        uni.showToast({ title: error.message || '请检查输入参数', icon: 'none' })
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.container{padding-bottom:44rpx}.hero{background:#123F43;color:#fff;padding:40rpx 28rpx 30rpx;border-radius:0 0 30rpx 30rpx}.hero-kicker{font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.45)}.hero-title{font-size:46rpx;font-weight:780;margin-top:8rpx}.hero-desc{font-size:24rpx;line-height:1.6;color:rgba(255,255,255,.66);margin-top:8rpx}.mode-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12rpx;margin-top:26rpx}.mode-item{display:flex;flex-direction:column;padding:18rpx 20rpx;border:1rpx solid rgba(255,255,255,.15);border-radius:16rpx;background:rgba(255,255,255,.04)}.mode-item.active{border-color:#E9794A;background:rgba(233,121,74,.16)}.mode-name{font-size:27rpx;font-weight:700}.mode-desc{font-size:19rpx;color:rgba(255,255,255,.55);margin-top:4rpx}.guide-strip{display:flex;align-items:center;margin:18rpx 20rpx 0;padding:17rpx 20rpx;border-radius:16rpx;background:#DDEFEA;color:#366664;font-size:22rpx;line-height:1.5}.guide-dot{width:12rpx;height:12rpx;border-radius:50%;background:#2C8884;margin-right:14rpx;flex-shrink:0}.card{margin:18rpx 20rpx 0;background:#FAF8F3;border-radius:22rpx;padding:28rpx;box-shadow:0 8rpx 24rpx rgba(18,63,67,.055)}.card-title{font-size:30rpx;font-weight:720;color:#17383A;margin-bottom:22rpx}.field-label,.form-label{font-size:22rpx;color:#667573}.second-label{margin-top:24rpx}.diameter-scroll{width:100%;white-space:nowrap;margin-top:12rpx}.diameter-row{display:inline-flex;gap:10rpx;padding-right:24rpx}.diameter-chip{min-width:72rpx;text-align:center;padding:14rpx 10rpx;border-radius:13rpx;background:#E9ECE8;color:#5F6D6B;font-size:23rpx}.diameter-chip.active{background:#14575B;color:#fff;font-weight:700}.lookup-strip{display:grid;grid-template-columns:1fr 1fr;gap:14rpx;margin-top:22rpx}.lookup-strip>view{display:flex;flex-direction:column;padding:18rpx;border-radius:15rpx;background:#EEF2EF}.lookup-label{font-size:20rpx;color:#7B8785}.lookup-value{font-size:27rpx;color:#17383A;font-weight:700;margin-top:5rpx}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16rpx}.full{grid-column:1/-1}.form-group{min-width:0}.form-input{height:82rpx;background:#F0F1ED;border:1rpx solid #E1E4DF;border-radius:15rpx;padding:0 20rpx;margin-top:10rpx;font-size:30rpx;color:#17383A}.input-note{font-size:21rpx;line-height:1.6;color:#7D8987;margin-top:18rpx;padding:15rpx 17rpx;background:#F3EEE5;border-radius:14rpx}.btn-primary{margin:20rpx 20rpx 0;background:#E9794A;color:#fff;border-radius:18rpx;height:92rpx;line-height:92rpx;font-size:30rpx;font-weight:700;box-shadow:0 10rpx 22rpx rgba(233,121,74,.24)}.result-card{border-top:6rpx solid #2C8884}.result-head{display:flex;justify-content:space-between;align-items:flex-start}.result-kicker{font-size:21rpx;color:#788684}.result-main{font-size:42rpx;color:#14575B;font-weight:800;margin-top:8rpx}.result-badge{font-size:19rpx;color:#2C7773;background:#DDEFEA;padding:8rpx 14rpx;border-radius:20rpx}.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:12rpx;margin-top:24rpx}.summary-item{display:flex;flex-direction:column;padding:17rpx;background:#EEF2EF;border-radius:14rpx}.summary-label{font-size:20rpx;color:#7B8785}.summary-value{font-size:26rpx;color:#17383A;font-weight:680;margin-top:5rpx}.section-title{font-size:27rpx;font-weight:700;color:#17383A;margin:28rpx 0 14rpx}.step-row{display:flex;align-items:flex-start;padding:14rpx 0;border-bottom:1rpx solid #ECECE7}.step-row:last-child{border-bottom:0}.step-index{width:36rpx;height:36rpx;line-height:36rpx;text-align:center;border-radius:50%;background:#DDEFEA;color:#236D69;font-size:19rpx;font-weight:700;flex-shrink:0;margin-right:14rpx}.step-text{font-size:23rpx;color:#4F5F5D;line-height:1.6}.source-card{box-shadow:none;border:1rpx solid #E4E3DC}.source-line{font-size:22rpx;line-height:1.65;color:#657371;margin-top:11rpx}.source-line.warn{color:#A15B3E;background:#F7EDE6;padding:15rpx;border-radius:13rpx}
</style>
