<template>
  <view class="container">
    <!-- 参数输入区 -->
    <view class="card">
      <view class="card-title">设计参数</view>

      <!-- 设计弯矩 -->
      <view class="form-group">
        <view class="form-label">设计弯矩 M (kN·m)</view>
        <input class="form-input highlight-input" v-model.number="form.M" type="digit" placeholder="如 200" />
      </view>

      <!-- 截面尺寸 -->
      <view class="grid-2">
        <view class="form-group">
          <view class="form-label">截面宽度 b (mm)</view>
          <input class="form-input" v-model.number="form.b" type="digit" placeholder="如 300" />
        </view>
        <view class="form-group">
          <view class="form-label">截面高度 h (mm)</view>
          <input class="form-input" v-model.number="form.h" type="digit" placeholder="如 600" />
        </view>
      </view>

      <view class="form-group">
        <view class="form-label">受拉区 a_s (mm)</view>
        <input class="form-input" v-model.number="form.a_s" type="digit" placeholder="默认 40" />
      </view>

      <!-- 材料选择 -->
      <view class="grid-2">
        <view class="form-group">
          <view class="form-label">混凝土</view>
          <picker
            :range="concreteGrades"
            :value="concreteIndex"
            @change="onConcreteChange"
          >
            <view class="form-picker">
              <text>{{ form.concrete_grade }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
        <view class="form-group">
          <view class="form-label">钢筋牌号</view>
          <picker
            :range="rebarGrades"
            :value="rebarIndex"
            @change="onRebarChange"
          >
            <view class="form-picker">
              <text>{{ form.rebar_grade }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </picker>
        </view>
      </view>

      <!-- 可选钢筋直径 -->
      <view class="form-group">
        <view class="form-label">选筋范围（可多选）</view>
        <view class="diameter-tags">
          <view
            v-for="d in allDiameters"
            :key="d"
            class="diameter-tag"
            :class="{ selected: form.bar_diameters.includes(d) }"
            @click="toggleDiameter(d)"
          >
            Φ{{ d }}
          </view>
        </view>
      </view>

      <!-- 计算按钮 -->
      <button class="btn-primary" @click="doCalculate" :disabled="loading">
        {{ loading ? '计算中...' : '计算配筋' }}
      </button>
    </view>

    <!-- 计算结果 -->
    <view class="card" v-if="result">
      <!-- 核心结果 -->
      <view class="calc-hero">
        <text class="calc-hero-label">所需钢筋面积</text>
        <text class="calc-hero-value">{{ result.data.as_req }}<text class="calc-hero-unit"> mm²</text></text>
        <text class="status-tag" :class="statusClass">{{ result.message }}</text>
      </view>

      <!-- 计算过程 -->
      <view class="calc-process">
        <view class="calc-row">
          <text class="calc-key">材料参数</text>
          <text class="calc-val">fc = {{ result.data.fc }} MPa, fy = {{ result.data.fy }} MPa</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">有效高度</text>
          <text class="calc-val">h₀ = h − a_s = {{ form.h }} − {{ form.a_s }} = {{ result.data.h0 }} mm</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">界限 ξb</text>
          <text class="calc-val">{{ result.data.xi_b }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">抵抗矩系数</text>
          <text class="calc-val">αs = M / (α₁·fc·b·h₀²) = {{ result.data.alpha_s }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">相对受压区高度</text>
          <text class="calc-val">ξ = 1 − √(1 − 2αs) = {{ result.data.xi }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">内力臂系数</text>
          <text class="calc-val">γs = 0.5·(1 + √(1 − 2αs)) = {{ result.data.gamma_s }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">配筋面积</text>
          <text class="calc-val">As = M / (fy·γs·h₀) = {{ result.data.as_req }} mm²</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">配筋率</text>
          <text class="calc-val">ρ = {{ result.data.as_req }} / ({{ form.b }} × {{ result.data.h0 }}) = {{ (result.data.as_req / (form.b * result.data.h0)).toFixed(4) }}</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">最小配筋</text>
          <text class="calc-val">As_min = ρ_min·b·h = {{ result.data.as_min }} mm² (ρ_min = {{ result.data.rho_min }})</text>
        </view>
        <view class="calc-hr"></view>

        <view class="calc-row">
          <text class="calc-key">单筋上限</text>
          <text class="calc-val">As_max = ξb·α₁·fc·b·h₀/fy = {{ result.data.as_max }} mm²</text>
        </view>
        <view class="calc-hr"></view>

        <view v-if="result.data.need_double" class="calc-row">
          <text class="calc-key">受压钢筋</text>
          <text class="calc-val" style="color:#C62828;">需双筋截面，As' = {{ result.data.as_prime_req }} mm²</text>
        </view>
        <view v-if="result.data.need_double" class="calc-hr"></view>
      </view>

      <!-- 选筋方案 -->
      <view class="scheme-title">推荐选筋方案</view>
      <view class="scheme-list">
        <view
          class="scheme-item"
          v-for="(s, idx) in result.data.schemes"
          :key="idx"
        >
          <view class="scheme-rank">{{ idx + 1 }}</view>
          <view class="scheme-desc">{{ s.desc }}</view>
          <view class="scheme-info">
            <text>{{ s.area }} mm² · {{ s.layout }}</text>
          </view>
          <view class="scheme-diff" :class="s.area >= result.data.as_req ? 'diff-ok' : 'diff-under'">
            {{ s.area >= result.data.as_req ? '+' : '' }}{{ ((s.area - result.data.as_req) / result.data.as_req * 100).toFixed(1) }}%
          </view>
        </view>
      </view>
    </view>

    <!-- 底部间距 -->
    <view style="height: 40rpx;"></view>
  </view>
</template>

<script>
import { calcReinforcement } from '@/utils/api.js'

export default {
  data() {
    return {
      form: {
        M: 200,
        b: 300,
        h: 600,
        concrete_grade: 'C30',
        rebar_grade: 'HRB400',
        a_s: 40,
        bar_diameters: [14, 16, 18, 20, 22, 25],
      },

      concreteGrades: ['C25', 'C30', 'C35', 'C40', 'C45', 'C50', 'C55', 'C60', 'C65', 'C70', 'C75', 'C80'],
      rebarGrades: ['HPB300', 'HRB400', 'HRB500'],
      concreteIndex: 1,
      rebarIndex: 1,

      allDiameters: [10, 12, 14, 16, 18, 20, 22, 25, 28, 32],

      loading: false,
      result: null,
      showSteps: false,
    }
  },

  computed: {
    statusClass() {
      if (!this.result) return ''
      const s = this.result.data.status
      if (s === 'ok') return 'status-ok'
      if (s === 'need_double') return 'status-warn'
      if (s === 'min_reinforcement') return 'status-warn'
      return 'status-error'
    },
  },

  methods: {
    onConcreteChange(e) {
      this.concreteIndex = e.detail.value
      this.form.concrete_grade = this.concreteGrades[e.detail.value]
    },
    onRebarChange(e) {
      this.rebarIndex = e.detail.value
      this.form.rebar_grade = this.rebarGrades[e.detail.value]
    },

    toggleDiameter(d) {
      const idx = this.form.bar_diameters.indexOf(d)
      if (idx > -1) {
        if (this.form.bar_diameters.length > 2) {
          this.form.bar_diameters.splice(idx, 1)
        } else {
          uni.showToast({ title: '至少保留2个直径', icon: 'none' })
        }
      } else {
        this.form.bar_diameters.push(d)
        this.form.bar_diameters.sort((a, b) => a - b)
      }
    },

    async doCalculate() {
      if (!this.form.M || !this.form.b || !this.form.h) {
        uni.showToast({ title: '请填写弯矩和截面尺寸', icon: 'none' })
        return
      }

      this.loading = true
      this.result = null

      try {
        const res = await calcReinforcement({
          M: this.form.M,
          b: this.form.b,
          h: this.form.h,
          concrete_grade: this.form.concrete_grade,
          rebar_grade: this.form.rebar_grade,
          a_s: this.form.a_s,
          bar_diameters: this.form.bar_diameters,
        })

        this.result = res
        this.showSteps = true
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

.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #222;
  margin-bottom: 24rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

.highlight-input {
  font-size: 36rpx;
  font-weight: 700;
  color: #2C6FCE;
  text-align: center;
}

/* 钢筋直径标签 */
.diameter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.diameter-tag {
  padding: 12rpx 24rpx;
  background: #F5F6FA;
  border-radius: 24rpx;
  font-size: 26rpx;
  color: #666;
  border: 2rpx solid transparent;
}

.diameter-tag.selected {
  background: #E8F0FF;
  color: #2C6FCE;
  border-color: #2C6FCE;
  font-weight: 600;
}

/* Picker 箭头 */
.picker-arrow {
  font-size: 24rpx;
  color: #999;
}

/* ========== 计算结果：简洁风格 ========== */
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
  font-size: 56rpx;
  font-weight: 800;
  color: #111;
  margin-bottom: 12rpx;
}
.calc-hero-unit {
  font-size: 28rpx;
  font-weight: 500;
  color: #999;
}

.calc-process {
  margin-top: 8rpx;
}
.calc-row {
  display: flex;
  align-items: baseline;
  padding: 16rpx 0;
}
.calc-key {
  width: 170rpx;
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

.text-warn { color: #E65100; }

/* 选筋方案 */
.scheme-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin: 24rpx 0 12rpx;
}
.scheme-list { display: flex; flex-direction: column; gap: 12rpx; }
.scheme-item {
  display: flex;
  align-items: center;
  background: #FAFBFC;
  border-radius: 12rpx;
  padding: 20rpx;
  border: 2rpx solid transparent;
}
.scheme-item:first-child { border-color: #2C6FCE; background: #F0F6FF; }
.scheme-rank {
  width: 40rpx; height: 40rpx;
  line-height: 40rpx; text-align: center;
  font-size: 24rpx; font-weight: 700; color: #fff;
  background: #2C6FCE;
  border-radius: 50%;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.scheme-item:first-child .scheme-rank { background: #FF9800; }
.scheme-desc { font-size: 30rpx; font-weight: 700; color: #222; margin-right: 12rpx; flex-shrink: 0; }
.scheme-info { display: flex; align-items: center; font-size: 24rpx; color: #666; flex: 1; }
.scheme-diff { font-size: 24rpx; font-weight: 700; padding: 4rpx 14rpx; border-radius: 16rpx; flex-shrink: 0; }
.diff-ok { background: #E8F5E9; color: #2E7D32; }
.diff-under { background: #FFEBEE; color: #C62828; }
</style>
