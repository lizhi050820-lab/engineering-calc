<template>
  <view class="container">
    <view class="category-intro">
      <view class="intro-kicker">STRUCTURAL MECHANICS</view>
      <view class="intro-title">结构力学速算</view>
      <view class="intro-desc">常见梁型与荷载工况，快速得到支座反力、剪力和弯矩</view>
    </view>

    <view class="tool-card" @click="goTo('/pages/calculator/beam-forces')">
      <view class="tool-icon-wrap"><text class="tool-icon">BM</text></view>
      <view class="tool-info">
        <view class="tool-name">梁内力与支座反力速算</view>
        <view class="tool-desc">简支梁、悬臂梁、外伸梁常见工况</view>
      </view>
      <view class="tool-arrow">›</view>
    </view>
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
.container { padding: 0 0 40rpx; min-height: 100vh; background:#EEF1EF; }
.category-intro{background:#123F43;color:#fff;padding:42rpx 34rpx 38rpx;border-radius:0 0 30rpx 30rpx;margin-bottom:24rpx}
.intro-kicker{font-size:18rpx;letter-spacing:4rpx;color:rgba(255,255,255,.48)}
.intro-title{font-size:42rpx;font-weight:750;margin-top:10rpx}
.intro-desc{font-size:23rpx;color:rgba(255,255,255,.64);margin-top:10rpx}
.tool-card { display:flex;align-items:center;background:#FAF8F3;margin:0 20rpx 16rpx;padding:32rpx;border-radius:22rpx;box-shadow:0 8rpx 24rpx rgba(18,63,67,.06); }
.tool-card:active { transform:scale(.98);background:#F4F2ED; }
.tool-icon-wrap { width:96rpx;height:96rpx;border-radius:24rpx;display:flex;align-items:center;justify-content:center;margin-right:24rpx;background:#E0EFED; }
.tool-icon { font-size:24rpx;font-weight:800;color:#14575B }
.tool-info{flex:1}.tool-name{font-size:32rpx;font-weight:650;color:#17383A;margin-bottom:8rpx}.tool-desc{font-size:24rpx;color:#7C8987}.tool-arrow{font-size:40rpx;color:#9EA9A7;margin-left:12rpx}
</style>
