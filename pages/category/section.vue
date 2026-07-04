<template>
  <view class="container">
    <view class="tool-list">
      <!-- 标准截面 -->
      <view class="tool-card" @click="goTo('/pages/calculator/section-props')">
        <view class="tool-icon-wrap bg-purple">
          <text class="tool-icon">📏</text>
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
          <text class="tool-icon">🧩</text>
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
.bg-purple { background: linear-gradient(135deg, #EDE7F6, #D1C4E9); }
.bg-teal   { background: linear-gradient(135deg, #E0F2F1, #B2DFDB); }
.tool-icon { font-size: 44rpx; }

.tool-info { flex: 1; }
.tool-name { font-size: 32rpx; font-weight: 600; color: #222; margin-bottom: 8rpx; }
.tool-desc { font-size: 24rpx; color: #999; }

.tool-arrow { font-size: 40rpx; color: #ccc; margin-left: 12rpx; }
</style>
