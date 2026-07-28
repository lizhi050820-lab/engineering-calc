# Tool verification contracts

## 正截面承载力

- Force equilibrium must hold within rounding tolerance.
- Capacity must increase with As before the limiting compression zone.
- Minimum- and maximum-reinforcement branches must be exercised.
- Double-reinforcement and non-yield compression-steel branches must be exercised.

## 配筋计算

- Required As must not decrease when M increases with other inputs fixed.
- Returned As must be at least As,min.
- Every recommended scheme must have area greater than or equal to required As.

## 截面统一设计

- Flexural output must equal the standalone flexural calculator for identical inputs.
- Shear output must equal the standalone shear reference.
- Vcs must be at least Vc when valid stirrups are present.

## 截面几何性质

- Circle and annulus must satisfy Ix = Iy and Wx = Wy.
- Rectangle scaling by factor s must produce A×s², I×s⁴, W/S×s³, i×s.
- Swapping rectangle b and h must swap Ix and Iy.

## 组合截面

- Translating every block by the same x/y offset must not change centroidal inertia.
- A centered hole must preserve symmetry.
- Net area must equal positive areas minus holes.

## 土力学三相比例

- n = e/(1+e).
- γd = γ/(1+w).
- Sr = w·Gs/e and must remain in the physical range.
- γsat − γw = γ′.

## 达西定律

- v = k·i and Q = v·A.
- For fixed k and A, doubling i doubles v and Q.
- Reversing h1/h2 in a falling-head test must be rejected.

## 螺栓连接

- Total capacity must equal bolt count times per-bolt capacity.
- Ordinary-bolt capacity must be the minimum of shear and bearing.
- High-strength slip resistance must scale linearly with μ, friction surfaces, and pretension.

## 梁内力

- Vertical equilibrium: RA + RB equals total vertical load for two-support beams.
- Moment equilibrium must hold about either support.
- Symmetric loads on symmetric supports must give equal reactions.
- Scaling every load by s must scale reactions, shear, and moments by s.

## 朗肯土压力

- 单层无黏性土主动压力应满足 Eₐ=0.5·Kₐ·γ·H²，合力作用点距墙底 H/3。
- 单层无黏性土被动压力应满足 Eₚ=0.5·Kₚ·γ·H²。
- 水土分算时，总侧压力必须等于有效土压力与静水压力之和。
- 地面均布荷载 q 增加时，主动、被动和静止侧压力均不得减小。
- 分层土每一层内压力随深度线性变化，层间强度指标变化允许压力跳变。
