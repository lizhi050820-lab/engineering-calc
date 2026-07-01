<template>
  <view class="container">
    <!-- 顶部 Banner -->
    <view class="banner">
      <view class="banner-icon">🏗️</view>
      <view class="banner-title">土木工程计算工具箱</view>
      <view class="banner-desc">正截面承载力 · 配筋计算 · 更多工具开发中</view>
    </view>

    <!-- 工具列表 -->
    <view class="section-title">计算工具</view>

    <view class="tool-list">
      <!-- 截面统一设计 -->
      <view class="tool-card" @click="goTo('/pages/calculator/section-design')">
        <view class="tool-icon-wrap bg-green">
          <text class="tool-icon">🏗️</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">截面设计</view>
          <view class="tool-desc">正截面+斜截面，一次输入完成全部计算</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>

      <!-- 正截面承载力 -->
      <view class="tool-card" @click="goTo('/pages/calculator/bearing')">
        <view class="tool-icon-wrap bg-blue">
          <text class="tool-icon">📐</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">正截面承载力计算</view>
          <view class="tool-desc">单筋/双筋矩形截面，校核与设计</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>

      <!-- 配筋计算 -->
      <view class="tool-card" @click="goTo('/pages/calculator/rebar')">
        <view class="tool-icon-wrap bg-orange">
          <text class="tool-icon">🔩</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">配筋计算</view>
          <view class="tool-desc">给定弯矩求配筋，自动推荐选筋方案</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>
    </view>

    <!-- 规范参考 -->
    <view class="section-title">参考资料</view>
    <view class="ref-card card">
      <view class="ref-item">
        <text class="ref-bullet">•</text>
        <text class="ref-text">《混凝土结构设计规范》GB/T 50010-2010（2024年版）</text>
      </view>
      <view class="ref-item">
        <text class="ref-bullet">•</text>
        <text class="ref-text">材料参数取自现行国家标准</text>
      </view>
      <view class="ref-item">
        <text class="ref-bullet">•</text>
        <text class="ref-text">计算结果仅供参考，实际工程请以规范为准</text>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version">v0.1.0 · Powered by Python FastAPI</view>
  </view>
</template>

<script>
export default {
  data() {
    return {}
  },
  methods: {
    goTo(url) {
      uni.navigateTo({ url })
    },
  },
}
</script>

<style scoped>
.container {
  padding-bottom: 40rpx;
}

/* Banner */
.banner {
  background: linear-gradient(135deg, #1A5CB5, #2C6FCE, #5B9CF5);
  padding: 60rpx 40rpx 50rpx;
  text-align: center;
  color: #fff;
}

.banner-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.banner-title {
  font-size: 40rpx;
  font-weight: 700;
  margin-bottom: 12rpx;
}

.banner-desc {
  font-size: 26rpx;
  opacity: 0.85;
}

/* 分区标题 */
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  padding: 32rpx 40rpx 16rpx;
}

/* 工具卡片 */
.tool-card {
  display: flex;
  align-items: center;
  background: #fff;
  margin: 0 20rpx 16rpx;
  padding: 32rpx;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  transition: transform 0.2s;
}

.tool-card:active {
  transform: scale(0.98);
  background: #FAFBFC;
}

.tool-icon-wrap {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;
}

.bg-blue {
  background: linear-gradient(135deg, #E3F0FF, #D0E5FF);
}

.bg-green {
  background: linear-gradient(135deg, #E0F5E8, #C8EAD5);
}

.bg-orange {
  background: linear-gradient(135deg, #FFF0E0, #FFE0C0);
}

.tool-icon {
  font-size: 44rpx;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #222;
  margin-bottom: 8rpx;
}

.tool-desc {
  font-size: 24rpx;
  color: #999;
}

.tool-arrow {
  font-size: 40rpx;
  color: #ccc;
  margin-left: 12rpx;
}

/* 参考卡片 */
.ref-card {
  margin: 0 20rpx;
}

.ref-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 14rpx;
}

.ref-item:last-child {
  margin-bottom: 0;
}

.ref-bullet {
  color: #2C6FCE;
  font-weight: 700;
  margin-right: 12rpx;
  line-height: 1.6;
}

.ref-text {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  flex: 1;
}

/* 版本号 */
.version {
  text-align: center;
  font-size: 22rpx;
  color: #bbb;
  margin-top: 40rpx;
}
</style>
