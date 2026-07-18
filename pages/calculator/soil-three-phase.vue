<template>
  <view class="container">
    <!-- 输入卡片 -->
    <view class="card">
      <view class="card-title">已知指标（填入你已知的值，≥3 个）</view>
      <view class="card-hint">注：含水量、孔隙率、饱和度以小数输入（如 15% → 0.15）</view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">土粒比重 Gₛ</text>
          <input class="form-input" v-model="form.Gs" type="digit" placeholder="必填，如 2.70" />
        </view>
        <view class="form-group">
          <text class="form-label">含水量 w</text>
          <input class="form-input" v-model="form.w" type="digit" placeholder="如 0.15" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">天然重度 γ (kN/m³)</text>
          <input class="form-input" v-model="form.gamma" type="digit" placeholder="如 18.5" />
        </view>
        <view class="form-group">
          <text class="form-label">干重度 γd (kN/m³)</text>
          <input class="form-input" v-model="form.gamma_d" type="digit" placeholder="如 16.1" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">饱和重度 γₛₐₜ (kN/m³)</text>
          <input class="form-input" v-model="form.gamma_sat" type="digit" placeholder="如 20.5" />
        </view>
        <view class="form-group">
          <text class="form-label">有效重度 γ′ (kN/m³)</text>
          <input class="form-input" v-model="form.gamma_prime" type="digit" placeholder="如 10.2" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">孔隙比 e</text>
          <input class="form-input" v-model="form.e" type="digit" placeholder="如 0.65" />
        </view>
        <view class="form-group">
          <text class="form-label">孔隙率 n</text>
          <input class="form-input" v-model="form.n" type="digit" placeholder="如 0.39" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">饱和度 Sᵣ</text>
          <input class="form-input" v-model="form.Sr" type="digit" placeholder="如 0.62（1.0=饱和）" />
        </view>
        <view class="form-group">
          <text class="form-label">天然密度 ρ (g/cm³)</text>
          <input class="form-input" v-model="form.rho" type="digit" placeholder="如 1.89" />
        </view>
      </view>

      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">干密度 ρd (g/cm³)</text>
          <input class="form-input" v-model="form.rho_d" type="digit" placeholder="如 1.64" />
        </view>
        <view class="form-group">
          <text class="form-label">水的重度 γw (kN/m³)</text>
          <input class="form-input" v-model="form.gamma_w" type="digit" placeholder="默认 9.81，考试常用 10" />
        </view>
      </view>

      <view class="preset-hint">
        <text>常见 Gₛ 参考：砂土 2.65~2.69 ｜ 粉土 2.70~2.71 ｜ 黏土 2.72~2.75</text>
      </view>
    </view>

    <!-- 计算按钮 -->
    <button class="btn-primary" :disabled="loading" @click="doCalculate">
      {{ loading ? '计算中...' : '开始推导' }}
    </button>

    <!-- 计算结果 -->
    <view class="card" v-if="result">
      <view class="calc-hero">
        <text class="calc-hero-label">天然重度 γ</text>
        <text class="calc-hero-value">{{ result.data.gamma || '—' }}<text class="calc-hero-unit" v-if="result.data.gamma"> kN/m³</text></text>
        <text class="status-tag status-ok">{{ result.message }}</text>
      </view>

      <!-- 三相草图式汇总 -->
      <view class="result-grid" v-if="result.data">
        <view class="rg-item rg-main">
          <text class="rg-label">土粒比重 Gₛ</text>
          <text class="rg-val">{{ fmt(result.data.Gs) }}</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">含水量 w</text>
          <text class="rg-val">{{ fmtPct(result.data.w) }}</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">孔隙比 e</text>
          <text class="rg-val">{{ fmt(result.data.e) }}</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">孔隙率 n</text>
          <text class="rg-val">{{ fmtPct(result.data.n) }}</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">饱和度 Sᵣ</text>
          <text class="rg-val">{{ fmtPct(result.data.Sr) }}</text>
        </view>
        <view class="rg-item rg-main">
          <text class="rg-label">天然重度 γ</text>
          <text class="rg-val">{{ fmt(result.data.gamma) }} kN/m³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">干重度 γd</text>
          <text class="rg-val">{{ fmt(result.data.gamma_d) }} kN/m³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">饱和重度 γₛₐₜ</text>
          <text class="rg-val">{{ fmt(result.data.gamma_sat) }} kN/m³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">有效重度 γ′</text>
          <text class="rg-val">{{ fmt(result.data.gamma_prime) }} kN/m³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">天然密度 ρ</text>
          <text class="rg-val">{{ fmt(result.data.rho) }} g/cm³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">干密度 ρd</text>
          <text class="rg-val">{{ fmt(result.data.rho_d) }} g/cm³</text>
        </view>
        <view class="rg-item">
          <text class="rg-label">饱和密度 ρₛₐₜ</text>
          <text class="rg-val">{{ fmt(result.data.rho_sat) }} g/cm³</text>
        </view>
      </view>

      <!-- γ_w 作用说明 -->
      <view class="gamma-note" v-if="result.data">
        <text class="gamma-note-title">为什么需要 γw？</text>
        <text class="gamma-note-text">土粒比重 Gₛ 是一个<text class="hl">比值</text>（Gₛ = γₛ / γw），本身没有单位。要将无量纲的 Gₛ 换算成实际重度（kN/m³），必须借助 γw 作为“桥梁”。公式中的 γd、γₛₐₜ、γ′ 都直接含有 γw，所以改变 γw（如考试取 10、实际取 9.81）会影响这些结果。</text>
      </view>

      <!-- 推导过程 -->
      <view class="deriv-title" v-if="result.data.derivations && result.data.derivations.length">
        推导过程（共 {{ result.data.derivations.length }} 步）
      </view>
      <view class="deriv-list" v-if="result.data.derivations && result.data.derivations.length">
        <view class="deriv-item" v-for="(d, i) in result.data.derivations" :key="'d'+i">
          <view class="deriv-step-num">{{ i+1 }}</view>
          <view class="deriv-content">
            <text class="deriv-symbol">{{ d.symbol }}</text>
            <text class="deriv-eq">= {{ fmt(d.value) }} <text class="deriv-unit">{{ d.unit }}</text></text>
            <rich-text class="deriv-formula" :nodes="formulaHtml(d.formula)"></rich-text>
          </view>
        </view>
      </view>

      <!-- 未推出项 -->
      <view class="missing-note" v-if="result.data.missing && result.data.missing.length">
        ⚠ 以下指标未能推出：{{ result.data.missing.join(', ') }}
      </view>
    </view>

    <!-- ==================== 公式参考 ==================== -->
    <view class="card">
      <view class="card-title">📖 公式参考说明</view>

      <view class="ref-section">
        <view class="ref-subtitle">一、三相草图法</view>
        <view class="ref-text">
          令土粒体积 <text class="hl">Vₛ = 1</text>，则孔隙体积 Vᵥ = e，总体积 V = 1 + e。在三相草图上标注各相质量和体积，即可推导全部公式。
        </view>
      </view>

      <view class="ref-section">
        <view class="ref-subtitle">二、基本定义</view>
        <view class="formula-list">
          <view class="formula-row">
            <text class="formula-sym">孔隙比</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('e = V_v / V_s')"></rich-text>
            <text class="formula-desc">孔隙体积与土粒体积之比</text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">孔隙率</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('n = V_v / V × 100%')"></rich-text>
            <text class="formula-desc">孔隙体积与总体积之比</text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">含水量</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('w = m_w / m_s × 100%')"></rich-text>
            <text class="formula-desc">水的质量与土粒质量之比</text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">饱和度</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('S_r = V_w / V_v × 100%')"></rich-text>
            <text class="formula-desc">水的体积与孔隙体积之比</text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">土粒比重</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('G_s = ρ_s / ρ_w = γ_s / γ_w')"></rich-text>
            <text class="formula-desc">土粒密度与水密度之比</text>
          </view>
        </view>
      </view>

      <view class="ref-section">
        <view class="ref-subtitle">三、重度换算公式</view>
        <view class="formula-list">
          <view class="formula-row">
            <text class="formula-sym">干重度</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('γ_d = γ / (1 + w) = G_s · γ_w / (1 + e)')"></rich-text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">天然重度</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('γ = G_s · γ_w · (1 + w) / (1 + e)')"></rich-text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">饱和重度</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('γ_sat = (G_s + e) · γ_w / (1 + e)')"></rich-text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">有效重度</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('γ′ = γ_sat − γ_w = (G_s − 1) · γ_w / (1 + e)')"></rich-text>
          </view>
        </view>
      </view>

      <view class="ref-section">
        <view class="ref-subtitle">四、相互换算</view>
        <view class="formula-list">
          <view class="formula-row">
            <text class="formula-sym">n ↔ e</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('n = e / (1 + e)，e = n / (1 − n)')"></rich-text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">Sᵣ 关联式</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('S_r · e = w · G_s（核心等式）')"></rich-text>
          </view>
          <view class="formula-row">
            <text class="formula-sym">饱和时</text>
            <rich-text class="formula-eq" :nodes="formulaHtml('S_r = 1 → e = w · G_s')"></rich-text>
          </view>
        </view>
      </view>

      <view class="ref-section">
        <view class="ref-subtitle">五、重度大小关系</view>
        <view class="ref-text ref-order">
          <text class="hl">γₛₐₜ ＞ γ ＞ γd ＞ γ′</text>
        </view>
        <view class="ref-text">即：饱和重度 > 天然重度 > 干重度 > 有效重度</view>
      </view>

      <view class="ref-section">
        <view class="ref-subtitle">六、符号说明</view>
        <view class="symbol-table">
          <view class="sym-row sym-header">
            <text class="sym-col sym-col-sym">符号</text>
            <text class="sym-col sym-col-name">名称</text>
            <text class="sym-col sym-col-unit">单位</text>
            <text class="sym-col sym-col-def">定义</text>
          </view>
          <view class="sym-row"><text class="sym-col sym-col-sym">Gₛ</text><text class="sym-col sym-col-name">土粒比重</text><text class="sym-col sym-col-unit">—</text><text class="sym-col sym-col-def">ρₛ / ρw</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">w</text><text class="sym-col sym-col-name">含水量</text><text class="sym-col sym-col-unit">%</text><text class="sym-col sym-col-def">mᵥ / mₛ</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">γ</text><text class="sym-col sym-col-name">天然重度</text><text class="sym-col sym-col-unit">kN/m³</text><text class="sym-col sym-col-def">W/V</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">γd</text><text class="sym-col sym-col-name">干重度</text><text class="sym-col sym-col-unit">kN/m³</text><text class="sym-col sym-col-def">Wₛ / V</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">γₛₐₜ</text><text class="sym-col sym-col-name">饱和重度</text><text class="sym-col sym-col-unit">kN/m³</text><text class="sym-col sym-col-def">孔隙全充满水</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">γ′</text><text class="sym-col sym-col-name">有效重度</text><text class="sym-col sym-col-unit">kN/m³</text><text class="sym-col sym-col-def">γₛₐₜ − γw</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">e</text><text class="sym-col sym-col-name">孔隙比</text><text class="sym-col sym-col-unit">—</text><text class="sym-col sym-col-def">Vᵥ / Vₛ</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">n</text><text class="sym-col sym-col-name">孔隙率</text><text class="sym-col sym-col-unit">%</text><text class="sym-col sym-col-def">Vᵥ / V</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">Sᵣ</text><text class="sym-col sym-col-name">饱和度</text><text class="sym-col sym-col-unit">%</text><text class="sym-col sym-col-def">Vw / Vᵥ</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">ρ</text><text class="sym-col sym-col-name">天然密度</text><text class="sym-col sym-col-unit">g/cm³</text><text class="sym-col sym-col-def">m/V</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">ρd</text><text class="sym-col sym-col-name">干密度</text><text class="sym-col sym-col-unit">g/cm³</text><text class="sym-col sym-col-def">mₛ / V</text></view>
          <view class="sym-row"><text class="sym-col sym-col-sym">γw</text><text class="sym-col sym-col-name">水的重度</text><text class="sym-col sym-col-unit">kN/m³</text><text class="sym-col sym-col-def">≈ 9.81（或 10）</text></view>
        </view>
      </view>
    </view>

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script>
import { calcSoilThreePhase } from '@/utils/api.js'

