# 工程计算批量验算报告

- 时间：2026-07-19T10:02:55+08:00
- Git：`a1f8560`
- 随机种子：`20260719`
- 每项计划算例：500
- 总通过：6900/6900

| 工具 | 算例数 | 通过数 | 通过率 | 最大绝对误差 | 对应字段 |
|---|---:|---:|---:|---:|---|
| bearing | 500 | 500 | 100.00% | 0.001 | xi_b |
| reinforcement | 500 | 500 | 100.00% | 0.1 | as_min |
| section_design | 500 | 500 | 100.00% | 0.001 | shear.V_max |
| section_properties | 500 | 500 | 100.00% | 1 | W_x |
| composite_section | 500 | 500 | 100.00% | 1 | I_y |
| soil_three_phase | 500 | 500 | 100.00% | 0.0001 | w |
| darcy_law | 500 | 500 | 100.00% | 0.0001 | i |
| bolt_connection | 500 | 500 | 100.00% | 0.001 | total_capacity |
| beam_forces | 500 | 500 | 100.00% | 0.001 | fixed_moment |
| mathematical_properties | 2400 | 2400 | 100.00% | 0 | property checks |

## 失败算例

无。Python 参考实现与 JavaScript 网页计算核心在本批算例中一致。

## 结论边界

本报告同时覆盖 Python/JavaScript 差分验证和数学性质测试。它们不单独构成规范公式正确性的最终证明；正式发布前仍须同时通过标注出处的权威固定算例、非法输入测试、项目回归测试和 H5 构建。
