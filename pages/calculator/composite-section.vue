<template>
  <view class="container">
    <!-- CAD 截面示意图 -->
    <view class="card">
      <view class="cad-wrap">
        <view class="cad-diagram" v-if="blocks.length > 0">
          <!-- 截面图区域 -->
          <view class="cad-drawing" :style="{ height: totalCadH + 'rpx', width: totalCadW + 'rpx' }">
            <!-- y 轴（竖直参考轴，x=0） -->
            <view class="cad-axis-y" :style="{ height: totalCadH + 'rpx' }">
              <text class="cad-axis-label-y">y</text>
            </view>
            <!-- x 轴（水平参考轴，y=0） -->
            <view class="cad-axis-x" :style="{ width: totalCadW + 'rpx' }">
              <text class="cad-axis-label-x">x</text>
            </view>
            <!-- 各分块 -->
            <view v-for="(blk, i) in blocks" :key="'blk-'+i"
              class="cad-block"
              :class="{ 'cad-block-hole': blk.is_hole }"
              :style="blockStyle(blk)">
              <text v-if="blk.h * cadScale > 20" class="cad-block-label">{{ blk.label || i+1 }}</text>
            </view>
            <!-- 形心轴线（水平，红色虚线） -->
            <view v-if="result" class="cad-centroid-line"
              :style="{ bottom: result.data.y_bar * cadScale + 'rpx', width: totalCadW + 'rpx' }">
            </view>
          </view>
          <!-- 形心标注 -->
          <text v-if="result" class="cad-centroid-label">
            形心轴 ȳ = {{ result.data.y_bar }} mm
          </text>
        </view>
        <text v-else class="cad-empty">请添加分块</text>
      </view>
    </view>

    <!-- 快捷预设 -->
    <view class="card">
      <view class="card-title">快捷预设</view>
      <view class="preset-row">
        <button class="btn-preset" @click="loadPreset('t')">T形截面</button>
        <button class="btn-preset" @click="loadPreset('i')">工字形截面</button>
        <button class="btn-preset" @click="loadPreset('box')">箱形截面</button>
        <button class="btn-preset" @click="loadPreset('hole')">矩形带孔</button>
      </view>
    </view>

    <!-- 分块列表 -->
    <view class="card" v-for="(blk, i) in blocks" :key="'form-'+i">
      <view class="card-title-row">
        <text class="card-title">分块 {{ i+1 }}</text>
        <view class="card-title-actions">
          <switch :checked="blk.is_hole" @change="(e) => toggleHole(i, e.detail.value)" color="#E53935" style="transform:scale(0.7)" />
          <text class="hole-tag" :class="{ 'hole-on': blk.is_hole }">{{ blk.is_hole ? '孔洞' : '实体' }}</text>
          <button v-if="blocks.length > 1" class="btn-del" @click="removeBlock(i)">✕</button>
        </view>
      </view>

      <view class="form-group">
        <text class="form-label">名称</text>
        <input class="form-input" v-model="blk.label" placeholder="如：上翼缘" />
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">宽度 b (mm)</text>
          <input class="form-input" v-model.number="blk.b" type="digit" placeholder="mm" />
        </view>
        <view class="form-group">
          <text class="form-label">高度 h (mm)</text>
          <input class="form-input" v-model.number="blk.h" type="digit" placeholder="mm" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">距底边 y₀ (mm)</text>
          <input class="form-input" v-model.number="blk.y0" type="digit" placeholder="mm" />
        </view>
        <view class="form-group">
          <text class="form-label">距左边 x₀ (mm)</text>
          <input class="form-input" v-model.number="blk.x0" type="digit" placeholder="默认0" />
        </view>
      </view>
    </view>

    <!-- 添加分块 -->
    <button class="btn-add" @click="addBlock">+ 添加分块</button>

    <!-- 计算按钮 -->
    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中...' : '开始计算（平行移轴公式）' }}
    </button>

    <!-- 计算结果 -->
    <view class="card" v-if="result">
      <view class="calc-hero">
        <text class="calc-hero-label">惯性矩 I_z</text>
        <text class="calc-hero-value">{{ formatSci(result.data.I_z) }}<text class="calc-hero-unit"> mm⁴</text></text>
        <text class="calc-hero-sub">{{ formatSci(result.data.I_z / 1e4) }} cm⁴</text>
        <text class="status-tag status-ok">计算完成</text>
      </view>

      <view class="calc-process">
        <!-- 基本参数 -->
        <view class="calc-row">
          <text class="calc-key">面积 A</text>
          <text class="calc-val">{{ result.data.A }} mm²</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">形心距底边 ȳ</text>
          <text class="calc-val">{{ result.data.y_bar }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">惯性矩 I_z</text>
          <text class="calc-val">{{ formatSci(result.data.I_z) }} mm⁴  =  {{ formatSci(result.data.I_z / 1e4) }} cm⁴</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">惯性矩 I_y</text>
          <text class="calc-val">{{ formatSci(result.data.I_y) }} mm⁴  =  {{ formatSci(result.data.I_y / 1e4) }} cm⁴</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">抵抗矩 W_z_top</text>
          <text class="calc-val">{{ formatSci(result.data.W_z_top) }} mm³</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">抵抗矩 W_z_bot</text>
          <text class="calc-val">{{ formatSci(result.data.W_z_bot) }} mm³</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">回转半径 i_z</text>
          <text class="calc-val">{{ result.data.i_z }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">回转半径 i_y</text>
          <text class="calc-val">{{ result.data.i_y }} mm</text>
        </view>
        <view class="calc-hr"></view>
        <view class="calc-row">
          <text class="calc-key">面积矩 S_z</text>
          <text class="calc-val">{{ formatSci(result.data.S_z) }} mm³</text>
        </view>
      </view>

      <!-- 计算过程表 -->
      <view class="calc-table-title">平行移轴计算明细</view>
      <view class="calc-table">
        <view class="calc-table-header">
          <text class="t-col t-col-name">分块</text>
          <text class="t-col">A (mm²)</text>
          <text class="t-col">y_ci</text>
          <text class="t-col">d_y</text>
          <text class="t-col t-col-wide">I_zc (mm⁴)</text>
          <text class="t-col t-col-wide">A·d_y² (mm⁴)</text>
          <text class="t-col t-col-wide">I_z 贡献</text>
        </view>
        <view v-for="(d, idx) in result.data.block_details" :key="'det-'+idx"
          class="calc-table-row" :class="{ 'row-hole': d.is_hole }">
          <text class="t-col t-col-name">{{ d.label }}</text>
          <text class="t-col">{{ d.A }}</text>
          <text class="t-col">{{ d.y_ci }}</text>
          <text class="t-col">{{ d.d_y }}</text>
          <text class="t-col t-col-wide">{{ formatSci(d.I_zc) }}</text>
          <text class="t-col t-col-wide">{{ formatSci(d.Ady2) }}</text>
          <text class="t-col t-col-wide t-col-bold">{{ formatSci(d.I_z_contrib) }}</text>
        </view>
        <view class="calc-table-row row-sum">
          <text class="t-col t-col-name">合计</text>
          <text class="t-col">{{ result.data.A }}</text>
          <text class="t-col">—</text>
          <text class="t-col">—</text>
          <text class="t-col t-col-wide">—</text>
          <text class="t-col t-col-wide">—</text>
          <text class="t-col t-col-wide t-col-bold">{{ formatSci(result.data.I_z) }}</text>
        </view>
      </view>
    </view>

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script>
import { calcCompositeSection } from '@/utils/api.js'

export default {
  data() {
    return {
      blocks: [
        { b: 200, h: 20, y0: 120, x0: 0, is_hole: false, label: '上翼缘' },
        { b: 20, h: 120, y0: 0, x0: 0, is_hole: false, label: '腹板' },
      ],
      loading: false,
      result: null,
    }
  },

  computed: {
    cadScale() {
      // 自动缩放：所有分块中最大宽度映射到 260rpx
      const maxW = Math.max(...this.blocks.map(b => b.x0 + b.b), 1)
      return Math.min(260 / maxW, 0.8)
    },
    totalH() {
      if (this.blocks.length === 0) return 0
      return Math.max(...this.blocks.map(b => b.y0 + b.h))
    },
    totalW() {
      if (this.blocks.length === 0) return 0
      return Math.max(...this.blocks.map(b => b.x0 + b.b))
    },
    totalCadH() {
      return Math.max(this.totalH * this.cadScale, 100)
    },
    totalCadW() {
      return Math.max(this.totalW * this.cadScale, 200)
    },
  },

  methods: {
    addBlock() {
      this.blocks.push({ b: 100, h: 100, y0: 0, x0: 0, is_hole: false, label: '' })
      this.result = null
    },

    removeBlock(i) {
      this.blocks.splice(i, 1)
      this.result = null
    },

    toggleHole(i, val) {
      this.blocks[i].is_hole = val
      this.result = null
    },

    // CAD 图中分块定位
    blockStyle(blk) {
      return {
        left: blk.x0 * this.cadScale + 'rpx',
        bottom: blk.y0 * this.cadScale + 'rpx',
        width: blk.b * this.cadScale + 'rpx',
        height: blk.h * this.cadScale + 'rpx',
      }
    },

    // 科学计数法
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

    loadPreset(type) {
      this.result = null
      if (type === 't') {
        this.blocks = [
          { b: 200, h: 20, y0: 120, x0: 0, is_hole: false, label: '上翼缘' },
          { b: 20, h: 120, y0: 0, x0: 0, is_hole: false, label: '腹板' },
        ]
      } else if (type === 'i') {
        this.blocks = [
          { b: 200, h: 15, y0: 285, x0: 0, is_hole: false, label: '上翼缘' },
          { b: 10, h: 270, y0: 15, x0: 0, is_hole: false, label: '腹板' },
          { b: 200, h: 15, y0: 0, x0: 0, is_hole: false, label: '下翼缘' },
        ]
      } else if (type === 'box') {
        this.blocks = [
          { b: 200, h: 300, y0: 0, x0: 0, is_hole: false, label: '外矩形' },
          { b: 140, h: 240, y0: 30, x0: 30, is_hole: true, label: '内孔（空心）' },
        ]
      } else if (type === 'hole') {
        this.blocks = [
          { b: 300, h: 500, y0: 0, x0: 0, is_hole: false, label: '外矩形' },
          { b: 150, h: 200, y0: 150, x0: 75, is_hole: true, label: '圆孔等效矩形' },
        ]
      }
    },

    async doCalculate() {
      // 校验
      const solids = this.blocks.filter(b => !b.is_hole)
      if (solids.length === 0) {
        uni.showToast({ title: '至少需要一个实体分块', icon: 'none' })
        return
      }
      for (let i = 0; i < this.blocks.length; i++) {
        const blk = this.blocks[i]
        if (!blk.b || !blk.h || blk.b <= 0 || blk.h <= 0) {
          uni.showToast({ title: `分块${i+1}: 请填写有效的宽度和高度`, icon: 'none' })
          return
        }
      }

      this.loading = true
      this.result = null
      try {
        this.result = await calcCompositeSection({ blocks: this.blocks })
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
.container { padding-bottom: 40rpx; }

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

.cad-empty {
  font-size: 26rpx;
  color: #bbb;
  padding: 40rpx;
}

.cad-drawing {
  position: relative;
}

/* ---- x 轴（水平，y=0）---- */
.cad-axis-x {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3rpx;
  background: #2C6FCE;
  border-radius: 2rpx;
}

.cad-axis-label-x {
  position: absolute;
  right: -36rpx;
  top: -12rpx;
  font-size: 22rpx;
  font-weight: 700;
  font-style: italic;
  color: #2C6FCE;
}

/* ---- y 轴（竖直，x=0）---- */
.cad-axis-y {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 3rpx;
  background: #2E7D32;
  border-radius: 2rpx;
}

.cad-axis-label-y {
  position: absolute;
  top: -24rpx;
  left: -8rpx;
  font-size: 22rpx;
  font-weight: 700;
  font-style: italic;
  color: #2E7D32;
}

.cad-block {
  position: absolute;
  border: 2rpx solid #333;
  background: rgba(44, 111, 206, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.cad-block-hole {
  border: 2rpx dashed #E53935;
  background: rgba(229, 57, 53, 0.06);
}

.cad-block-label {
  font-size: 18rpx;
  color: #666;
  white-space: nowrap;
}

.cad-centroid-line {
  position: absolute;
  height: 1rpx;
  background: #E53935;
  border: none;
  border-top: 2rpx dashed #E53935;
}

.cad-centroid-label {
  font-size: 20rpx;
  color: #E53935;
  margin-top: 6rpx;
}

.cad-dim-top-line {
  display: flex;
  justify-content: center;
  margin-bottom: 2rpx;
}

.cad-dim-tag {
  font-size: 20rpx;
  color: #555;
}

.cad-dim-right {
  position: relative;
}

.cad-dim-tag-v {
  font-size: 20rpx;
  color: #555;
  writing-mode: vertical-rl;
}

/* ========== 预设按钮 ========== */
.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.btn-preset {
  flex: 0 0 auto;
  padding: 12rpx 24rpx;
  font-size: 24rpx;
  background: #F0F4FF;
  color: #2C6FCE;
  border: 1rpx solid #C8D9F0;
  border-radius: 8rpx;
  line-height: 1;
}

/* ========== 分块卡片 ========== */
.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

.card-title-actions {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.hole-tag {
  font-size: 22rpx;
  color: #999;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  background: #f5f5f5;
}

.hole-on {
  color: #E53935;
  background: #FFEBEE;
}

.btn-del {
  width: 48rpx;
  height: 48rpx;
  line-height: 48rpx;
  text-align: center;
  font-size: 28rpx;
  color: #E53935;
  background: #FFEBEE;
  border: none;
  border-radius: 50%;
  padding: 0;
  margin-left: 8rpx;
}

.btn-add {
  display: block;
  margin: 0 20rpx 20rpx;
  padding: 24rpx;
  text-align: center;
  font-size: 28rpx;
  color: #2C6FCE;
  background: #fff;
  border: 2rpx dashed #C8D9F0;
  border-radius: 12rpx;
}

/* ========== 通用组件（复用全局样式） ========== */
.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #222;
  margin: 0;
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
  width: 220rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.calc-val {
  flex: 1;
  font-size: 26rpx;
  color: #111;
  line-height: 1.5;
}

.calc-hr {
  height: 1rpx;
  background: #E8E8E8;
}

/* ========== 计算明细表 ========== */
.calc-table-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-top: 30rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid #eee;
}

.calc-table {
  margin-top: 16rpx;
  border: 1rpx solid #eee;
  border-radius: 8rpx;
  overflow: hidden;
}

.calc-table-header {
  display: flex;
  background: #F5F7FA;
  padding: 16rpx 8rpx;
  border-bottom: 1rpx solid #eee;
}

.calc-table-header .t-col {
  font-weight: 600;
  color: #555;
  font-size: 22rpx;
}

.calc-table-row {
  display: flex;
  padding: 14rpx 8rpx;
  border-bottom: 1rpx solid #f5f5f5;
}

.t-col {
  flex: 1;
  font-size: 22rpx;
  color: #333;
  text-align: center;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.t-col-name { flex: 1.2; text-align: left; }
.t-col-wide { flex: 1.5; }
.t-col-bold { font-weight: 600; color: #111; }

.row-hole {
  background: #FFF5F5;
}

.row-hole .t-col {
  color: #C62828;
}

.row-sum {
  background: #F8FAFB;
}

.row-sum .t-col {
  font-weight: 600;
  color: #111;
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
