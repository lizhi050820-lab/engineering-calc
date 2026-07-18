<template>
  <view class="container">
    <!-- CAD 截面示意图 -->
    <view class="card">
      <view class="cad-wrap">
        <!-- 矩形 -->
        <view v-if="form.shape === 'rectangle'" class="cad-diagram">
          <view class="cad-dim-top">
            <view class="cad-tick cad-tick-h"></view>
            <text class="cad-dim">b = {{ form.b || '?' }}</text>
            <view class="cad-tick cad-tick-h"></view>
          </view>
          <view class="cad-row">
            <view class="cad-dim-left">
              <view class="cad-tick cad-tick-v"></view>
              <text class="cad-dim cad-dim-v">h = {{ form.h || '?' }}</text>
              <view class="cad-tick cad-tick-v"></view>
            </view>
            <view class="cad-frame-rect"></view>
          </view>
        </view>

        <!-- T形 -->
        <view v-if="form.shape === 't-section'" class="cad-diagram">
          <view class="cad-dim-top">
            <view class="cad-tick cad-tick-h"></view>
            <text class="cad-dim">b𝒻 = {{ form.b_f || '?' }}</text>
            <view class="cad-tick cad-tick-h"></view>
          </view>
          <view class="cad-row">
            <view class="cad-dim-left">
              <view class="cad-tick cad-tick-v"></view>
              <text class="cad-dim cad-dim-v">h = {{ form.h || '?' }}</text>
              <view class="cad-tick cad-tick-v"></view>
            </view>
            <view class="cad-frame-t">
              <view class="cad-t-flange">
                <text class="cad-dim-inner">h𝒻 = {{ form.h_f || '?' }}</text>
              </view>
              <view class="cad-t-web">
                <text class="cad-dim-inner">bw = {{ form.b_w || '?' }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 圆形 -->
        <view v-if="form.shape === 'circle'" class="cad-diagram">
          <view class="cad-row">
            <view class="cad-dim-left">
              <view class="cad-tick cad-tick-v"></view>
              <text class="cad-dim cad-dim-v">d = {{ form.d || '?' }}</text>
              <view class="cad-tick cad-tick-v"></view>
            </view>
            <view class="cad-frame-circle"></view>
          </view>
        </view>

        <!-- 环形 -->
        <view v-if="form.shape === 'annular'" class="cad-diagram">
          <view class="cad-row">
            <view class="cad-dim-left">
              <view class="cad-tick cad-tick-v"></view>
              <text class="cad-dim cad-dim-v">D = {{ form.D || '?' }}</text>
              <view class="cad-tick cad-tick-v"></view>
            </view>
            <view class="cad-frame-annular"></view>
          </view>
          <view class="cad-dim-bottom">
            <text class="cad-dim">内径 d = {{ form.d_inner || '?' }}</text>
          </view>
        </view>

        <!-- 工字钢 -->
        <view v-if="form.shape === 'i-beam'" class="cad-diagram">
          <view class="cad-dim-top">
            <view class="cad-tick cad-tick-h"></view>
            <text class="cad-dim">b𝒻 = {{ form.b_f_ibeam || '?' }}</text>
            <view class="cad-tick cad-tick-h"></view>
          </view>
          <view class="cad-row">
            <view class="cad-dim-left">
              <view class="cad-tick cad-tick-v"></view>
              <text class="cad-dim cad-dim-v">h = {{ form.h_ibeam || '?' }}</text>
              <view class="cad-tick cad-tick-v"></view>
            </view>
            <view class="cad-frame-i">
              <view class="cad-i-flange-top">
                <text class="cad-dim-inner">t𝒻 = {{ form.t_f || '?' }}</text>
              </view>
              <view class="cad-i-web">
                <text class="cad-dim-inner">tw = {{ form.t_w || '?' }}</text>
              </view>
              <view class="cad-i-flange-bot"></view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 截面形状选择 -->
    <view class="card">
      <view class="card-title">截面形状</view>
      <picker :range="shapeList" :value="shapeIndex" @change="onShapeChange">
        <view class="form-picker">{{ shapeList[shapeIndex] }}</view>
      </picker>
    </view>

    <!-- 尺寸参数 -->
    <view class="card">
      <view class="card-title">截面尺寸 (mm)</view>

      <!-- 矩形 -->
      <view v-if="form.shape === 'rectangle'" class="grid-2">
        <view class="form-group">
          <text class="form-label">宽度 b</text>
          <input class="form-input" v-model.number="form.b" type="digit" placeholder="mm" />
        </view>
        <view class="form-group">
          <text class="form-label">高度 h</text>
          <input class="form-input" v-model.number="form.h" type="digit" placeholder="mm" />
        </view>
      </view>

      <!-- T形 -->
      <view v-if="form.shape === 't-section'">
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">翼缘宽 b𝒻</text>
            <input class="form-input" v-model.number="form.b_f" type="digit" placeholder="mm" />
          </view>
          <view class="form-group">
            <text class="form-label">翼缘厚 h𝒻</text>
            <input class="form-input" v-model.number="form.h_f" type="digit" placeholder="mm" />
          </view>
        </view>
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">腹板宽 bw</text>
            <input class="form-input" v-model.number="form.b_w" type="digit" placeholder="mm" />
          </view>
          <view class="form-group">
            <text class="form-label">总高 h</text>
            <input class="form-input" v-model.number="form.h" type="digit" placeholder="mm" />
          </view>
        </view>
      </view>

      <!-- 圆形 -->
      <view v-if="form.shape === 'circle'">
        <view class="form-group">
          <text class="form-label">直径 d</text>
          <input class="form-input highlight-input" v-model.number="form.d" type="digit" placeholder="mm" />
        </view>
      </view>

      <!-- 环形 -->
      <view v-if="form.shape === 'annular'" class="grid-2">
        <view class="form-group">
          <text class="form-label">外径 D</text>
          <input class="form-input" v-model.number="form.D" type="digit" placeholder="mm" />
        </view>
        <view class="form-group">
          <text class="form-label">内径 d</text>
          <input class="form-input" v-model.number="form.d_inner" type="digit" placeholder="mm" />
        </view>
      </view>

      <!-- 工字钢 -->
      <view v-if="form.shape === 'i-beam'">
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">翼缘宽 b𝒻</text>
            <input class="form-input" v-model.number="form.b_f_ibeam" type="digit" placeholder="mm" />
          </view>
          <view class="form-group">
            <text class="form-label">总高 h</text>
            <input class="form-input" v-model.number="form.h_ibeam" type="digit" placeholder="mm" />
          </view>
        </view>
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">翼缘厚 t𝒻</text>
            <input class="form-input" v-model.number="form.t_f" type="digit" placeholder="mm" />
          </view>
          <view class="form-group">
            <text class="form-label">腹板厚 tw</text>
            <input class="form-input" v-model.number="form.t_w" type="digit" placeholder="mm" />
          </view>
        </view>
      </view>
    </view>

    <!-- 计算按钮 -->
    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中...' : '开始计算' }}
    </button>

    <!-- 计算结果 -->
    <view class="card" v-if="result">
      <view class="calc-hero">
        <text class="calc-hero-label">惯性矩 Iₓ</text>
        <text class="calc-hero-value">{{ formatSci(result.data.I_x) }}<text class="calc-hero-unit"> mm⁴</text></text>
        <text class="calc-hero-sub">{{ formatSci(result.data.I_x / 1e4) }} cm⁴</text>
        <text class="status-tag status-ok">计算完成</text>
      </view>

      <view class="calc-process">
        <view class="calc-row">
          <text class="calc-key">面积 A</text>
          <text class="calc-val">{{ result.data.A }} mm²</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">惯性矩 Iₓ</text>
          <text class="calc-val">{{ formatSci(result.data.I_x) }} mm⁴  =  {{ formatSci(result.data.I_x / 1e4) }} cm⁴</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">惯性矩 Iᵧ</text>
          <text class="calc-val">{{ formatSci(result.data.I_y) }} mm⁴  =  {{ formatSci(result.data.I_y / 1e4) }} cm⁴</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">抵抗矩 Wₓ</text>
          <text class="calc-val">{{ formatSci(result.data.W_x) }} mm³</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">抵抗矩 Wᵧ</text>
          <text class="calc-val">{{ formatSci(result.data.W_y) }} mm³</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">回转半径 iₓ</text>
          <text class="calc-val">{{ result.data.i_x }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">回转半径 iᵧ</text>
          <text class="calc-val">{{ result.data.i_y }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">面积矩 Sₓ</text>
          <text class="calc-val">{{ formatSci(result.data.S_x) }} mm³</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">形心距底边 y꜀</text>
          <text class="calc-val">{{ result.data.y_c }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">极惯性矩 Iₚ</text>
          <text class="calc-val">{{ formatSci(result.data.I_p) }} mm⁴  =  {{ formatSci(result.data.I_p / 1e4) }} cm⁴</text>
        </view>
      </view>
    </view>

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script>
import { calcSectionProperties } from '@/utils/api.js'

export default {
  data() {
    return {
      shapeList: ['矩形', 'T形', '圆形', '环形', '工字钢'],
      shapeValues: ['rectangle', 't-section', 'circle', 'annular', 'i-beam'],
      shapeIndex: 0,

      form: {
        shape: 'rectangle',
        // 矩形
        b: 200, h: 400,
        // T形
        b_f: 400, h_f: 100, b_w: 200,
        // 圆形
        d: 200,
        // 环形
        D: 200, d_inner: 100,
        // 工字钢
        b_f_ibeam: 300, h_ibeam: 400, t_f: 20, t_w: 12,
      },

      loading: false,
      result: null,
    }
  },

  methods: {
    onShapeChange(e) {
      this.shapeIndex = e.detail.value
      this.form.shape = this.shapeValues[this.shapeIndex]
      this.result = null  // 切换形状时清空结果
    },

    // 科学计数法格式化（如 1.067×10⁹）
    formatSci(val, decimals = 3) {
      if (!val || val === 0) return '0'
      const sign = val < 0 ? '-' : ''
      const abs = Math.abs(val)
      const exp = Math.floor(Math.log10(abs))
      const mantissa = abs / Math.pow(10, exp)
      const superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','-':'⁻'}
      const expStr = String(exp).split('').map(c => superscripts[c] || c).join('')
      return `${sign}${mantissa.toFixed(decimals)}×10${expStr}`
    },

    async doCalculate() {
      const shape = this.form.shape
      const params = { shape }

      // 按形状组装参数并校验
      if (shape === 'rectangle') {
        if (!this.form.b || !this.form.h) {
          uni.showToast({ title: '请填写宽度 b 和高度 h', icon: 'none' })
          return
        }
        params.b = this.form.b
        params.h = this.form.h
      } else if (shape === 't-section') {
        if (!this.form.b_f || !this.form.h_f || !this.form.b_w || !this.form.h) {
          uni.showToast({ title: '请填写全部 T形截面参数', icon: 'none' })
          return
        }
        params.b_f = this.form.b_f
        params.h_f = this.form.h_f
        params.b_w = this.form.b_w
        params.h = this.form.h
      } else if (shape === 'circle') {
        if (!this.form.d) {
          uni.showToast({ title: '请填写直径 d', icon: 'none' })
          return
        }
        params.d = this.form.d
      } else if (shape === 'annular') {
        if (!this.form.D || !this.form.d_inner) {
          uni.showToast({ title: '请填写外径 D 和内径 d', icon: 'none' })
          return
        }
        params.D = this.form.D
        params.d = this.form.d_inner
      } else if (shape === 'i-beam') {
        if (!this.form.b_f_ibeam || !this.form.h_ibeam || !this.form.t_f || !this.form.t_w) {
          uni.showToast({ title: '请填写全部工字钢参数', icon: 'none' })
          return
        }
        params.b_f = this.form.b_f_ibeam
        params.h = this.form.h_ibeam
        params.t_f = this.form.t_f
        params.t_w = this.form.t_w
      }

      this.loading = true
      this.result = null
      try {
        this.result = await calcSectionProperties(params)
      } catch (e) {
        console.error('计算失败:', e)
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.container {
  padding-bottom: 40rpx;
}

/* ========== CAD 示意图 ========== */
.cad-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}

.cad-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cad-row {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.cad-dim {
  font-size: 22rpx;
  color: #555;
}

.cad-dim-v {
  writing-mode: vertical-rl;
}

.cad-dim-top {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 4rpx;
}

.cad-dim-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 8rpx;
}

.cad-dim-bottom {
  margin-top: 8rpx;
}

.cad-dim-inner {
  font-size: 18rpx;
  color: #999;
  line-height: 1;
}

.cad-tick {
  background: #666;
}

.cad-tick-h {
  width: 24rpx;
  height: 1rpx;
  margin: 0 6rpx;
}

.cad-tick-v {
  width: 1rpx;
  height: 24rpx;
  margin: 6rpx 0;
}

/* 矩形 */
.cad-frame-rect {
  width: 260rpx;
  height: 200rpx;
  border: 2rpx solid #333;
}

/* T形 */
.cad-frame-t {
  width: 260rpx;
}

.cad-t-flange {
  width: 100%;
  height: 60rpx;
  border: 2rpx solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cad-t-web {
  width: 120rpx;
  height: 160rpx;
  border: 2rpx solid #333;
  border-top: none;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

/* 圆形 */
.cad-frame-circle {
  width: 200rpx;
  height: 200rpx;
  border: 2rpx solid #333;
  border-radius: 50%;
}

/* 环形 */
.cad-frame-annular {
  width: 220rpx;
  height: 220rpx;
  border: 2rpx solid #333;
  border-radius: 50%;
  position: relative;
}

.cad-frame-annular::after {
  content: '';
  position: absolute;
  top: 18%;
  left: 18%;
  width: 64%;
  height: 64%;
  border: 1.5rpx dashed #999;
  border-radius: 50%;
}

/* 工字钢 */
.cad-frame-i {
  width: 260rpx;
}

.cad-i-flange-top {
  width: 100%;
  height: 38rpx;
  border: 2rpx solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cad-i-web {
  width: 80rpx;
  height: 140rpx;
  border-left: 2rpx solid #333;
  border-right: 2rpx solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.cad-i-flange-bot {
  width: 100%;
  height: 38rpx;
  border: 2rpx solid #333;
}

/* ========== 卡片标题 ========== */
.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #222;
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

/* ========== 高亮输入 ========== */
.highlight-input {
  font-size: 36rpx;
  font-weight: 700;
  color: #14575B;
  text-align: center;
}

/* ========== 计算过程 ========== */
.calc-hero {
  text-align: center;
  padding: 16rpx 0 24rpx;
}

.calc-hero-label {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.calc-hero-value {
  display: block;
  font-size: 48rpx;
  font-weight: 800;
  color: #111;
  margin-bottom: 12rpx;
}

.calc-hero-unit {
  font-size: 28rpx;
  font-weight: 500;
  color: #999;
}

.calc-hero-sub {
  display: block;
  font-size: 26rpx;
  color: #888;
  margin-bottom: 12rpx;
}

.calc-process {
  margin-top: 8rpx;
}

.calc-row {
  display: flex;
  align-items: baseline;
  padding: 14rpx 0;
}

.calc-key {
  width: 190rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.calc-val {
  flex: 1;
  font-size: 28rpx;
  color: #111;
  line-height: 1.75;
  font-variant-numeric: lining-nums tabular-nums;
  letter-spacing: .3rpx;
}

.calc-hr {
  height: 1rpx;
  background: #E8E8E8;
}

/* ========== 状态标签 ========== */
.status-tag {
  display: inline-block;
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
  font-size: 24rpx;
  font-weight: 500;
}

.status-ok {
  background: #E8F5E9;
  color: #2E7D32;
}
</style>
