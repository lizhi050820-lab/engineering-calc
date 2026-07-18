<template>
  <view class="page">
    <view class="hero">
      <view class="eyebrow">STRUCTURAL MECHANICS</view>
      <view class="hero-title">梁内力速算</view>
      <view class="hero-subtitle">组合多项荷载，计算支座反力、剪力和弯矩极值</view>

      <view class="beam-tabs">
        <view v-for="item in beamTypes" :key="item.value" class="beam-tab" :class="{active: form.beam_type === item.value}" @click="setBeamType(item.value)">
          <text>{{ item.name }}</text>
          <small>{{ item.desc }}</small>
        </view>
      </view>
    </view>

    <view class="workspace">
      <view class="section-head">
        <view>
          <view class="section-title">建立梁模型</view>
          <view class="section-note">所有位置均从梁左端 x = 0 起算</view>
        </view>
        <view class="completion">{{ readyCount }}/{{ requiredCount }}</view>
      </view>

      <view class="dimension-row">
        <view class="param-block grow">
          <view class="param-label">梁总长 Lt</view>
          <view class="unit-input"><input type="digit" v-model="form.L" @input="lengthChanged" /><text>m</text></view>
        </view>
      </view>

      <view v-if="form.beam_type === 'simply_supported'" class="support-panel">
        <view class="support-panel-head">
          <view>
            <view class="section-title tiny">支座位置</view>
            <view class="section-note">支座 A、B 均从梁左端起算</view>
          </view>
          <view class="layout-name">{{ layoutName }}</view>
        </view>
        <view class="field-grid">
          <view class="param-block">
            <view class="param-label">A 支座位置 xA</view>
            <view class="unit-input"><input type="digit" v-model="form.support_a" @input="clearResult" /><text>m</text></view>
          </view>
          <view class="param-block">
            <view class="param-label">B 支座位置 xB</view>
            <view class="unit-input"><input type="digit" v-model="form.support_b" @input="clearResult" /><text>m</text></view>
          </view>
        </view>
        <view class="preset-row">
          <view v-for="item in supportPresets" :key="item.value" @click="applyPreset(item.value)">{{ item.name }}</view>
        </view>
      </view>

      <view v-else class="support-panel">
        <view class="param-label">固定端位置</view>
        <view class="direction-tabs">
          <view :class="{active:form.fixed_end==='left'}" @click="setFixedEnd('left')">左端固定 ▌</view>
          <view :class="{active:form.fixed_end==='right'}" @click="setFixedEnd('right')">右端固定 ▐</view>
        </view>
      </view>

      <view class="beam-sketch">
        <view class="sketch-axis">x = 0</view>
        <view class="beam-line">
          <view v-if="form.beam_type === 'cantilever'" class="support fixed movable" :style="fixedSupportStyle">{{ form.fixed_end === 'left' ? '▌' : '▐' }}<small>固定端</small></view>
          <template v-else>
            <view class="support movable" :style="supportAStyle">△<small>A · 铰</small></view>
            <view class="support roller movable" :style="supportBStyle">△<i>○</i><small>B · 滚</small></view>
          </template>
          <view v-for="load in loads" :key="'mark-'+load.id" class="load-visual">
            <view v-if="load.type === 'point'" class="point-mark" :style="pointStyle(load)"><text>P↓</text></view>
            <view v-else-if="load.type === 'moment'" class="moment-mark" :style="pointStyle(load)"><text>{{ load.direction === 'clockwise' ? 'M↻' : 'M↺' }}</text></view>
            <view v-else class="udl-mark" :style="udlStyle(load)"><text>q↓↓↓</text></view>
          </view>
        </view>
        <view class="sketch-label">梁总长 {{ displayTotalLength }} m · {{ supportSummary }} · {{ loads.length }} 项荷载</view>
      </view>

      <view class="load-head">
        <view>
          <view class="section-title small">荷载清单</view>
          <view class="section-note">不同荷载可同时添加，同类荷载也可重复添加</view>
        </view>
        <view class="load-count">{{ loads.length }} 项</view>
      </view>

      <view class="add-row">
        <view v-for="item in loadTypes" :key="item.value" class="add-load" @click="addLoad(item.value)">
          <text class="add-icon">＋</text><text>{{ item.name }}</text>
        </view>
      </view>

      <view v-if="loads.length === 0" class="empty-load">
        <view class="empty-title">还没有荷载</view>
        <view>点击上方按钮添加集中力、均布荷载或集中弯矩</view>
      </view>

      <view v-for="(load,index) in loads" :key="load.id" class="load-card">
        <view class="load-card-head">
          <view class="load-title">
            <view class="load-number">{{ index + 1 }}</view>
            <view>
              <strong>{{ loadName(load.type) }}</strong>
              <small>{{ loadHint(load.type) }}</small>
            </view>
          </view>
          <view class="delete-load" @click="removeLoad(index)">删除</view>
        </view>

        <view class="field-grid">
          <view class="param-block">
            <view class="param-label">{{ valueLabel(load.type) }}</view>
            <view class="unit-input"><input type="digit" v-model="load.value" @input="clearResult" /><text>{{ valueUnit(load.type) }}</text></view>
          </view>

          <view v-if="load.type !== 'udl'" class="param-block">
            <view class="param-label">作用位置 x</view>
            <view class="unit-input"><input type="digit" v-model="load.x" @input="clearResult" /><text>m</text></view>
          </view>

          <template v-else>
            <view class="param-block">
              <view class="param-label">荷载起点 x₁</view>
              <view class="unit-input"><input type="digit" v-model="load.x1" @input="clearResult" /><text>m</text></view>
            </view>
            <view class="param-block">
              <view class="param-label">荷载终点 x₂</view>
              <view class="unit-input"><input type="digit" v-model="load.x2" @input="clearResult" /><text>m</text></view>
            </view>
          </template>
        </view>

        <view v-if="load.type === 'moment'" class="direction-block">
          <view class="param-label">弯矩方向</view>
          <view class="direction-tabs">
            <view :class="{active:load.direction==='clockwise'}" @click="setDirection(load,'clockwise')">顺时针 ↻</view>
            <view :class="{active:load.direction==='counterclockwise'}" @click="setDirection(load,'counterclockwise')">逆时针 ↺</view>
          </view>
        </view>
      </view>

      <view class="smart-tip">
        <view class="tip-dot"></view>
        <view>局部均布荷载只需填写 x₁～x₂；满跨荷载填写 0～梁总长即可。</view>
      </view>
    </view>

    <view v-if="result" class="result-panel">
      <view class="result-head">
        <view>
          <view class="result-kicker">计算完成</view>
          <view class="result-title">组合荷载 · {{ result.key_values.load_count }} 项</view>
        </view>
        <view class="result-status">静定梁</view>
      </view>

      <view class="result-grid">
        <view><text>RA</text><strong>{{ result.RA }} kN</strong></view>
        <view v-if="result.RB !== null"><text>RB</text><strong>{{ result.RB }} kN</strong></view>
        <view v-if="result.fixed_moment !== null"><text>固定端反力矩 MF</text><strong>{{ result.fixed_moment }} kN·m</strong></view>
        <view><text>|V|max</text><strong>{{ result.Vmax }} kN</strong></view>
        <view><text>|M|max</text><strong>{{ result.Mmax }} kN·m</strong></view>
        <view><text>绝对最大弯矩位置</text><strong>x = {{ result.x_Mmax }} m</strong></view>
        <view><text>最大正弯矩 M⁺max</text><strong>{{ result.M_positive }} kN·m</strong><small>x = {{ result.x_M_positive }} m</small></view>
        <view><text>最大负弯矩 M⁻min</text><strong>{{ result.M_negative }} kN·m</strong><small>x = {{ result.x_M_negative }} m</small></view>
      </view>

      <view class="sign-tip">正值表示下缘受拉（正弯矩），负值表示上缘受拉（负弯矩）。</view>
      <view class="steps-title" @click="showSteps=!showSteps">
        <text>查看计算步骤</text>
        <text>{{ showSteps ? '收起' : '展开' }}</text>
      </view>
      <view v-if="showSteps" class="steps">
        <view v-for="(step,i) in result.steps" :key="i" class="step">
          <text>{{ i + 1 }}</text>
          <view>{{ step }}</view>
        </view>
      </view>
    </view>

    <view class="action-bar">
      <view class="readiness">
        <view class="ready-dots"><view v-for="i in Math.max(requiredCount,1)" :key="i" class="ready-dot" :class="{on:i<=readyCount}"></view></view>
        <text>{{ canCalculate ? '模型已就绪' : '请完善梁与荷载参数' }}</text>
      </view>
      <button class="calc-btn" :loading="loading" @click="calculate">{{ result ? '重新计算' : '开始计算' }}</button>
    </view>
  </view>
