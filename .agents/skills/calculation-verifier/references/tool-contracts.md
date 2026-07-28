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

## 地基承载力规范验算

- 轴心荷载下四个角点压力必须相等，且 pₖ=(Fₖ+Gₖ)/A。
- 在基础尺寸和其他参数不变时，Fₖ 增加应使 pₖ 线性增加。
- 宽度修正计算宽度必须限制在 3～6 m，埋深小于 0.5 m 时不得产生负的深度修正。
- 全截面受压时，四角压力平均值必须等于 pₖ。
- 单向偏心 e>b/6 时应转入三角形接触压力；e≥b/2 时必须判为合力作用线位于基础外。
- 双向偏心出现拉应力时不得把线性外推的 pₖ,max 当成真实接触压力。

## 钢筋工程速算

- 同一规格和单根长度下，总长度与总重量必须随根数线性变化。
- 重量反算长度后再乘理论单位重量，应回到原重量（显示舍入容差内）。
- 按最大允许间距排布时，实际间距不得大于输入的最大间距。
- 等面积代换根数必须向上取整，替换后的公称面积不得小于原配筋面积。
