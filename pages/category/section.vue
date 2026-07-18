<template>
  <view class="container">
    <view class="category-intro"><view class="intro-kicker">SECTION</view><view class="intro-title">截面几何性质</view><view class="intro-desc">标准截面与组合截面的几何特性分析</view></view>
    <view class="tool-list">
      <!-- 标准截面 -->
      <view class="tool-card" @click="goTo('/pages/calculator/section-props')">
        <view class="tool-icon-wrap bg-purple">
          <text class="tool-icon">IX</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">标准截面计算</view>
          <view class="tool-desc">矩形、T形、圆形、环形、工字钢，直接公式求截面特性</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>

      <!-- 组合截面（平行移轴） -->
      <view class="tool-card" @click="goTo('/pages/calculator/composite-section')">
        <view class="tool-icon-wrap bg-teal">
          <text class="tool-icon">ΣI</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">组合截面（平行移轴）</view>
          <view class="tool-desc">任意矩形组合截面，平行移轴公式逐步计算惯性矩</view>
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
.bg-purple,.bg-teal { background: #E0EFED; }
.tool-icon { font-size: 24rpx;font-weight:800;color:#14575B }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 650; color: #17383A; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #7C8987; }

.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }
</style>