</template>

<script>
import { calcBeamForces } from '../../utils/api.js'

export default {
  data() {
    return {
      beamTypes: [
        { value:'simply_supported', name:'两支座梁', desc:'A、B 可移动' },
        { value:'cantilever', name:'悬臂梁', desc:'固定端可切换' },
      ],
      supportPresets: [
        { value:'simple', name:'简支' },
        { value:'left', name:'左外伸' },
        { value:'right', name:'右外伸' },
        { value:'double', name:'双外伸' },
      ],
      loadTypes: [
        { value:'point', name:'集中力' },
        { value:'udl', name:'均布荷载' },
        { value:'moment', name:'集中弯矩' },
      ],
      form: { beam_type:'simply_supported', L:'6', support_a:'0', support_b:'6', fixed_end:'left' },
      lastLength:'6',
      loads: [{ id:1, type:'point', value:'40', x:'3', x1:'', x2:'', direction:'clockwise' }],
      nextId:2,
      loading:false,
      result:null,
      showSteps:false,
    }
  },
  computed: {
    totalLength() {
      const L = parseFloat(this.form.L)
      return Number.isFinite(L) ? L : 0
    },
    displayTotalLength() { return this.totalLength > 0 ? this.totalLength.toFixed(3) : '—' },
    supportAStyle() { return {left:`${this.percent(this.form.support_a)}%`} },
    supportBStyle() { return {left:`${this.percent(this.form.support_b)}%`} },
    fixedSupportStyle() { return {left:this.form.fixed_end==='left'?'0%':'100%',transform:this.form.fixed_end==='left'?'none':'translateX(-100%)'} },
    layoutName() {
      if (!this.supportsValid) return '待完善'
      const a=parseFloat(this.form.support_a), b=parseFloat(this.form.support_b), L=this.totalLength
      if (a===0 && b===L) return '简支梁'
      if (a>0 && b===L) return '左外伸梁'
      if (a===0 && b<L) return '右外伸梁'
      return '双外伸梁'
    },
    supportSummary() { return this.form.beam_type==='cantilever' ? `${this.form.fixed_end==='left'?'左':'右'}端固定` : this.layoutName },
    supportsValid() {
      const a=parseFloat(this.form.support_a), b=parseFloat(this.form.support_b)
      return Number.isFinite(a) && Number.isFinite(b) && a>=0 && a<b && b<=this.totalLength
    },
    requiredCount() {
      let count = this.form.beam_type === 'simply_supported' ? 3 : 1
      this.loads.forEach(load => { count += load.type === 'udl' ? 3 : 2 })
      return count
    },
    readyCount() {
      let count = this.isPositive(this.form.L) ? 1 : 0
      if (this.form.beam_type === 'simply_supported') {
        if (this.isPosition(this.form.support_a)) count++
        if (this.isPosition(this.form.support_b) && parseFloat(this.form.support_b)>parseFloat(this.form.support_a||-1)) count++
      }
      this.loads.forEach(load => {
        if (this.isPositive(load.value)) count++
        if (load.type === 'udl') {
          if (this.isPosition(load.x1)) count++
          if (this.isPosition(load.x2) && parseFloat(load.x2) > parseFloat(load.x1 || -1)) count++
        } else if (this.isPosition(load.x)) count++
      })
      return count
    },
    canCalculate() { return this.loads.length > 0 && this.readyCount === this.requiredCount },
  },
  methods: {
    setBeamType(type) {
      this.form.beam_type=type
      if (type==='simply_supported' && !this.supportsValid) this.applyPreset('simple')
      this.clearResult()
    },
    setFixedEnd(side) { this.form.fixed_end=side; this.clearResult() },
    applyPreset(type) {
      const L=this.totalLength
      if (!(L>0)) return
      const positions={
        simple:[0,L], left:[L*0.2,L], right:[0,L*0.8], double:[L*0.15,L*0.85],
      }[type]
      this.form.support_a=String(parseFloat(positions[0].toFixed(3)))
      this.form.support_b=String(parseFloat(positions[1].toFixed(3)))
      this.clearResult()
    },
    lengthChanged() {
      const oldLength=parseFloat(this.lastLength)
      const newLength=parseFloat(this.form.L)
      if (Number.isFinite(newLength) && parseFloat(this.form.support_b)===oldLength) this.form.support_b=String(newLength)
      this.lastLength=this.form.L
      this.clearResult()
    },
    addLoad(type) {
      const total = this.totalLength || 1
      const load = { id:this.nextId++, type, value:type==='udl'?'10':type==='point'?'20':'20', x:'', x1:'', x2:'', direction:'clockwise' }
      if (type === 'udl') { load.x1 = '0'; load.x2 = String(total) }
      else load.x = String(total / 2)
      this.loads.push(load)
      this.clearResult()
    },
    removeLoad(index) { this.loads.splice(index,1); this.clearResult() },
    setDirection(load,direction) { load.direction=direction; this.clearResult() },
    clearResult() { this.result=null; this.showSteps=false },
    loadName(type) { return {point:'集中力',udl:'均布荷载',moment:'集中弯矩'}[type] },
    loadHint(type) { return {point:'向下作用',udl:'向下作用，可设置局部范围',moment:'可设置位置和方向'}[type] },
    valueLabel(type) { return {point:'集中力 P',udl:'荷载集度 q',moment:'集中弯矩 M'}[type] },
    valueUnit(type) { return {point:'kN',udl:'kN/m',moment:'kN·m'}[type] },
    isPositive(value) { const n=parseFloat(value); return Number.isFinite(n) && n>0 },
    isPosition(value) { const n=parseFloat(value); return Number.isFinite(n) && n>=0 && n<=this.totalLength },
    percent(value) {
      const n=parseFloat(value)
      return this.totalLength>0 && Number.isFinite(n) ? Math.max(0,Math.min(100,n/this.totalLength*100)) : 0
    },
    pointStyle(load) { return {left:`${this.percent(load.x)}%`} },
    udlStyle(load) {
      const left=this.percent(load.x1), right=this.percent(load.x2)
      return {left:`${left}%`,width:`${Math.max(2,right-left)}%`}
    },
    positive(value,label) {
      const n=parseFloat(value)
      if (!Number.isFinite(n) || n<=0) throw new Error(`请正确填写${label}`)
      return n
    },
    position(value,label) {
      const n=parseFloat(value)
      if (!Number.isFinite(n) || n<0 || n>this.totalLength) throw new Error(`${label}应在 0～${this.totalLength.toFixed(3)} m 之间`)
      return n
    },
    async calculate() {
      try {
        if (!this.loads.length) throw new Error('请至少添加一项荷载')
        this.loading=true
        const payload={
          beam_type:this.form.beam_type,
          load_type:'combined',
          L:this.positive(this.form.L,'梁长 L'),
          loads:[],
        }
        if (this.form.beam_type==='simply_supported') {
          payload.support_a=this.position(this.form.support_a,'A 支座位置 xA')
          payload.support_b=this.position(this.form.support_b,'B 支座位置 xB')
          if (payload.support_b<=payload.support_a) throw new Error('支座位置应满足 xB > xA')
        } else payload.fixed_end=this.form.fixed_end
        this.loads.forEach((load,index) => {
          const item={type:load.type,value:this.positive(load.value,`第 ${index+1} 项荷载值`)}
          if (load.type==='udl') {
            item.x1=this.position(load.x1,`第 ${index+1} 项起点 x₁`)
            item.x2=this.position(load.x2,`第 ${index+1} 项终点 x₂`)
            if (item.x2<=item.x1) throw new Error(`第 ${index+1} 项均布荷载应满足 x₂ > x₁`)
          } else {
            item.x=this.position(load.x,`第 ${index+1} 项作用位置 x`)
            if (load.type==='moment') item.direction=load.direction
          }
          payload.loads.push(item)
        })
        const res=await calcBeamForces(payload)
        this.result=res.data
        setTimeout(()=>uni.pageScrollTo({selector:'.result-panel',duration:320}),80)
      } catch(e) {
        uni.showToast({title:e.data?.detail||e.message||'计算失败',icon:'none',duration:3200})
      } finally { this.loading=false }
    },
  },
}
</script>

