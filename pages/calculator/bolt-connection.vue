<template>
  <view class="page">
    <view class="hero">
      <view class="eyebrow">STEEL CONNECTION</view>
      <view class="hero-title">螺栓连接承载力</view>
      <view class="hero-subtitle">先选择连接方式，再完成关键参数</view>

      <scroll-view class="type-scroll" scroll-x :show-scrollbar="false">
        <view class="type-row">
          <view class="type-card" :class="{ active: form.bolt_type === 'ordinary' }" @click="setType('ordinary')">
            <image class="type-image" src="/static/bolt-ui/ordinary-bolt.png" mode="aspectFill" />
            <view class="type-name">普通螺栓</view>
            <view class="type-desc">抗剪 · 承压</view>
          </view>
          <view class="type-card" :class="{ active: form.bolt_type === 'high_strength' }" @click="setType('high_strength')">
            <image class="type-image" src="/static/bolt-ui/high-strength-bolt.png" mode="aspectFill" />
            <view class="type-name">高强螺栓</view>
            <view class="type-desc">摩擦型 · 抗滑移</view>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="workspace">
      <view class="section-head">
        <view><view class="section-title">螺栓参数</view><view class="section-note">常用规格可直接点选</view></view>
        <view class="completion">{{ readyCount }}/{{ requiredCount }}</view>
      </view>

      <view class="param-block">
        <view class="param-label">直径 d</view>
        <view class="chips">
          <view v-for="d in diameters" :key="d" class="chip" :class="{selected: String(form.diameter)===String(d)}" @click="selectDiameter(d)">M{{ d }}</view>
        </view>
      </view>

      <view class="param-block split">
        <view class="split-item">
          <view class="param-label">螺栓数量 n</view>
          <view class="stepper">
            <view class="step-btn" @click="changeCount(-1)">−</view>
            <input class="step-value" type="number" v-model="form.bolt_count" @input="clearResult" />
            <view class="step-btn" @click="changeCount(1)">＋</view>
          </view>
        </view>
        <view class="split-item">
          <view class="param-label">性能等级</view>
          <picker :range="grades" :value="gradeIndex" @change="onGradeChange">
            <view class="select-box"><text>{{ grades[gradeIndex] }} 级</text><text class="select-mark">⌄</text></view>
          </picker>
        </view>
      </view>

      <view v-if="form.bolt_type === 'ordinary'" class="smart-tip">
        <view class="tip-dot"></view>
        <view>已按 M{{ form.diameter }} 普通螺栓准备抗剪与承压验算</view>
      </view>
      <view v-else class="smart-tip">
        <view class="tip-dot"></view>
        <view>已匹配 {{ grades[gradeIndex] }} 级 M{{ form.diameter }} 预拉力查表</view>
      </view>

      <view class="divider"></view>
      <view class="section-head simple"><view class="section-title">连接参数</view><view class="section-note">用于确定控制承载力</view></view>

      <template v-if="form.bolt_type === 'ordinary'">
        <view class="param-block">
          <view class="param-label">连接板钢材</view>
          <view class="chips compact"><view v-for="(g,i) in steelGrades" :key="g" class="chip" :class="{selected:steelIndex===i}" @click="steelIndex=i;clearResult()">{{ g }}</view></view>
        </view>
        <view class="param-block split">
          <view class="split-item"><view class="param-label">受剪面数 nᵥ</view><view class="chips compact"><view v-for="n in [1,2]" :key="n" class="chip" :class="{selected:String(form.shear_planes)===String(n)}" @click="form.shear_planes=String(n);clearResult()">{{ n===1?'单剪':'双剪' }}</view></view></view>
          <view class="split-item"><view class="param-label">承压总厚度 Σt</view><view class="unit-input"><input type="digit" v-model="form.connected_thickness" @input="clearResult"/><text>mm</text></view></view>
        </view>
      </template>
      <template v-else>
        <view class="param-block"><view class="param-label">孔型</view><view class="chips compact"><view v-for="(name,i) in holeNames" :key="name" class="chip" :class="{selected:holeIndex===i}" @click="holeIndex=i;clearResult()">{{ name }}</view></view></view>
        <view class="param-block split">
          <view class="split-item"><view class="param-label">抗滑移系数 μ（按表或试验）</view><view class="unit-input"><input type="digit" v-model="form.slip_coefficient" @input="clearResult"/></view></view>
          <view class="split-item"><view class="param-label">摩擦面数 n𝒻</view><view class="chips compact"><view v-for="n in [1,2]" :key="n" class="chip" :class="{selected:String(form.friction_surfaces)===String(n)}" @click="form.friction_surfaces=String(n);clearResult()">{{ n }}</view></view></view>
        </view>
      </template>

      <view class="param-block load-block">
        <view><view class="param-label">设计剪力 V</view><view class="optional">可选 · 填写后自动判断是否满足</view></view>
        <view class="unit-input load"><input type="digit" v-model="form.load" placeholder="0" @input="clearResult"/><text>kN</text></view>
      </view>
    </view>

    <view v-if="result" class="result-panel">
      <view class="result-head"><view><view class="result-kicker">计算完成</view><view class="result-title">{{ result.control }}控制</view></view><view v-if="result.passed!==null" class="result-status" :class="result.passed?'pass':'fail'">{{ result.passed?'满足':'不满足' }}</view></view>
      <view class="capacity"><text class="capacity-number">{{ result.total_capacity }}</text><text class="capacity-unit">kN</text></view>
      <view class="capacity-label">连接承载力 Nᵤ</view>
      <view v-if="result.utilization!==null" class="meter"><view class="meter-fill" :class="{danger:!result.passed}" :style="{width: Math.min(result.utilization*100,100)+'%'}"></view></view>
      <view class="result-grid"><view><text>单栓承载力</text><strong>{{ result.per_bolt_capacity }} kN</strong></view><view v-if="result.utilization!==null"><text>利用率 η</text><strong>{{ result.utilization }}</strong></view></view>
      <view class="steps-title" @click="showSteps=!showSteps"><text>查看计算步骤</text><text>{{ showSteps?'收起':'展开' }}</text></view>
      <view v-if="showSteps" class="steps"><view v-for="(step,i) in result.steps" :key="i" class="step"><text>{{ i+1 }}</text><view>{{ step }}</view></view></view>
    </view>

    <view class="action-bar">
      <view class="readiness"><view class="ready-dots"><view v-for="i in requiredCount" :key="i" class="ready-dot" :class="{on:i<=readyCount}"></view></view><text>{{ readyCount===requiredCount?'准备就绪':'还需完善参数' }}</text></view>
      <button class="calc-btn" :loading="loading" @click="calculate">{{ result?'重新计算':'开始计算' }}</button>
    </view>
  </view>
