<template>
  <view class="container">
    <view class="category-intro"><view class="intro-kicker">GEOTECHNICS</view><view class="intro-title">土力学计算</view><view class="intro-desc">土体指标推导与渗流计算，过程清晰可追溯</view></view>
    <view class="tool-list">
      <!-- 三相比例指标 -->
      <view class="tool-card" @click="goTo('/pages/calculator/soil-three-phase')">
        <view class="tool-icon-wrap bg-brown">
          <text class="tool-icon">3P</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">三相比例指标计算</view>
          <view class="tool-desc">重度、含水量、孔隙比、饱和度等指标的相互推导</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>

      <!-- 达西定律 -->
      <view class="tool-card" @click="goTo('/pages/calculator/darcy-law')">
        <view class="tool-icon-wrap bg-blue2">
          <text class="tool-icon">K</text>
        </view>
        <view class="tool-info">
          <view class="tool-name">达西定律渗透计算</view>
          <view class="tool-desc">渗透系数、流量、渗透力、临界水力梯度、流土判别</view>
        </view>
        <view class="tool-arrow">›</view>
      </view>
    </view>

    <view class="soon-notice">更多土力学计算工具开发中…</view>

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
  display: flex; align-items: center; background: #FAF8F3;
  margin: 0 20rpx 16rpx; padding: 32rpx;
  border-radius: 22rpx; box-shadow: 0 8rpx 24rpx rgba(18,63,67,.06);
}
.tool-card:active { transform: scale(0.98); background: #F2F1EC; }

.tool-icon-wrap {
  width: 96rpx; height: 96rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
  margin-right: 24rpx; flex-shrink: 0;
}
.bg-brown,.bg-blue2 { background: #E0EFED; }
.tool-icon { font-size: 24rpx;font-weight:800;color:#14575B }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 650; color: #17383A; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #7C8987; }
.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }

.soon-notice {
  text-align: center; font-size: 24rpx; color: #bbb;
  padding: 40rpx 0;
}
</style>
