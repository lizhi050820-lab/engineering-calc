<template>
  <view class="container">
    <view class="tool-list">
      <!-- 三相比例指标 -->
      <view class="tool-card" @click="goTo('/pages/calculator/soil-three-phase')">
        <view class="tool-icon-wrap bg-brown">
          <text class="tool-icon">🧪</text>
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
          <text class="tool-icon">💧</text>
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
.container { padding: 20rpx 0 40rpx; }

.tool-card {
  display: flex; align-items: center; background: #fff;
  margin: 0 20rpx 16rpx; padding: 32rpx;
  border-radius: 16rpx; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.tool-card:active { transform: scale(0.98); background: #FAFBFC; }

.tool-icon-wrap {
  width: 96rpx; height: 96rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
  margin-right: 24rpx; flex-shrink: 0;
}
.bg-brown { background: linear-gradient(135deg, #EFEBE9, #D7CCC8); }
.bg-blue2 { background: linear-gradient(135deg, #E0F2FF, #B3E5FC); }
.tool-icon { font-size: 44rpx; }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 600; color: #222; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #999; }
.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }

.soon-notice {
  text-align: center; font-size: 24rpx; color: #bbb;
  padding: 40rpx 0;
}
</style>
