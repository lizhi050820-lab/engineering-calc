<script>
export default {
  onLaunch() {
    console.log('土木工程计算工具箱 启动')
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  },
}
</script>

<style>
/* 全局样式 */
page {
  background-color: #EEF1EF;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 28rpx;
  color: #333;
}

/* 通用按钮 */
.btn-primary {
  background: #E8734A;
  color: #fff;
  border: none;
  border-radius: 18rpx;
  padding: 24rpx 0;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  width: 100%;
}

.btn-primary:active {
  opacity: 0.9;
  transform: scale(0.985);
}

.btn-secondary {
  background: #fff;
  color: #14575B;
  border: 2rpx solid #14575B;
  border-radius: 18rpx;
  padding: 24rpx 0;
  font-size: 32rpx;
  text-align: center;
  width: 100%;
}

/* 通用卡片 */
.card {
  background: #FAF8F3;
  border-radius: 22rpx;
  padding: 32rpx;
  margin: 20rpx;
  box-shadow: 0 8rpx 26rpx rgba(18, 63, 67, 0.07);
  border: 1rpx solid rgba(18, 63, 67, 0.06);
}

/* 表单组 */
.form-group {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #385759;
  margin-bottom: 12rpx;
  font-weight: 500;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #F0EFEB;
  border-radius: 15rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  box-sizing: border-box;
  border: 2rpx solid transparent;
}

.form-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 80rpx;
  background: #F0EFEB;
  border-radius: 15rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}

.form-picker .placeholder {
  color: #999;
}

/* Grid布局 */
.grid-2 {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.grid-2 > .form-group {
  flex: 1 1 calc(50% - 8rpx);
  min-width: 200rpx;
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
  font-size: 24rpx;
  font-weight: 500;
}

.status-ok {
  background: #D9F0E4;
  color: #26734C;
}

.status-warn {
  background: #FBE8DF;
  color: #B95836;
}

.status-error {
  background: #FFEBEE;
  color: #C62828;
}

/* 计算结果 — 简洁风格 */
.calc-hero {
  text-align: center;
  padding: 16rpx 0 24rpx;
}
.calc-hero-label {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 8rpx;
}
.calc-hero-value {
  display: block;
  font-size: 56rpx;
  font-weight: 800;
  color: #123F43;
  margin-bottom: 12rpx;
}
.calc-hero-unit {
  font-size: 28rpx;
  font-weight: 500;
  color: #999;
}

.calc-process {
  margin-top: 8rpx;
}
.calc-row {
  display: flex;
  align-items: baseline;
  padding: 16rpx 0;
}
.calc-key {
  width: 170rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #385759;
  font-weight: 500;
}
.calc-val {
  flex: 1;
  font-size: 28rpx;
  color: #17383A;
  line-height: 1.75;
  font-variant-numeric: lining-nums tabular-nums;
  letter-spacing: 0.3rpx;
}
.calc-hr {
  height: 1rpx;
  background: #E8E8E8;
}
</style>
