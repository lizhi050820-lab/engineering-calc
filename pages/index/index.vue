<template>
  <view class="container">
    <!-- 顶部 Banner -->
    <view class="banner">
      <view class="banner-icon">🏗️</view>
      <view class="banner-title">土木工程计算工具箱</view>
      <view class="banner-desc">混凝土结构 · 截面性质 · 更多模块开发中</view>
    </view>

    <!-- 分类入口 -->
    <view class="section-label">选择计算模块</view>

    <!-- 混凝土结构设计 -->
    <view class="cat-card" @click="goTo('/pages/category/concrete')">
      <view class="cat-accent accent-concrete"></view>
      <view class="cat-body">
        <view class="cat-icon-wrap bg-concrete">
          <text class="cat-icon">🏗️</text>
        </view>
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
        <view class="cat-icon-wrap bg-section">
          <text class="cat-icon">📏</text>
        </view>
        <view class="cat-info">
          <view class="cat-name">截面几何性质</view>
          <view class="cat-desc">标准截面 · 组合截面平行移轴</view>
          <view class="cat-count">2 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <!-- 即将推出 -->
    <view class="section-label">即将推出</view>
    <view class="cat-card" @click="goTo('/pages/category/soil')">
      <view class="cat-accent accent-soil"></view>
      <view class="cat-body">
        <view class="cat-icon-wrap bg-soil">
          <text class="cat-icon">⛰️</text>
        </view>
        <view class="cat-info">
          <view class="cat-name">土力学计算</view>
          <view class="cat-desc">三相比例指标 · 地基承载力 · 沉降计算</view>
          <view class="cat-count">1 个工具</view>
        </view>
        <view class="cat-arrow">›</view>
      </view>
    </view>

    <view class="cat-card cat-card-soon">
      <view class="cat-accent accent-soon"></view>
      <view class="cat-body">
        <view class="cat-icon-wrap bg-soon">
          <text class="tool-icon">🔩</text>
        </view>
        <view class="cat-info">
          <view class="cat-name">钢结构设计</view>
          <view class="cat-desc">螺栓连接 · 焊缝计算 · 轴压构件</view>
          <view class="cat-count">开发中</view>
        </view>
        <view class="cat-arrow cat-arrow-soon">›</view>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version">v0.2.0 · Powered by Python FastAPI</view>
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
.container { padding-bottom: 40rpx; }

/* ========== Banner ========== */
.banner {
  background: linear-gradient(135deg, #1A5CB5, #2C6FCE, #5B9CF5);
  padding: 60rpx 40rpx 50rpx;
  text-align: center;
  color: #fff;
}
.banner-icon { font-size: 80rpx; margin-bottom: 16rpx; }
.banner-title { font-size: 40rpx; font-weight: 700; margin-bottom: 12rpx; }
.banner-desc { font-size: 26rpx; opacity: 0.85; }

/* ========== 分区标签 ========== */
.section-label {
  font-size: 26rpx;
  color: #999;
  padding: 32rpx 40rpx 16rpx;
  letter-spacing: 2rpx;
}

/* ========== 分类卡片 ========== */
.cat-card {
  margin: 0 20rpx 16rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.06);
  overflow: hidden;
}
.cat-card:active { transform: scale(0.985); }

.cat-card-soon { opacity: 0.55; }

.cat-accent {
  height: 6rpx;
}
.accent-concrete { background: linear-gradient(90deg, #2C6FCE, #5B9CF5); }
.accent-section  { background: linear-gradient(90deg, #7C4DFF, #B388FF); }
.accent-soil     { background: linear-gradient(90deg, #795548, #A1887F); }
.accent-soon     { background: linear-gradient(90deg, #CCC, #DDD); }

.cat-body {
  display: flex;
  align-items: center;
  padding: 28rpx 28rpx 28rpx 28rpx;
}

.cat-icon-wrap {
  width: 100rpx; height: 100rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
  margin-right: 24rpx; flex-shrink: 0;
}
.bg-concrete { background: linear-gradient(135deg, #E3F0FF, #D0E5FF); }
.bg-section  { background: linear-gradient(135deg, #EDE7F6, #D1C4E9); }
.bg-soil     { background: linear-gradient(135deg, #EFEBE9, #D7CCC8); }
.bg-soon     { background: #F5F5F5; }

.cat-icon { font-size: 48rpx; }

.cat-info { flex: 1; }
.cat-name { font-size: 34rpx; font-weight: 700; color: #222; margin-bottom: 8rpx; }
.cat-desc { font-size: 24rpx; color: #888; margin-bottom: 6rpx; }
.cat-count { font-size: 22rpx; color: #2C6FCE; }
.cat-card-soon .cat-count { color: #bbb; }
.cat-card-soon .cat-name { color: #888; }

.cat-arrow { font-size: 44rpx; color: #ccc; margin-left: 8rpx; }
.cat-arrow-soon { color: #ddd; }

/* ========== 版本号 ========== */
.version {
  text-align: center; font-size: 22rpx; color: #bbb; margin-top: 40rpx;
}
</style>
