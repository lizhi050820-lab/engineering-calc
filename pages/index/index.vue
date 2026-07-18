<template>
  <view class="container">
    <!-- 顶部 Banner -->
    <view class="banner">
      <view class="banner-kicker">ENGINEERING CALCULATOR</view>
      <view class="banner-title">土木工程计算工具箱</view>
      <view class="banner-desc">把规范公式变成清晰、可靠的计算过程</view>
      <view class="banner-meta"><text>9 个工具</text><text>5 个专业模块</text><text>逐步推导</text></view>
    </view>

    <!-- 分类入口 -->
    <view class="section-label">选择计算模块</view>

    <!-- 混凝土结构设计 -->
    <view class="cat-card" @click="goTo('/pages/category/concrete')">
      <view class="cat-accent accent-concrete"></view>
      <view class="cat-body">
        <view class="cat-index">01</view>
        <view class="cat-info">
          <view class="cat-name">混凝土结构设计</view>
          <view class="cat-desc">截面设计 · 正截面承载力 · 配筋计算</view>
          <view class="cat-count">3 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <!-- 截面几何性质 -->
    <view class="cat-card" @click="goTo('/pages/category/section')">
      <view class="cat-accent accent-section"></view>
      <view class="cat-body">
        <view class="cat-index">02</view>
        <view class="cat-info">
          <view class="cat-name">截面几何性质</view>
          <view class="cat-desc">标准截面 · 组合截面平行移轴</view>
          <view class="cat-count">2 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <view class="cat-card" @click="goTo('/pages/category/soil')">
      <view class="cat-accent accent-soil"></view>
      <view class="cat-body">
        <view class="cat-index">03</view>
        <view class="cat-info">
          <view class="cat-name">土力学计算</view>
          <view class="cat-desc">三相比例指标 · 地基承载力 · 沉降计算</view>
          <view class="cat-count">2 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <view class="cat-card" @click="goTo('/pages/category/steel')">
      <view class="cat-accent accent-steel"></view>
      <view class="cat-body">
        <view class="cat-index">04</view>
        <view class="cat-info">
          <view class="cat-name">钢结构设计</view>
          <view class="cat-desc">螺栓连接 · 焊缝计算 · 轴压构件</view>
          <view class="cat-count">1 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <view class="cat-card" @click="goTo('/pages/category/mechanics')">
      <view class="cat-accent accent-mechanics"></view>
      <view class="cat-body">
        <view class="cat-index">05</view>
        <view class="cat-info">
          <view class="cat-name">结构力学速算</view>
          <view class="cat-desc">简支梁 · 悬臂梁 · 外伸梁内力与反力</view>
          <view class="cat-count">1 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version">v0.3.0 · 浏览器本地计算</view>
  </view>
</template>

<script>
export default {
  methods: {
    goTo(url) { uni.navigateTo({ url }) },
  },
}
</script>

<style scoped>
.container { padding-bottom: 40rpx; background:#EEF1EF; min-height:100vh; }

/* ========== Banner ========== */
.banner {
  background: #123F43;
  padding: 62rpx 38rpx 50rpx;
  text-align: left;
  color: #fff;
  border-radius: 0 0 34rpx 34rpx;
}
.banner-kicker{font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.48);margin-bottom:16rpx}
.banner-title { font-size: 44rpx; font-weight: 750; margin-bottom: 12rpx; }
.banner-desc { font-size: 25rpx; color:rgba(255,255,255,.68); }
.banner-meta{display:flex;gap:12rpx;margin-top:30rpx}.banner-meta text{font-size:20rpx;padding:9rpx 14rpx;border:1rpx solid rgba(255,255,255,.18);border-radius:18rpx;color:rgba(255,255,255,.76)}

/* ========== 分区标签 ========== */
.section-label {
  font-size: 26rpx;
  color: #6F7F7D;
  padding: 32rpx 40rpx 16rpx;
  letter-spacing: 2rpx;
}

/* ========== 分类卡片 ========== */
.cat-card {
  margin: 0 20rpx 16rpx;
  background: #FAF8F3;
  border-radius: 22rpx;
  box-shadow: 0 8rpx 24rpx rgba(18,63,67,.06);
  overflow: hidden;
}
.cat-card:active { transform: scale(0.985); background:#F4F2ED; }

.cat-card-soon { opacity: 0.55; }

.cat-accent {
  height: 6rpx;
}
.accent-concrete { background: #2C8884; }
.accent-section  { background: #B6924A; }
.accent-soil     { background: #8A6F5A; }
.accent-soon     { background: #AAB4B1; }
.accent-steel    { background: #E8734A; }
.accent-mechanics{ background: #2C8884; }

.cat-body {
  display: flex;
  align-items: center;
  padding: 28rpx 28rpx 28rpx 28rpx;
}

.cat-index{width:72rpx;height:72rpx;line-height:72rpx;text-align:center;margin-right:22rpx;border-radius:18rpx;background:#E0EFED;color:#14575B;font-size:24rpx;font-weight:750;flex-shrink:0}
.bg-concrete { background: linear-gradient(135deg, #E3F0FF, #D0E5FF); }
.bg-section  { background: linear-gradient(135deg, #EDE7F6, #D1C4E9); }
.bg-soil     { background: linear-gradient(135deg, #EFEBE9, #D7CCC8); }
.bg-soon     { background: #F5F5F5; }
.bg-steel    { background: linear-gradient(135deg, #ECEFF1, #CFD8DC); }

.cat-icon { font-size: 48rpx; }

.cat-info { flex: 1; }
.cat-name { font-size: 33rpx; font-weight: 700; color: #17383A; margin-bottom: 8rpx; }
.cat-desc { font-size: 24rpx; color: #778582; margin-bottom: 6rpx; }
.cat-count { font-size: 22rpx; color: #E8734A; }
.cat-card-soon .cat-count { color: #bbb; }
.cat-card-soon .cat-name { color: #888; }

.cat-arrow { font-size: 44rpx; color: #ccc; margin-left: 8rpx; }
.cat-arrow-soon { color: #ddd; }

/* ========== 版本号 ========== */
.version {
  text-align: center; font-size: 22rpx; color: #bbb; margin-top: 40rpx;
}
</style>
