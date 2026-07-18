<template>
  <view class="container">
    <!-- 模式切换 -->
    <view class="card">
      <view class="card-title">题型</view>
      <view class="mode-tabs">
        <view v-for="(m, i) in modes" :key="i" class="mode-tab" :class="{on: i===modeIndex}" @click="modeIndex=i;result=null">
          {{ m.short }}
        </view>
      </view>
      <view class="mode-desc">{{ modes[modeIndex].desc }}</view>
    </view>

    <!-- 单位 -->
    <view class="card">
      <view class="card-title">单位</view>
      <view class="unit-row">
        <text>k:</text><picker mode="selector" :range="kUnits" :value="kUnitIndex" @change="(e)=>kUnitIndex=e.detail.value"><view class="chip">{{ kUnits[kUnitIndex] }}</view></picker>
        <text>v:</text><picker mode="selector" :range="vUnits" :value="vUnitIndex" @change="(e)=>vUnitIndex=e.detail.value"><view class="chip">{{ vUnits[vUnitIndex] }}</view></picker>
        <text>Q:</text>
        <text v-if="modeIndex===1" class="chip">m³（累计）</text>
        <picker v-else mode="selector" :range="qUnits" :value="qUnitIndex" @change="(e)=>qUnitIndex=e.detail.value"><view class="chip">{{ qUnits[qUnitIndex] }}</view></picker>
      </view>
    </view>

    <!-- 输入参数 -->
    <view class="card">
      <view class="card-title">已知参数</view>
      <view class="grid-2">
        <view class="form-group" v-for="f in currentFields" :key="f.k">
          <text class="form-label">{{ f.l }}</text>
          <input class="form-input" type="digit" v-model="form[f.k]" :placeholder="f.ph" />
        </view>
      </view>
    </view>

    <!-- 成层土（模式5专用） -->
    <view class="card" v-if="modeIndex===5">
      <view class="card-title">土层</view>
      <view class="grid-2">
        <view class="form-group">
          <text class="form-label">方向</text>
          <picker mode="selector" :range="['水平','垂直']" :value="layerDir" @change="(e)=>layerDir=e.detail.value">
            <view class="form-picker">{{ ['水平','垂直'][layerDir] }}</view>
          </picker>
        </view>
        <view class="form-group">
          <text class="form-label">总水头差 (m)</text>
          <input class="form-input" type="digit" v-model="layerDh" placeholder="如 0.3" />
        </view>
      </view>
      <view v-for="(ly,i) in layers" :key="i" class="ly-row">
        <text class="ly-num">{{ i+1 }}</text>
        <input class="form-input ly-inp" type="digit" v-model="layers[i].kv" placeholder="k" />
        <input class="form-input ly-inp" type="digit" v-model="layers[i].Hv" placeholder="H(m)" />
        <view v-if="layers.length>2" class="ly-del" @click="layers.splice(i,1)">✕</view>
      </view>
      <view class="ly-add" @click="layers.push({kv:null,Hv:null})">+ 添加土层</view>
      <view v-if="lyResult" class="ly-result">
        <text>kₑq = {{ lyResult.ke }} {{ kUnits[kUnitIndex] }}</text>
        <text v-if="lyResult.pl"> | 各层 Δh: {{ lyResult.pl }}</text>
      </view>
    </view>

    <button class="btn-primary" :disabled="loading" @click="doCalc">
      {{ loading ? '计算中...' : '开始计算' }}
    </button>

    <view class="card" v-if="result">
      <view class="result-grid">
        <view class="rg-item" v-for="r in showResults" :key="r.k">
          <text class="rg-label">{{ r.k }}</text>
          <text class="rg-val">{{ r.v }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-title">公式</view>
      <view class="fm"><rich-text :nodes="formulaHtml('v = k · i')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('Q = k · i · A')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('i = Δh / L')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('k = Q · L / (A · Δh · t)')"></rich-text><text class="fm-note">常水头试验</text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('k = a · L / (A · t) · ln(h₁ / h₂)')"></rich-text><text class="fm-note">变水头试验</text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('j = γ_w · i')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('J = j · V')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('i_cr = γ′ / γ_w = (G_s − 1) / (1 + e)')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('k_h = Σ(k_i · H_i) / ΣH_i')"></rich-text></view>
      <view class="fm"><rich-text :nodes="formulaHtml('k_v = ΣH_i / Σ(H_i / k_i)')"></rich-text></view>
    </view>
  </view>
</template>

<script>
import { calcDarcyLaw } from '@/utils/api.js'

const FIELD_SETS = [
  [{k:'k',l:'渗透系数 k',ph:'如 0.0001'},{k:'i',l:'水力梯度 i',ph:'如 0.5'},{k:'delta_h',l:'水头差 Δh (m)',ph:'如 0.3'},{k:'L',l:'渗径 L (m)',ph:'如 0.8'},{k:'A',l:'截面积 A (m²)',ph:'如需 Q'}],
  [{k:'Q',l:'总水量 Q (m³)',ph:'如 0.002'},{k:'L',l:'试样长度 L (m)',ph:'如 0.2'},{k:'A',l:'截面积 A (m²)',ph:'如 0.01'},{k:'delta_h',l:'水头差 Δh (m)',ph:'如 1.5'},{k:'t',l:'时间 t (s)',ph:'如 600'}],
  [{k:'a',l:'细管截面积 a (cm²)',ph:'如 0.785'},{k:'L',l:'试样长度 L (m)',ph:'如 0.1'},{k:'A',l:'截面积 A (m²)',ph:'如 0.005'},{k:'h1',l:'初始水头 h₁ (cm)',ph:'如 120'},{k:'h2',l:'终止水头 h₂ (cm)',ph:'如 80'},{k:'t',l:'时间 t (s)',ph:'如 3600'}],
  [{k:'i',l:'水力梯度 i',ph:'如 0.5'},{k:'V',l:'土体体积 V (m³)',ph:'如需 J'},{k:'gamma_w',l:'水的重度 γw',ph:'默认 9.81'}],
  [{k:'Gs',l:'土粒比重 Gₛ',ph:'如 2.70'},{k:'e',l:'孔隙比 e',ph:'如 0.65'},{k:'gamma_prime',l:'有效重度 γ′ (kN/m³)',ph:'或直接填'},{k:'i',l:'实际水力梯度 i',ph:'判断安全'}],
  [], // 成层土用自己的输入
]

export default {
  data() {
    return {
      modeIndex: 0,
      modes: [
        {short:'基础渗流',desc:'已知 k、i(或Δh/L)、A，求 v 和 Q'},
        {short:'常水头',desc:'已知 Q、A、L、Δh、t，反求 k（砂土）'},
        {short:'变水头',desc:'已知 a、A、L、h₁h₂、t，反求 k（粘土）'},
        {short:'渗透力',desc:'已知 i、V，求 j 和 J'},
        {short:'临界梯度',desc:'已知 Gₛ、e（或 γ′），求 i 下标 cr，判别流土'},
        {short:'成层土',desc:'各层 kᵢ、Hᵢ → 等效 kₑq'},
      ],
      kUnits: ['m/s','cm/s','m/d'], kUnitIndex: 0,
      vUnits: ['m/s','cm/s','mm/s'], vUnitIndex: 0,
      qUnits: ['m³/s','cm³/s','L/s'], qUnitIndex: 0,
      form: {k:null,i:null,delta_h:null,L:null,Q:null,v:null,A:null,t:null,a:null,h1:null,h2:null,j:null,J:null,V:null,i_cr:null,gamma_prime:null,Gs:null,e:null,Fs:null,gamma_w:null},
      layers: [{kv:null,Hv:null},{kv:null,Hv:null}],
      layerDir: 0,
      layerDh: null,
      lyResult: null,
      loading: false,
      result: null,
      _ku:0,_vu:0,_qu:0,
    }
  },
  computed: {
    currentFields() { return FIELD_SETS[this.modeIndex] || [] },
    showResults() {
      const d = this.result?.data; if (!d) return []
      const ku = this.kUnits[this._ku||0], vu = this.vUnits[this._vu||0], qu = this.qUnits[this._qu||0]
      const kf = {m:1, c:100, d:86400}[ku[0]] || 1
      const vf = {'m/s':1, 'cm/s':100, 'mm/s':1000}[vu] || 1
      const qf = {m:1, c:1e6, L:1000}[qu[0]] || 1
      const f = (v,d) => v!=null ? (typeof v==='number'?v.toFixed(d):v) : '--'
      const fs = (v) => { if(v==null) return '--'; const a=Math.abs(v); if(a===0) return '0'; if(a>=0.001&&a<1e4) return v.toFixed(6); const e=Math.floor(Math.log10(a)); return (v/Math.pow(10,e)).toFixed(3)+'e'+e }
      const items = [
        {k:'渗透系数 k', v: fs(d.k*kf)+' '+ku},
        {k:'水力梯度 i', v: f(d.i,4)},
        {k:'水头差 Δh', v: f(d.delta_h,4)+' m'},
        {k:'渗径 L', v: f(d.L,4)+' m'},
        {k:'渗透速度 v', v: f(d.v*vf,6)+' '+vu},
        {k:this.modeIndex===1?'累计水量 Q':'渗流量 Q', v:this.modeIndex===1 ? fs(d.Q)+' m³' : fs(d.Q*qf)+' '+qu},
        {k:'截面积 A', v: f(d.A,4)+' m²'},
        {k:'渗透力 j', v: f(d.j,4)+' kN/m³'},
        {k:'总渗透力 J', v: f(d.J,4)+' kN'},
        {k:'临界梯度 i꜀ᵣ', v: f(d.i_cr,4)},
        {k:'安全系数 Fs', v: f(d.Fs,4)},
      ]
      return items.filter(it => !it.v.startsWith('--'))
    },
  },
  methods: {
    formulaHtml(value) {
      if (value === null || value === undefined) return ''
      const safe = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      return safe.replace(/([A-Za-z\u0370-\u03FF]+)_([A-Za-z0-9]+)/g, '$1<sub style="font-size:70%;line-height:0;vertical-align:sub;">$2</sub>')
    },
    async doCalc() {
      let Keq=null, Lsum=null, Dh=null
      if (this.modeIndex===5) {
        const raw = this.layers.filter(ly=>{const k=parseFloat(ly.kv),h=parseFloat(ly.Hv); return !isNaN(k)&&k>0&&!isNaN(h)&&h>0})
        if (raw.length<2) { uni.showToast({title:'请填写至少2层',icon:'none'}); return }
        Lsum = raw.reduce((s,ly)=>s+parseFloat(ly.Hv),0)
        if (this.layerDir===0) {
          Keq = raw.reduce((s,ly)=>s+parseFloat(ly.kv)*parseFloat(ly.Hv),0)/Lsum
        } else {
          Keq = Lsum/raw.reduce((s,ly)=>s+parseFloat(ly.Hv)/parseFloat(ly.kv),0)
        }
        Dh = this.layerDh ? parseFloat(this.layerDh) : null
        // 水头分配
        let plStr = ''
        if (this.layerDir===1 && Dh && Dh>0) {
          const vv = Keq*Dh/Lsum; const parts=[]; let sd=0
          for(const ly of raw){const k=parseFloat(ly.kv),H=parseFloat(ly.Hv),dh=(vv/k)*H; parts.push((dh*100).toFixed(1)+'cm'); sd+=dh}
          plStr = parts.join(', ')
        }
        this.lyResult = {ke:Keq, pl:plStr||null}
      }
      this.loading=true; this.result=null
      const kf2ms = [1,0.01,1/86400][this.kUnitIndex]
      const vf2ms = [1,0.01,0.001][this.vUnitIndex]
      const qf2ms = [1,1e-6,0.001][this.qUnitIndex]
      try {
        const p = {}
        if (Keq!==null) {
          p.k = Keq; p.L = Lsum
          if (Dh && !isNaN(Dh)) p.delta_h = Dh
          for(const k of ['A','t','gamma_w']) { if(this.form[k]!=null&&this.form[k]!=='') p[k]=parseFloat(this.form[k]) }
        } else {
          for(const [k,v] of Object.entries(this.form)) { if(v!=null&&v!=='') p[k]=parseFloat(v) }
        }
        if(p.k) p.k*=kf2ms
        if(p.v) p.v*=vf2ms
        if(p.Q && this.modeIndex!==1) p.Q*=qf2ms
        this.result = await calcDarcyLaw(p)
        this._ku=this.kUnitIndex; this._vu=this.vUnitIndex; this._qu=this.qUnitIndex
      } catch(e) {
        uni.showToast({title:'失败: '+(e.data?.detail||e.message||'网络错误'),icon:'none',duration:3000})
      } finally { this.loading=false }
    },
  },
}
</script>

<style scoped>
.container { padding-bottom: 40rpx; }
.card-title { font-size: 30rpx; font-weight: 600; color: #222; margin-bottom: 16rpx; padding-bottom: 12rpx; border-bottom: 1rpx solid #eee; }
.mode-tabs { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 12rpx; }
.mode-tab { padding: 10rpx 18rpx; font-size: 24rpx; border-radius: 8rpx; background: #f0f0f0; color: #666; }
.mode-tab.on { background: #14575B; color: #fff; }
.mode-desc { font-size: 24rpx; color: #888; line-height: 1.6; }
.unit-row { display: flex; align-items: center; gap: 10rpx; font-size: 24rpx; color: #666; }
.chip { padding: 6rpx 14rpx; background: #E0EFED; color: #14575B; border-radius: 8rpx; font-weight: 600; font-size: 22rpx; }
.ly-row { display: flex; align-items: center; gap: 10rpx; margin: 8rpx 0; }
.ly-num { width: 36rpx; height: 36rpx; line-height: 36rpx; text-align: center; background: #2C8884; color: #fff; border-radius: 50%; font-size: 20rpx; font-weight: 700; }
.ly-inp { flex: 1; }
.ly-del { color: #E53935; font-size: 28rpx; padding: 8rpx; }
.ly-add { color: #14575B; font-size: 24rpx; padding: 12rpx; text-align: center; border: 2rpx dashed #9EC7C3; border-radius: 10rpx; margin-top: 8rpx; }
.ly-result { margin-top: 12rpx; padding: 14rpx; background: #E0EFED; border-radius: 10rpx; font-size: 26rpx; font-weight: 600; color: #17383A; }
.result-grid { display: flex; flex-wrap: wrap; }
.rg-item { width: 50%; padding: 12rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.rg-item:nth-child(odd) { padding-right: 12rpx; border-right: 1rpx solid #f5f5f5; box-sizing: border-box; }
.rg-item:nth-child(even) { padding-left: 12rpx; box-sizing: border-box; }
.rg-label { display: block; font-size: 22rpx; color: #888; }
.rg-val { display: block; font-size: 26rpx; font-weight: 600; color: #222; }
.fm {font-size:29rpx;color:#14575B;padding:18rpx 4rpx;border-bottom:1rpx solid #E5E7E3;font-family:Georgia,'Times New Roman',serif;font-variant-numeric:lining-nums tabular-nums;line-height:1.6;letter-spacing:.4rpx}.fm-note{display:block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:21rpx;color:#8A9694;margin-top:4rpx}
</style>
