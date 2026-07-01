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
  background-color: #F5F6FA;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 28rpx;
  color: #333;
}

/* 通用按钮 */
.btn-primary {
  background: linear-gradient(135deg, #2C6FCE, #5B9CF5);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 24rpx 0;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  width: 100%;
}

.btn-primary:active {
  opacity: 0.85;
}

.btn-secondary {
  background: #fff;
  color: #2C6FCE;
  border: 2rpx solid #2C6FCE;
  border-radius: 12rpx;
  padding: 24rpx 0;
  font-size: 32rpx;
  text-align: center;
  width: 100%;
}

/* 通用卡片 */
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

/* 表单组 */
.form-group {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 12rpx;
  font-weight: 500;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #F5F6FA;
  border-radius: 12rpx;
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
  background: #F5F6FA;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}

.form-picker .placeholder {
  color: #999;
}

/* 结果区 */
.result-card {
  background: linear-gradient(135deg, #EBF3FF, #F0F7FF);
  border-radius: 16rpx;
  padding: 30rpx;
  margin-top: 20rpx;
  border-left: 8rpx solid #2C6FCE;
}

.result-value {
  font-size: 48rpx;
  font-weight: 700;
  color: #2C6FCE;
  text-align: center;
  margin: 16rpx 0;
}

.result-unit {
  font-size: 28rpx;
  color: #999;
}

.result-label {
  font-size: 26rpx;
  color: #666;
  text-align: center;
}

.status-tag {
  display: inline-block;
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
  font-size: 24rpx;
  margin: 12rpx auto;
}

.status-ok {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-warn {
  background: #FFF3E0;
  color: #E65100;
}

.status-error {
  background: #FFEBEE;
  color: #C62828;
}

/* 公式步骤展开 */
.steps-box {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-top: 16rpx;
}

.step-line {
  font-family: 'Courier New', monospace;
  font-size: 24rpx;
  color: #555;
  line-height: 1.8;
  padding: 4rpx 0;
  border-bottom: 1rpx dashed #eee;
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
</style>
