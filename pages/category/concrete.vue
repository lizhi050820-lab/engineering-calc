<template>
  <view class="container">
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

    <view style="height: 40rpx;"></view>
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
.container { padding: 20rpx 0 40rpx; }

.tool-card {
  display: flex;
  align-items: center;
  background: #fff;
  margin: 0 20rpx 16rpx;
  padding: 32rpx;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}
.tool-card:active { transform: scale(0.98); background: #FAFBFC; }

.tool-icon-wrap {
  width: 96rpx; height: 96rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
  margin-right: 24rpx; flex-shrink: 0;
}
.bg-green  { background: linear-gradient(135deg, #E0F5E8, #C8EAD5); }
.bg-blue   { background: linear-gradient(135deg, #E3F0FF, #D0E5FF); }
.bg-orange { background: linear-gradient(135deg, #FFF0E0, #FFE0C0); }
.tool-icon { font-size: 44rpx; }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 600; color: #222; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #999; }

.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }
</style>