export default {
  data() {
    return {
      form: {
        Gs: null, w: null, gamma: null, gamma_d: null,
        gamma_sat: null, gamma_prime: null,
        e: null, n: null, Sr: null,
        rho: null, rho_d: null,
        gamma_w: null,
      },
      loading: false,
      result: null,
    }
  },

  methods: {
    formulaHtml(value) {
      if (value === null || value === undefined) return ''
      const safe = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      return safe.replace(/([A-Za-z\u0370-\u03FF]+)_([A-Za-z0-9]+)/g, '$1<sub style="font-size:70%;line-height:0;vertical-align:sub;">$2</sub>')
    },
    async doCalculate() {
      if (!this.form.Gs && !this.form.w && !this.form.gamma && !this.form.gamma_d
        && !this.form.e && !this.form.n && !this.form.Sr && !this.form.rho && !this.form.rho_d) {
        uni.showToast({ title: '请至少填写 2-3 个已知指标', icon: 'none' })
        return
      }
      if (!this.form.Gs) {
        uni.showToast({ title: '土粒比重 Gₛ 为必填项', icon: 'none' })
        return
      }

      this.loading = true
      this.result = null
      try {
        const params = {}
        for (const [k, v] of Object.entries(this.form)) {
          if (v !== null && v !== '' && v !== undefined) {
            params[k] = parseFloat(v)
          }
        }
        this.result = await calcSoilThreePhase(params)
      } catch (e) {
        console.error('计算失败:', e)
      } finally {
        this.loading = false
      }
    },

    fmt(val) {
      if (val === null || val === undefined) return '—'
      return parseFloat(val).toFixed(4)
    },

    fmtPct(val) {
      if (val === null || val === undefined) return '—'
      return (parseFloat(val) * 100).toFixed(2) + '%'
    },
  },
}
</script>

