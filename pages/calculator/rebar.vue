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
      <!-- 主要结果 -->
      <view class="result-card">
        <view class="result-label">所需钢筋面积</view>
        <view class="result-value">
          {{ result.data.as_req }}
          <text class="result-unit">mm²</text>
        </view>

        <!-- 判定 -->
        <view style="text-align:center;">
          <text class="status-tag" :class="statusClass">{{ result.message }}</text>
        </view>
      </view>

      <!-- 关键参数 -->
      <view class="params-grid">
        <view class="param-item">
          <text class="param-label">相对受压区高度 ξ</text>
          <text class="param-value">{{ result.data.xi }}</text>
        </view>
        <view class="param-item">
          <text class="param-label">截面抵抗矩系数 αs</text>
          <text class="param-value">{{ result.data.alpha_s }}</text>
        </view>
        <view class="param-item">
          <text class="param-label">内力臂系数 γs</text>
          <text class="param-value">{{ result.data.gamma_s }}</text>
        </view>
        <view class="param-item">
          <text class="param-label">是否需双筋</text>
          <text class="param-value" :class="{ 'text-warn': result.data.need_double }">
            {{ result.data.need_double ? '是' : '否' }}
          </text>
        </view>
        <view class="param-item">
          <text class="param-label">最小配筋面积</text>
          <text class="param-value">{{ result.data.as_min }} mm²</text>
        </view>
        <view class="param-item">
          <text class="param-label">单筋最大配筋面积</text>
          <text class="param-value">{{ result.data.as_max }} mm²</text>
        </view>
      </view>

      <!-- 双筋附加信息 -->
      <view class="double-info" v-if="result.data.need_double">
        <text class="double-label">⚠ 需配置受压钢筋</text>
        <text class="double-value">As' = {{ result.data.as_prime_req }} mm²</text>
      </view>

      <!-- 选筋方案 -->
      <view class="scheme-title">📋 推荐选筋方案</view>
      <view class="scheme-list">
        <view
          class="scheme-item"
          v-for="(s, idx) in result.data.schemes"
          :key="idx"
        >
          <view class="scheme-rank">方案{{ idx + 1 }}</view>
          <view class="scheme-desc">{{ s.desc }}</view>
          <view class="scheme-info">
            <text class="scheme-area">{{ s.area }} mm²</text>
            <text class="scheme-layout">· {{ s.layout }}</text>
          </view>
          <view class="scheme-diff" :class="s.area >= result.data.as_req ? 'diff-ok' : 'diff-under'">
            {{ s.area >= result.data.as_req ? '+' : '' }}{{ ((s.area - result.data.as_req) / result.data.as_req * 100).toFixed(1) }}%
          </view>
        </view>
      </view>

      <!-- 计算步骤 -->
      <view class="steps-toggle" @click="showSteps = !showSteps">
        <text>📝 详细计算过程</text>
        <text>{{ showSteps ? '▲' : '▼' }}</text>
      </view>
      <view class="steps-box" v-if="showSteps">
        <view class="step-line" v-for="(step, idx) in result.data.steps" :key="idx">
          {{ step }}
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

/* 参数网格 */
.params-grid {
  display: flex;
  flex-wrap: wrap;
  background: #FAFBFC;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-top: 20rpx;
}

.param-item {
  width: 50%;
  padding: 14rpx 0;
}

.param-label {
  display: block;
  font-size: 24rpx;
  color: #999;
}

.param-value {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-top: 4rpx;
}

.text-warn {
  color: #E65100;
}

/* 双筋提示 */
.double-info {
  background: #FFF8E1;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-top: 16rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.double-label {
  font-size: 26rpx;
  color: #E65100;
  font-weight: 500;
}

.double-value {
  font-size: 28rpx;
  font-weight: 700;
  color: #E65100;
}

/* 选筋方案 */
.scheme-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-top: 24rpx;
  margin-bottom: 12rpx;
}

.scheme-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.scheme-item {
  display: flex;
  align-items: center;
  background: #FAFBFC;
  border-radius: 12rpx;
  padding: 20rpx;
  border: 2rpx solid transparent;
}

.scheme-item:first-child {
  border-color: #2C6FCE;
  background: #F0F6FF;
}

.scheme-rank {
  font-size: 22rpx;
  color: #fff;
  background: #2C6FCE;
  border-radius: 8rpx;
  padding: 4rpx 12rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.scheme-item:first-child .scheme-rank {
  background: #FF9800;
}

.scheme-desc {
  font-size: 30rpx;
  font-weight: 700;
  color: #222;
  margin-right: 12rpx;
  flex-shrink: 0;
}

.scheme-info {
  display: flex;
  align-items: center;
  font-size: 24rpx;
  color: #999;
  flex: 1;
}

.scheme-area {
  font-weight: 600;
  color: #555;
}

.scheme-layout {
  color: #bbb;
}

.scheme-diff {
  font-size: 24rpx;
  font-weight: 700;
  padding: 4rpx 14rpx;
  border-radius: 16rpx;
  flex-shrink: 0;
}

.diff-ok {
  background: #E8F5E9;
  color: #2E7D32;
}

.diff-under {
  background: #FFEBEE;
  color: #C62828;
}

/* 步骤折叠 */
.steps-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: #2C6FCE;
  font-weight: 500;
}
</style>
