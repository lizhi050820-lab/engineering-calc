<template>
  <view class="container">
    <!-- 参数输入区 -->
    <view class="card">
      <view class="card-title">截面参数</view>

      <!-- 截面类型 -->
      <view class="form-group">
        <view class="form-label">截面类型</view>
        <view class="type-toggle">
          <view
            class="type-btn"
            :class="{ active: asType === 'single' }"
            @click="asType = 'single'"
          >
            单筋截面
          </view>
          <view
            class="type-btn"
            :class="{ active: asType === 'double' }"
            @click="asType = 'double'"
          >
            双筋截面
          </view>
        </view>
      </view>

      <!-- 基本尺寸 -->
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

      <view class="grid-2">
        <view class="form-group">
          <view class="form-label">受拉区 a_s (mm)</view>
          <input class="form-input" v-model.number="form.a_s" type="digit" placeholder="默认 40" />
        </view>
        <view class="form-group" v-if="asType === 'double'">
          <view class="form-label">受压区 a_s' (mm)</view>
          <input class="form-input" v-model.number="form.a_s_prime" type="digit" placeholder="默认 40" />
        </view>
      </view>

      <!-- 材料选择 -->
      <view class="form-group">
        <view class="form-label">混凝土强度等级</view>
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

      <!-- 模式选择：设计 / 校核 -->
      <view class="form-group">
        <view class="form-label">计算模式</view>
        <view class="type-toggle">
          <view
            class="type-btn"
            :class="{ active: mode === 'check' }"
            @click="mode = 'check'"
          >
            校核模式
          </view>
          <view
            class="type-btn"
            :class="{ active: mode === 'design' }"
            @click="mode = 'design'"
          >
            设计模式
          </view>
        </view>
      </view>

      <!-- 校核模式：输入已知配筋 -->
      <template v-if="mode === 'check'">
        <view class="form-group">
          <view class="form-label">已知受拉钢筋面积 As (mm²)</view>
          <input class="form-input" v-model.number="form.as_given" type="digit" placeholder="如 1256 (4Φ20)" />
        </view>
        <view class="form-group" v-if="asType === 'double'">
          <view class="form-label">已知受压钢筋面积 As' (mm²)</view>
          <input class="form-input" v-model.number="form.as_prime_given" type="digit" placeholder="如 628 (2Φ20)" />
        </view>
      </template>

      <!-- 计算按钮 -->
      <button class="btn-primary" @click="doCalculate" :disabled="loading">
        {{ loading ? '计算中...' : '开始计算' }}
      </button>
    </view>

    <!-- 计算结果 -->
    <view class="card" v-if="result">
      <!-- 主要结果 -->
      <view class="result-card">
        <view class="result-label">极限弯矩 Mu</view>
        <view class="result-value">
          {{ result.data.mu }}
          <text class="result-unit">kN·m</text>
        </view>

        <!-- 判定 -->
        <view style="text-align:center;">
          <text class="status-tag" :class="statusClass">{{ result.message }}</text>
        </view>
      </view>

      <!-- 计算参数 -->
      <view class="params-grid">
        <view class="param-item">
          <text class="param-label">受压区高度 x</text>
          <text class="param-value">{{ result.data.x }} mm</text>
        </view>
        <view class="param-item">
          <text class="param-label">相对受压区高度 ξ</text>
          <text class="param-value">{{ result.data.xi }}</text>
        </view>
        <view class="param-item">
          <text class="param-label">有效高度 h₀</text>
          <text class="param-value">{{ result.data.h0 }} mm</text>
        </view>
        <view class="param-item">
          <text class="param-label">界限 ξb</text>
          <text class="param-value">{{ result.data.xi_b }}</text>
        </view>
        <view class="param-item">
          <text class="param-label">所需 As</text>
          <text class="param-value">{{ result.data.as_req }} mm²</text>
        </view>
        <view class="param-item">
          <text class="param-label">最小配筋率</text>
          <text class="param-value">{{ result.data.rho_min }}</text>
        </view>
      </view>

      <!-- 计算步骤 -->
      <view class="steps-toggle" @click="showSteps = !showSteps">
        <text>📝 计算步骤</text>
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
import { calcBearingCapacity } from '@/utils/api.js'

export default {
  data() {
    return {
      // 表单
      asType: 'single',
      mode: 'design',
      form: {
        b: 300,
        h: 600,
        concrete_grade: 'C30',
        rebar_grade: 'HRB400',
        a_s: 40,
        a_s_prime: 40,
        as_given: null,
        as_prime_given: null,
      },

      // 材料选择器
      concreteGrades: ['C25', 'C30', 'C35', 'C40', 'C45', 'C50', 'C55', 'C60', 'C65', 'C70', 'C75', 'C80'],
      rebarGrades: ['HPB300', 'HRB400', 'HRB500'],
      concreteIndex: 1,
      rebarIndex: 1,

      // 状态
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
      if (s === 'over_reinforced') return 'status-error'
      if (s === 'under_reinforced') return 'status-warn'
      return 'status-warn'
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

    async doCalculate() {
      // 校验
      if (!this.form.b || !this.form.h) {
        uni.showToast({ title: '请填写截面尺寸', icon: 'none' })
        return
      }
      if (this.mode === 'check' && !this.form.as_given) {
        uni.showToast({ title: '校核模式请输入已知配筋面积', icon: 'none' })
        return
      }
      if (this.asType === 'double' && this.mode === 'check' && !this.form.as_prime_given) {
        uni.showToast({ title: '双筋校核请输入受压钢筋面积', icon: 'none' })
        return
      }

      this.loading = true
      this.result = null

      try {
        const params = {
          b: this.form.b,
          h: this.form.h,
          concrete_grade: this.form.concrete_grade,
          rebar_grade: this.form.rebar_grade,
          a_s: this.form.a_s,
          as_type: this.asType,
        }

        if (this.asType === 'double') {
          params.a_s_prime = this.form.a_s_prime
        }

        if (this.mode === 'check') {
          params.as_given = this.form.as_given
          if (this.asType === 'double') {
            params.as_prime_given = this.form.as_prime_given
          }
        }

        const res = await calcBearingCapacity(params)
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

/* 类型切换 */
.type-toggle {
  display: flex;
  background: #F5F6FA;
  border-radius: 12rpx;
  padding: 6rpx;
}

.type-btn {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #666;
  border-radius: 10rpx;
  transition: all 0.2s;
}

.type-btn.active {
  background: #2C6FCE;
  color: #fff;
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