</template>

<script>
import { calcBoltConnection } from '../../utils/api.js'
export default {
  data() { return {
    form:{bolt_type:'ordinary',diameter:'20',bolt_count:'4',shear_planes:'2',connected_thickness:'10',slip_coefficient:'0.45',friction_surfaces:'1',load:''},
    ordinaryGrades:['4.6','4.8','5.6','8.8'], highGrades:['8.8','10.9'], gradeIndex:0,
    steelGrades:['Q235','Q355','Q390','Q420'], steelIndex:0,
    holeNames:['标准孔','大圆孔','槽孔'], holeTypes:['standard','oversize','slotted'], holeIndex:0,
    loading:false,result:null,showSteps:false
  } },
  computed:{
    grades(){ return this.form.bolt_type==='ordinary'?this.ordinaryGrades:this.highGrades },
    diameters(){ return this.form.bolt_type==='ordinary'?[12,16,20,22,24]:[16,20,22,24,27,30] },
    requiredCount(){ return 7 },
    readyCount(){ const base=[this.form.diameter,this.form.bolt_count,this.grades[this.gradeIndex],this.form.bolt_type];const extra=this.form.bolt_type==='ordinary'?[this.steelGrades[this.steelIndex],this.form.shear_planes,this.form.connected_thickness]:[this.holeTypes[this.holeIndex],this.form.slip_coefficient,this.form.friction_surfaces];return base.concat(extra).filter(v=>v!==''&&v!==null&&v!==undefined).length }
  },
  methods:{
    clearResult(){ this.result=null;this.showSteps=false },
    setType(type){ this.form.bolt_type=type;this.gradeIndex=0;if(type==='high_strength'&&!this.diameters.includes(parseInt(this.form.diameter)))this.form.diameter='20';this.clearResult() },
    selectDiameter(d){ this.form.diameter=String(d);this.clearResult() },
    changeCount(delta){ const value=Math.max(1,(parseInt(this.form.bolt_count)||1)+delta);this.form.bolt_count=String(value);this.clearResult() },
    onGradeChange(e){ this.gradeIndex=parseInt(e.detail.value);this.clearResult() },
    positive(value,name){ const n=parseFloat(value);if(!Number.isFinite(n)||n<=0)throw new Error('请正确填写'+name);return n },
    async calculate(){
      try{
        this.loading=true;this.result=null
        const p={bolt_type:this.form.bolt_type,diameter:this.positive(this.form.diameter,'螺栓直径'),bolt_count:Math.round(this.positive(this.form.bolt_count,'螺栓数量')),bolt_grade:this.grades[this.gradeIndex],steel_grade:this.steelGrades[this.steelIndex],shear_planes:Math.round(this.positive(this.form.shear_planes,'受剪面数')),connected_thickness:this.positive(this.form.connected_thickness,'承压总厚度'),slip_coefficient:this.positive(this.form.slip_coefficient,'抗滑移系数'),friction_surfaces:Math.round(this.positive(this.form.friction_surfaces,'摩擦面数')),hole_type:this.holeTypes[this.holeIndex]}
        if(this.form.load!=='')p.load=this.positive(this.form.load,'设计剪力')
        const res=await calcBoltConnection(p);this.result=res.data
        setTimeout(()=>uni.pageScrollTo({selector:'.result-panel',duration:320}),80)
      }catch(e){uni.showToast({title:e.data?.detail||e.message||'计算失败',icon:'none',duration:3000})}finally{this.loading=false}
    }
  }
}
</script>

