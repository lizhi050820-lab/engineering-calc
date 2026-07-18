<template>
  <view class="container">
    <view class="category-intro"><view class="intro-kicker">CONCRETE</view><view class="intro-title">混凝土结构设计</view><view class="intro-desc">从截面设计到配筋校核，按规范逐步计算</view></view>
    <view class="tool-list">
      <!-- 截面统一设计 -->
      <view class="tool-card" @click="goTo('/pages/calculator/section-design')">
        <view class="tool-icon-wrap bg-green">
          <text class="tool-icon">RC</text>
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
          <text class="tool-icon">MU</text>
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
          <text class="tool-icon">AS</text>
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
.container { padding: 0 0 40rpx; }.category-intro{background:#123F43;color:#fff;padding:42rpx 34rpx 38rpx;border-radius:0 0 30rpx 30rpx;margin-bottom:24rpx}.intro-kicker{font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.48)}.intro-title{font-size:42rpx;font-weight:750;margin-top:10rpx}.intro-desc{font-size:23rpx;color:rgba(255,255,255,.64);margin-top:10rpx}

.tool-card {
  display: flex;
  align-items: center;
  background: #FAF8F3;
  margin: 0 20rpx 16rpx;
  padding: 32rpx;
  border-radius: 22rpx;
  box-shadow: 0 8rpx 24rpx rgba(18,63,67,.06);
}
.tool-card:active { transform: scale(0.98); background: #F2F1EC; }

.tool-icon-wrap {
  width: 96rpx; height: 96rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
  margin-right: 24rpx; flex-shrink: 0;
}
.bg-green,.bg-blue,.bg-orange { background: #E0EFED; }
.tool-icon { font-size: 24rpx;font-weight:800;color:#14575B;letter-spacing:1rpx }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 650; color: #17383A; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #7C8987; }

.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }
</style>