<style scoped>
.page{min-height:100vh;background:#EEF1EF;color:#17383A;padding-bottom:180rpx}.hero{background:#123F43;padding:34rpx 30rpx 40rpx;color:#fff}.eyebrow{font-size:18rpx;letter-spacing:5rpx;color:rgba(255,255,255,.55);margin-bottom:12rpx}.hero-title{font-size:46rpx;font-weight:750}.hero-subtitle{font-size:24rpx;color:rgba(255,255,255,.64);margin-top:10rpx}.beam-tabs{display:flex;gap:14rpx;margin-top:28rpx}.beam-tab{flex:1;padding:20rpx 12rpx;border-radius:18rpx;border:2rpx solid rgba(255,255,255,.15);background:#17494D;text-align:center}.beam-tab.active{border-color:#E8734A;background:#1D5B5F}.beam-tab text{display:block;font-size:27rpx;font-weight:700}.beam-tab small{display:block;font-size:19rpx;color:rgba(255,255,255,.55);margin-top:6rpx}.workspace{background:#FAF8F3;margin-top:-18rpx;border-radius:28rpx 28rpx 0 0;padding:34rpx 30rpx 24rpx}.section-head,.load-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24rpx}.section-title{font-size:34rpx;font-weight:750}.section-title.small{font-size:30rpx}.section-note{font-size:21rpx;color:#7C8C8B;margin-top:6rpx}.completion,.load-count{font-size:22rpx;color:#E8734A;font-weight:700;background:#FBE8DF;padding:8rpx 16rpx;border-radius:20rpx}.dimension-row,.field-grid{display:flex;gap:16rpx}.grow,.field-grid .param-block{flex:1;min-width:0}.param-block{margin-bottom:24rpx}.param-label{font-size:24rpx;font-weight:650;color:#385759;margin-bottom:11rpx}.unit-input{height:78rpx;border:2rpx solid #D9DCD7;border-radius:15rpx;background:#F4F3EF;display:flex;align-items:center;padding:0 18rpx;box-sizing:border-box}.unit-input input{flex:1;min-width:0;font-size:28rpx;font-weight:700}.unit-input text{font-size:20rpx;color:#84918F;margin-left:8rpx}.beam-sketch{background:#E8EFED;border-radius:20rpx;padding:28rpx 24rpx;margin:4rpx 0 34rpx;overflow:hidden}.sketch-axis{font-size:18rpx;color:#7A8B89}.beam-line{height:118rpx;position:relative;border-bottom:8rpx solid #17383A;margin:0 30rpx}.support{position:absolute;bottom:-48rpx;font-size:34rpx;color:#E8734A;transform:translateX(-50%)}.support.left{left:0}.support.fixed{bottom:-17rpx;transform:none;font-size:48rpx}.support.movable{z-index:2}.point-mark,.moment-mark{position:absolute;top:20rpx;transform:translateX(-50%);font-size:23rpx;font-weight:800;color:#14575B;white-space:nowrap}.moment-mark{color:#E8734A}.udl-mark{position:absolute;top:54rpx;height:30rpx;border-top:4rpx solid #2C8884;color:#2C8884;font-size:19rpx;text-align:center;box-sizing:border-box;white-space:nowrap;overflow:hidden}.sketch-label{text-align:center;font-size:21rpx;color:#6F7F7D;margin-top:38rpx}.add-row{display:flex;gap:12rpx;margin-bottom:20rpx}.add-load{flex:1;padding:18rpx 8rpx;border:2rpx solid #B9D4D1;border-radius:15rpx;background:#EDF6F4;text-align:center;color:#216267;font-size:22rpx;font-weight:700}.add-icon{color:#E8734A;font-size:26rpx;margin-right:4rpx}.empty-load{text-align:center;padding:36rpx 20rpx;margin-bottom:20rpx;border:2rpx dashed #CDD5D1;border-radius:18rpx;color:#83908E;font-size:21rpx}.empty-title{font-size:26rpx;font-weight:700;color:#536D6D;margin-bottom:8rpx}.load-card{background:#fff;border:2rpx solid #E1E2DD;border-radius:20rpx;padding:22rpx;margin-bottom:18rpx;box-shadow:0 7rpx 20rpx rgba(23,56,58,.05)}.load-card-head{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20rpx}.load-title{display:flex;gap:13rpx;align-items:center}.load-number{width:42rpx;height:42rpx;line-height:42rpx;text-align:center;border-radius:12rpx;background:#DDEDEC;color:#176064;font-size:21rpx;font-weight:800}.load-title strong,.load-title small{display:block}.load-title strong{font-size:26rpx}.load-title small{font-size:19rpx;color:#8A9693;margin-top:4rpx}.delete-load{font-size:21rpx;color:#D46A4A;padding:8rpx}.direction-block{margin-top:-3rpx}.direction-tabs{display:flex;background:#EEF1EF;padding:6rpx;border-radius:13rpx}.direction-tabs view{flex:1;text-align:center;padding:14rpx;border-radius:10rpx;font-size:22rpx;color:#72817F}.direction-tabs view.active{background:#14575B;color:#fff;box-shadow:0 4rpx 10rpx rgba(20,87,91,.18)}.smart-tip{display:flex;align-items:flex-start;gap:12rpx;padding:18rpx 20rpx;border-radius:14rpx;background:#E0EFED;color:#246166;font-size:22rpx;line-height:1.55;margin-top:8rpx}.tip-dot{width:14rpx;height:14rpx;background:#2C8884;border-radius:50%;box-shadow:0 0 0 7rpx rgba(44,136,132,.12);margin-top:9rpx;flex-shrink:0}.result-panel{margin:20rpx;background:#123F43;color:#fff;border-radius:24rpx;padding:30rpx;box-shadow:0 12rpx 32rpx rgba(18,63,67,.16)}.result-head{display:flex;justify-content:space-between;align-items:flex-start}.result-kicker{font-size:20rpx;color:rgba(255,255,255,.5)}.result-title{font-size:30rpx;font-weight:700;margin-top:5rpx}.result-status{padding:8rpx 16rpx;border-radius:18rpx;font-size:22rpx;background:#D9F0E4;color:#26734C}.result-grid{display:grid;grid-template-columns:1fr 1fr;margin-top:26rpx;border-top:1rpx solid rgba(255,255,255,.12);border-left:1rpx solid rgba(255,255,255,.12)}.result-grid view{padding:18rpx;border-right:1rpx solid rgba(255,255,255,.12);border-bottom:1rpx solid rgba(255,255,255,.12)}.result-grid text,.result-grid strong,.result-grid small{display:block}.result-grid text{font-size:19rpx;color:rgba(255,255,255,.48)}.result-grid strong{font-size:25rpx;margin-top:6rpx}.result-grid small{font-size:18rpx;color:#9EC9C5;margin-top:5rpx}.sign-tip{font-size:20rpx;color:#B6D6D3;background:rgba(255,255,255,.07);border-radius:12rpx;padding:15rpx;margin-top:18rpx}.steps-title{display:flex;justify-content:space-between;padding-top:24rpx;font-size:22rpx;color:#A9D5D1}.steps{margin-top:16rpx}.step{display:flex;gap:12rpx;font-size:22rpx;line-height:1.6;padding:12rpx 0;border-top:1rpx solid rgba(255,255,255,.08)}.step>text{color:#E8734A}.action-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;background:rgba(250,248,243,.96);padding:18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));display:flex;align-items:center;gap:22rpx;border-top:1rpx solid #DEE1DD}.readiness{flex:1}.ready-dots{display:flex;gap:5rpx;margin-bottom:8rpx;max-width:280rpx}.ready-dot{height:7rpx;flex:1;background:#D4DAD6;border-radius:4rpx}.ready-dot.on{background:#2C8884}.readiness text{font-size:20rpx;color:#6F7F7D}.calc-btn{width:270rpx;height:86rpx;line-height:86rpx;margin:0;border:none;border-radius:17rpx;background:#E8734A;color:#fff;font-size:29rpx;font-weight:750;box-shadow:0 8rpx 20rpx rgba(232,115,74,.24)}.calc-btn::after{border:none}
.section-title.tiny{font-size:26rpx}.support-panel{background:#F1F3EF;border:2rpx solid #DCE1DC;border-radius:18rpx;padding:20rpx;margin-bottom:24rpx}.support-panel-head{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:18rpx}.layout-name{font-size:20rpx;font-weight:700;color:#246166;background:#DCEDEA;padding:8rpx 14rpx;border-radius:18rpx}.preset-row{display:flex;gap:9rpx}.preset-row view{flex:1;text-align:center;padding:13rpx 5rpx;border-radius:11rpx;background:#fff;border:2rpx solid #D8DDDA;color:#55706F;font-size:20rpx}.beam-line{height:128rpx}.support{position:absolute;text-align:center;white-space:nowrap}.support.fixed{transform:none}.support small{display:block;font-size:16rpx;color:#657A78;margin-top:-2rpx}.support.roller i{display:block;font-size:15rpx;line-height:8rpx;font-style:normal}.support.roller small{margin-top:5rpx}.sketch-label{margin-top:48rpx}
</style>