<style scoped>
.page{min-height:100vh;background:#EEF1EF;color:#17383A;padding-bottom:180rpx}.hero{background:#123F43;padding:34rpx 30rpx 44rpx;color:#fff}.eyebrow{font-size:18rpx;letter-spacing:5rpx;color:rgba(255,255,255,.55);margin-bottom:12rpx}.hero-title{font-size:46rpx;font-weight:750;letter-spacing:-1rpx}.hero-subtitle{font-size:24rpx;color:rgba(255,255,255,.64);margin-top:10rpx}.type-scroll{margin-top:30rpx;width:100%;white-space:nowrap}.type-row{display:flex;gap:18rpx}.type-card{position:relative;width:282rpx;height:210rpx;flex-shrink:0;overflow:hidden;border:2rpx solid rgba(255,255,255,.16);border-radius:22rpx;background:#17494D;box-sizing:border-box;transition:.2s}.type-card.active{border-color:#E8734A;box-shadow:0 0 0 4rpx rgba(232,115,74,.14)}.type-image{position:absolute;right:-8rpx;top:-34rpx;width:180rpx;height:180rpx;opacity:.58}.type-card.active .type-image{opacity:.95}.type-name{position:absolute;left:22rpx;bottom:48rpx;font-size:30rpx;font-weight:700}.type-desc{position:absolute;left:22rpx;bottom:18rpx;font-size:20rpx;color:rgba(255,255,255,.55)}.workspace{background:#FAF8F3;margin-top:-18rpx;border-radius:28rpx 28rpx 0 0;padding:34rpx 30rpx 24rpx}.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:26rpx}.section-head.simple{align-items:flex-end}.section-title{font-size:34rpx;font-weight:750;color:#17383A}.section-note{font-size:21rpx;color:#7C8C8B;margin-top:6rpx}.completion{font-size:22rpx;color:#E8734A;font-weight:700;background:#FBE8DF;padding:8rpx 16rpx;border-radius:20rpx}.param-block{margin-bottom:28rpx}.param-label{font-size:25rpx;font-weight:650;color:#385759;margin-bottom:14rpx}.chips{display:flex;flex-wrap:wrap;gap:12rpx}.chip{min-width:92rpx;padding:17rpx 18rpx;text-align:center;background:#F0EFEB;border:2rpx solid #DDDCD6;border-radius:14rpx;font-size:27rpx;color:#44595A;box-sizing:border-box;transition:.15s}.chip.selected{background:#14575B;border-color:#14575B;color:#fff;box-shadow:0 6rpx 16rpx rgba(20,87,91,.16)}.chips.compact .chip{min-width:104rpx;padding:15rpx 16rpx;font-size:24rpx}.split{display:flex;gap:20rpx}.split-item{flex:1;min-width:0}.stepper,.select-box,.unit-input{height:78rpx;border:2rpx solid #D9DCD7;border-radius:15rpx;background:#F4F3EF;display:flex;align-items:center;box-sizing:border-box}.step-btn{width:70rpx;text-align:center;font-size:34rpx;color:#14575B}.step-value{flex:1;text-align:center;font-size:30rpx;font-weight:700;min-width:0}.select-box{padding:0 20rpx;justify-content:space-between;font-size:27rpx;font-weight:650}.select-mark{color:#84918F}.unit-input{padding:0 18rpx}.unit-input input{flex:1;min-width:0;font-size:29rpx;font-weight:700}.unit-input text{font-size:22rpx;color:#84918F}.smart-tip{display:flex;align-items:center;gap:12rpx;padding:18rpx 20rpx;border-radius:14rpx;background:#E0EFED;color:#246166;font-size:22rpx;margin:-4rpx 0 34rpx}.tip-dot{width:14rpx;height:14rpx;background:#2C8884;border-radius:50%;box-shadow:0 0 0 7rpx rgba(44,136,132,.12)}.divider{height:1rpx;background:#DADFDB;margin:0 0 30rpx}.load-block{display:flex;justify-content:space-between;align-items:center;border-top:1rpx solid #E1E3DF;padding-top:26rpx}.optional{font-size:20rpx;color:#8A9694}.unit-input.load{width:240rpx}.result-panel{margin:20rpx;background:#123F43;color:#fff;border-radius:24rpx;padding:30rpx;box-shadow:0 12rpx 32rpx rgba(18,63,67,.16)}.result-head{display:flex;justify-content:space-between;align-items:flex-start}.result-kicker{font-size:20rpx;color:rgba(255,255,255,.5)}.result-title{font-size:30rpx;font-weight:700;margin-top:5rpx}.result-status{padding:8rpx 16rpx;border-radius:18rpx;font-size:22rpx}.result-status.pass{background:#D9F0E4;color:#26734C}.result-status.fail{background:#FCE2DC;color:#A23E31}.capacity{margin-top:28rpx}.capacity-number{font-size:74rpx;font-weight:800;letter-spacing:-2rpx}.capacity-unit{font-size:26rpx;color:rgba(255,255,255,.55);margin-left:10rpx}.capacity-label{font-size:22rpx;color:rgba(255,255,255,.5)}.meter{height:10rpx;background:rgba(255,255,255,.12);border-radius:6rpx;margin:24rpx 0;overflow:hidden}.meter-fill{height:100%;background:#4CB58A;border-radius:6rpx}.meter-fill.danger{background:#E8734A}.result-grid{display:flex;border-top:1rpx solid rgba(255,255,255,.12);border-bottom:1rpx solid rgba(255,255,255,.12)}.result-grid view{flex:1;padding:20rpx 0}.result-grid text,.result-grid strong{display:block}.result-grid text{font-size:20rpx;color:rgba(255,255,255,.48)}.result-grid strong{font-size:26rpx;margin-top:6rpx}.steps-title{display:flex;justify-content:space-between;padding-top:22rpx;font-size:22rpx;color:#A9D5D1}.steps{margin-top:16rpx}.step{display:flex;gap:12rpx;font-size:22rpx;line-height:1.6;padding:12rpx 0;border-top:1rpx solid rgba(255,255,255,.08)}.step>text{color:#E8734A}.action-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;background:rgba(250,248,243,.96);padding:18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));display:flex;align-items:center;gap:22rpx;border-top:1rpx solid #DEE1DD}.readiness{flex:1}.ready-dots{display:flex;gap:7rpx;margin-bottom:8rpx}.ready-dot{height:7rpx;flex:1;background:#D4DAD6;border-radius:4rpx}.ready-dot.on{background:#2C8884}.readiness text{font-size:20rpx;color:#6F7F7D}.calc-btn{width:270rpx;height:86rpx;line-height:86rpx;margin:0;border:none;border-radius:17rpx;background:#E8734A;color:#fff;font-size:29rpx;font-weight:750;box-shadow:0 8rpx 20rpx rgba(232,115,74,.24)}.calc-btn::after{border:none}
</style>
