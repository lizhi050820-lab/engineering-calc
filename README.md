# 土木工程计算工具箱

微信小程序，提供土木工程结构设计常用计算功能。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | uni-app (Vue 3) |
| 后端 | Python FastAPI |
| 规范 | GB/T 50010-2010（2024年版） |

## 功能模块

| 模块 | 说明 |
|------|------|
| **截面设计** | 正截面承载力 + 斜截面受剪承载力，一次输入全部计算 |
| **正截面承载力** | 单筋/双筋矩形截面，校核与设计模式 |
| **配筋计算** | 给定设计弯矩，自动计算配筋并推荐选筋方案 |

## 项目结构

```
├── backend/                  # Python FastAPI 后端
│   ├── main.py               # API 应用（4个端点）
│   ├── calculators/
│   │   ├── bearing_capacity.py   # 正截面承载力
│   │   ├── reinforcement.py      # 配筋计算
│   │   └── shear_capacity.py     # 斜截面承载力
│   └── tests/
│       └── test_calculators.py   # 24个单元测试
├── pages/                    # uni-app 前端页面
│   ├── index/                # 首页
│   └── calculator/
│       ├── bearing.vue        # 正截面页面
│       ├── rebar.vue          # 配筋页面
│       └── section-design.vue # 截面设计页面
├── utils/api.js              # API 调用封装
├── pages.json                # 页面路由配置
└── manifest.json             # 小程序配置
```

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

用 HBuilderX 打开项目根目录，运行 → 微信开发者工具。

### 测试

```bash
cd backend
python tests/test_calculators.py
```
