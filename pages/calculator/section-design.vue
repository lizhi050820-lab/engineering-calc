<template>
  <view class="page">
    <!-- ========== 输入区 ========== -->
    <view class="card">
      <view class="card-title">截面参数</view>

      <!-- 截面尺寸 -->
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">截面宽度 b (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.b" placeholder="如 300" />
        </view>
        <view class="form-group">
          <text class="form-label">截面高度 h (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.h" placeholder="如 600" />
        </view>
      </view>

      <!-- 材料 -->
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

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">保护层 a_s (mm)</text>
          <input class="form-input" type="digit" v-model.number="form.a_s" placeholder="40" />
        </view>
        <view class="form-group">
          <text class="form-label">箍筋牌号</text>
          <picker :range="stirrupGrades" :value="stirrupIndex" @change="onStirrupChange">
            <view class="form-picker">{{ form.stirrup_grade }}</view>
          </picker>
        </view>
      </view>
    </view>

    <!-- 荷载类型 -->
    <view class="card">
      <view class="card-title">荷载与箍筋</view>

      <view class="form-group">
        <text class="form-label">荷载类型</text>
        <view class="type-toggle">
          <view
            class="type-btn" :class="{ active: form.load_type === 'uniform' }"
            @click="form.load_type = 'uniform'"
          >均布荷载</view>
          <view
            class="type-btn" :class="{ active: form.load_type === 'concentrated' }"
            @click="form.load_type = 'concentrated'"
          >集中荷载</view>
        </view>
      </view>

      <view class="form-group" v-if="form.load_type === 'concentrated'">
        <text class="form-label">剪跨比 λ (1.5~3.0)</text>
        <input class="form-input" type="digit" v-model.number="form.shear_span_ratio" placeholder="2.0" />
      </view>

      <!-- 校核/设计 toggle -->
      <view class="form-group">
        <text class="form-label">计算模式</text>
        <view class="type-toggle">
          <view class="type-btn" :class="{ active: !checkMode }" @click="checkMode = false">设计模式</view>
          <view class="type-btn" :class="{ active: checkMode }" @click="checkMode = true">校核模式</view>
        </view>
      </view>

      <!-- 校核输入 -->
      <view v-if="checkMode">
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">受拉钢筋 As (mm²)</text>
            <input class="form-input" type="digit" v-model.number="form.as_given" placeholder="如 1256" />
          </view>
          <view class="form-group">
            <text class="form-label">箍筋直径 (mm)</text>
            <picker :range="diameterOptions" :value="diameterIndex" @change="onDiameterChange">
              <view class="form-picker">{{ form.stirrup_diameter || '选择' }}</view>
            </picker>
          </view>
        </view>
        <view class="grid-2">
          <view class="form-group">
            <text class="form-label">箍筋肢数</text>
            <picker :range="legOptions" :value="legIndex" @change="onLegChange">
              <view class="form-picker">{{ form.stirrup_legs }} 肢</view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">箍筋间距 (mm)</text>
            <input class="form-input" type="digit" v-model.number="form.stirrup_spacing" placeholder="200" />
          </view>
        </view>
      </view>
    </view>

    <!-- 计算按钮 -->
    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中...' : '计算' }}
    </button>

    <!-- ========== 结果区 ========== -->
    <view v-if="result" class="results">

      <!-- 正截面 -->
      <view class="card">
        <view class="card-title">正截面承载力（受弯）</view>

        <view class="result-card" v-if="result.data.flexural">
          <view class="result-label">
            {{ checkMode ? '极限弯矩 Mu' : '单筋最大承载力 Mu_max' }}
          </view>
          <view class="result-value">
            {{ result.data.flexural.mu }}<text class="result-unit"> kN·m</text>
          </view>
          <view :class="['status-tag', statusFlexClass]">{{ result.data.flexural.status === 'ok' ? '适筋' : result.data.flexural.status }}</view>
        </view>

        <!-- 设计模式 - 配筋表格 -->
        <view v-if="result.data.flexural.design_points" class="params-grid" style="margin-top: 16px;">
          <view class="section-subtitle">配筋方案</view>
          <view v-for="pt in result.data.flexural.design_points" :key="pt.label" class="param-item">
            <text class="param-label">{{ pt.label }}</text>
            <text class="param-value">As={{ pt.As }} mm², Mu={{ pt.Mu }} kN·m</text>
          </view>
        </view>

        <view class="params-grid" style="margin-top: 12px;">
          <view class="param-item">
            <text class="param-label">有效高度 h₀</text>
            <text class="param-value">{{ result.data.flexural.h0 }} mm</text>
          </view>
          <view class="param-item">
            <text class="param-label">ξb</text>
            <text class="param-value">{{ result.data.flexural.xi_b }}</text>
          </view>
          <view class="param-item">
            <text class="param-label">ρ_min</text>
            <text class="param-value">{{ result.data.flexural.rho_min }}</text>
          </view>
          <view class="param-item">
            <text class="param-label">ρ_max</text>
            <text class="param-value">{{ result.data.flexural.rho_max }}</text>
          </view>
        </view>
      </view>

      <!-- 斜截面 -->
      <view class="card">
        <view class="card-title">斜截面受剪承载力</view>

        <view class="result-card" v-if="result.data.shear">
          <view class="result-label">受剪承载力 {{ form.stirrup_diameter ? 'V_cs' : 'V_c' }}</view>
          <view class="result-value">
            {{ form.stirrup_diameter ? result.data.shear.V_cs : result.data.shear.V_c }}<text class="result-unit"> kN</text>
          </view>
          <view :class="['status-tag', statusShearClass]">
            {{ result.data.shear.status === 'ok' ? '满足' : result.data.shear.status }}
          </view>
        </view>

        <view class="params-grid" style="margin-top: 12px;">
          <view class="param-item">
            <text class="param-label">V_c (混凝土项)</text>
            <text class="param-value">{{ result.data.shear.V_c }} kN</text>
          </view>
          <view class="param-item">
            <text class="param-label">V_max (截面限制)</text>
            <text class="param-value">{{ result.data.shear.V_max }} kN</text>
          </view>
          <view class="param-item">
            <text class="param-label">β_h</text>
            <text class="param-value">{{ result.data.shear.beta_h }}</text>
          </view>
          <view class="param-item">
            <text class="param-label">β_c</text>
            <text class="param-value">{{ result.data.shear.beta_c }}</text>
          </view>
          <view class="param-item" v-if="result.data.shear.A_sv > 0">
            <text class="param-label">A_sv</text>
            <text class="param-value">{{ result.data.shear.A_sv }} mm²</text>
          </view>
          <view class="param-item" v-if="result.data.shear.rho_sv > 0">
            <text class="param-label">ρ_sv / ρ_sv,min</text>
            <text class="param-value">{{ result.data.shear.rho_sv }} / {{ result.data.shear.rho_sv_min }}</text>
          </view>
        </view>
      </view>

      <!-- 计算步骤折叠 -->
      <view class="card" v-if="result.data.flexural.steps.length || result.data.shear.steps.length">
        <view class="steps-toggle" @click="showSteps = !showSteps">
          <text>计算步骤</text>
          <text>{{ showSteps ? '▲' : '▼' }}</text>
        </view>
        <view v-if="showSteps" class="steps-box">
          <view class="section-subtitle" style="color:#2C6FCE;">▸ 正截面</view>
          <view v-for="(s, i) in result.data.flexural.steps" :key="'f'+i" class="step-line">{{ s }}</view>
          <view class="section-subtitle" style="color:#E67E22; margin-top:12px;">▸ 斜截面</view>
          <view v-for="(s, i) in result.data.shear.steps" :key="'s'+i" class="step-line">{{ s }}</view>
        </view>
      </view>

    </view>
  </view>
</template>

<script>
import { calcSectionDesign } from '@/utils/api.js'

export default {
  data() {
    return {
      form: {
        b: 300,
        h: 600,
        concrete_grade: 'C30',
        rebar_grade: 'HRB400',
        stirrup_grade: 'HPB300',
        a_s: 40,
        load_type: 'uniform',
        shear_span_ratio: null,
        as_given: null,
        stirrup_diameter: null,
        stirrup_legs: 2,
        stirrup_spacing: null,
      },

      concreteGrades: ['C25', 'C30', 'C35', 'C40', 'C45', 'C50', 'C55', 'C60', 'C65', 'C70', 'C75', 'C80'],
      rebarGrades: ['HPB300', 'HRB400', 'HRB500'],
      stirrupGrades: ['HPB300', 'HRB400'],
      diameterOptions: [6, 8, 10, 12],

      concreteIndex: 1,
      rebarIndex: 1,
      stirrupIndex: 0,
      diameterIndex: 1,
      legOptions: [2, 4],
      legIndex: 0,

      checkMode: false,
      loading: false,
      result: null,
      showSteps: true,
    }
  },

  computed: {
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

    async doCalculate() {
      if (!this.form.b || !this.form.h) {
        uni.showToast({ title: '请填写截面尺寸', icon: 'none' })
        return
      }
      if (this.form.load_type === 'concentrated' && !this.form.shear_span_ratio) {
        uni.showToast({ title: '集中荷载需填写剪跨比 λ', icon: 'none' })
        return
      }

      this.loading = true
      this.result = null

      try {
        const params = { ...this.form }
        if (!this.checkMode) {
          params.as_given = null
          params.stirrup_diameter = null
          params.stirrup_spacing = null
        }
        const res = await calcSectionDesign(params)
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
.page {
  padding: 16px;
}

.results {
  margin-top: 16px;
}

.section-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
  width: 100%;
  grid-column: 1 / -1;
}

.type-toggle {
  display: flex;
  background: #f0f2f5;
  border-radius: 8px;
  padding: 3px;
}
.type-btn {
  flex: 1;
  text-align: center;
  padding: 8px;
  font-size: 14px;
  color: #666;
  border-radius: 6px;
}
.type-btn.active {
  background: #2C6FCE;
  color: #fff;
}
</style>