<style scoped>
.container { padding-bottom: 40rpx; }

/* ========== 卡片标题 ========== */
.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #222;
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

.card-hint {
  font-size: 22rpx;
  color: #999;
  margin-bottom: 20rpx;
  margin-top: -12rpx;
}

.preset-hint {
  margin-top: 12rpx;
  padding: 12rpx 16rpx;
  background: #F5F7FA;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #888;
}

/* ========== 结果网格 ========== */
.result-grid {
  display: flex;
  flex-wrap: wrap;
  margin-top: 16rpx;
}

.rg-item {
  width: 50%;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.rg-item:nth-child(odd) {
  padding-right: 16rpx;
  border-right: 1rpx solid #f5f5f5;
  box-sizing: border-box;
}

.rg-item:nth-child(even) {
  padding-left: 16rpx;
  box-sizing: border-box;
}

.rg-label {
  display: block;
  font-size: 22rpx;
  color: #888;
  margin-bottom: 4rpx;
}

.rg-val {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #222;
}

.rg-main .rg-val {
  color: #14575B;
  font-size: 30rpx;
}

/* ========== γ_w 说明卡片 ========== */
.gamma-note {
  margin-top: 24rpx;
  padding: 20rpx;
  background: #F0F4FF;
  border-radius: 12rpx;
  border-left: 4rpx solid #14575B;
}

.gamma-note-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: #14575B;
  margin-bottom: 8rpx;
}

