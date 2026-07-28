# 土木工程计算工具箱

面向快速复核与学习的土木工程计算网站，采用 uni-app（Vue 3）开发，并通过 GitHub Pages 免费发布。正式网页中的计算均在浏览器本地完成，无需下载，也不依赖开发者电脑或后端服务器。

公开地址：<https://lizhi050820-lab.github.io/engineering-calc/>

## 功能模块

| 分类 | 计算工具 |
|---|---|
| 混凝土结构设计 | 截面统一设计、正截面承载力、配筋计算 |
| 截面几何性质 | 标准截面、组合截面 |
| 土力学计算 | 三相比例指标、达西定律、朗肯土压力、地基承载力规范验算 |
| 钢结构设计 | 螺栓连接承载力 |
| 结构力学速算 | 梁内力与支座反力 |

朗肯土压力当前支持主动、被动和静止土压力，多层土、地面均布荷载、地下水位，以及水土分算/合算。页面会给出压力分布、合力、作用点、计算步骤和适用范围。

地基承载力规范验算支持 GB 50007—2011 宽深修正、矩形基础轴心/偏心压力、单向大偏心三角形接触压力和双向偏心脱空识别。

## 技术结构

| 层 | 技术与用途 |
|---|---|
| 网站 | uni-app（Vue 3）+ Vite |
| 网页计算核心 | `utils/calculators/` 中的 JavaScript 纯函数 |
| 独立参考实现 | `backend/calculators/` 中的 Python 计算器 |
| API（开发与复核） | Python FastAPI |
| 自动验证 | 固定权威算例、Python/JavaScript 差分测试、性质测试和浏览器回归测试 |
| 发布 | GitHub Actions + GitHub Pages |

## 本地运行

安装依赖后启动 H5：

```powershell
pnpm install
pnpm run dev:h5
```

需要运行 FastAPI 时：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

微信小程序仍可在 HBuilderX 中编译，微信开发者工具应打开 `unpackage/dist/dev/mp-weixin/`。

## 验证

```powershell
pnpm run test:browser-calculators
pnpm run test:authoritative-cases
pnpm run test:rankine
pnpm run test:foundation-bearing
python .agents/skills/calculation-verifier/scripts/verify_project.py --cases-per-tool 500
cd backend
python tests/test_calculators.py
```

最新全量差分与性质测试为 **8300/8300 通过**，其中地基承载力发布前专项验证为 **7800/7800 通过**；Python 后端回归测试为 **62/62 通过**。详细证据在 `verification/reports/`。

> 本工具用于学习、方案比较和快速复核，不能替代具备资质的工程师审核、完整结构分析及正式施工图设计。超出页面列明的理论假定时，应改用相应规范方法或专业软件。