.gamma-note-text {
  font-size: 24rpx;
  color: #555;
  line-height: 1.7;
}

/* ========== 推导过程 ========== */
.deriv-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-top: 30rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid #eee;
}

.deriv-list {
  margin-top: 8rpx;
}

.deriv-item {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.deriv-step-num {
  width: 40rpx;
  height: 40rpx;
  line-height: 40rpx;
  text-align: center;
  font-size: 22rpx;
  font-weight: 700;
  color: #fff;
  background: #14575B;
  border-radius: 50%;
  flex-shrink: 0;
  margin-right: 16rpx;
  margin-top: 2rpx;
}

.deriv-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.deriv-symbol {
  font-size: 26rpx;
  font-weight: 700;
  color: #222;
}

.deriv-eq {
  font-size: 28rpx;
  font-weight: 700;
  color: #14575B;
  margin: 4rpx 0;
}

.deriv-unit {
  font-size: 22rpx;
  font-weight: 500;
  color: #999;
}

.deriv-formula {
  display:block;font-size: 25rpx;color: #526B6C;line-height: 1.75;
  font-family: Georgia, 'Times New Roman', serif;
  font-variant-numeric: lining-nums tabular-nums;
  letter-spacing:.4rpx;
}

.missing-note {
  margin-top: 20rpx;
  padding: 12rpx 16rpx;
  background: #FFF8E1;
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #E65100;
}

/* ========== 计算 Hero ========== */
.calc-hero {
  text-align: center;
  padding: 16rpx 0 24rpx;
}
.calc-hero-label { display: block; font-size: 26rpx; color: #666; margin-bottom: 8rpx; }
.calc-hero-value { display: block; font-size: 48rpx; font-weight: 800; color: #111; margin-bottom: 12rpx; }
.calc-hero-unit { font-size: 28rpx; font-weight: 500; color: #999; }

/* ========== 公式参考区 ========== */
.ref-section { margin-top: 24rpx; }
.ref-subtitle {
  font-size: 28rpx; font-weight: 600; color: #333;
  margin-bottom: 12rpx;
  padding-left: 12rpx; border-left: 4rpx solid #14575B;
}
.ref-text { font-size: 24rpx; color: #555; line-height: 1.7; }
.ref-order { text-align: center; padding: 12rpx; background: #F0F4FF; border-radius: 8rpx; margin: 8rpx 0; }

.hl { color: #14575B; font-weight: 600; }

.formula-list { margin-top: 8rpx; }
.formula-row {
  display: flex; align-items: flex-start;
  padding: 18rpx 0; border-bottom: 1rpx solid #E5E7E3;
  flex-wrap: wrap; row-gap:8rpx;
}
.formula-sym {
  width: 112rpx; flex-shrink: 0;
  font-size: 24rpx; font-weight: 650; color: #263F40;
}
.formula-eq {
  flex:1;min-width:420rpx;
  font-size: 29rpx;color:#14575B;
  font-family: Georgia, 'Times New Roman', serif;
  font-variant-numeric: lining-nums tabular-nums;
  line-height:1.65;letter-spacing:.5rpx;
}
.formula-desc {
  width:100%;font-size: 22rpx;color:#8A9694;margin-left:112rpx;line-height:1.55;
}

/* ========== 符号表 ========== */
.symbol-table {
  margin-top: 8rpx;
  border: 1rpx solid #eee;
  border-radius: 8rpx;
  overflow: hidden;
}

.sym-row {
  display: flex;
  padding: 12rpx 8rpx;
  border-bottom: 1rpx solid #f5f5f5;
}

.sym-row:last-child { border-bottom: none; }

.sym-header {
  background: #F5F7FA;
}

.sym-header .sym-col {
  font-weight: 600;
  color: #555;
  font-size: 22rpx;
}

.sym-col {
  font-size: 22rpx;
  color: #333;
}

.sym-col-sym { width: 60rpx; flex-shrink: 0; text-align: center; font-weight: 600; }
.sym-col-name { flex: 1; }
.sym-col-unit { width: 90rpx; flex-shrink: 0; text-align: center; }
.sym-col-def { flex: 1.2; color: #666; }

/* ========== 状态标签 ========== */
.status-tag {
  display: inline-block;
  padding: 6rpx 20rpx; border-radius: 24rpx;
  font-size: 24rpx; font-weight: 500;
}
.status-ok { background: #E8F5E9; color: #2E7D32; }
</style>
