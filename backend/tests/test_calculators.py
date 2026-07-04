"""
计算模块单元测试

验证正截面承载力和配筋计算与手算结果的一致性。
所有手算结果基于 GB 50010-2010 规范公式。
"""

import sys
sys.path.insert(0, '.')

import math
from calculators.bearing_capacity import (
    calculate_bearing_capacity,
    BearingCapacityInput,
    CONCRETE_FC, REBAR_FY, get_alpha1, get_xi_b, get_epsilon_cu,
)
from calculators.reinforcement import (
    calculate_reinforcement,
    ReinforcementInput,
)
from calculators.shear_capacity import (
    calculate_shear_capacity,
    ShearCapacityInput,
    get_beta_c, get_beta_h,
)
from calculators.section_properties import (
    calculate_section_properties,
    SectionPropertiesInput,
)


# =============================================================================
# 正截面承载力测试
# =============================================================================

class TestBearingCapacity:
    """正截面承载力计算测试"""

    def test_check_single_4d20(self):
        """
        校核: 单筋截面 4Φ20

        手算验证:
          b=250, h=500, C30(fc=14.3), HRB400(fy=360), a_s=40
          h0 = 460
          As = 1256 (4Φ20)
          x = fy*As/(alpha1*fc*b) = 360*1256/(1.0*14.3*250) = 126.46 mm
          Mu = alpha1*fc*b*x*(h0-x/2) = 1.0*14.3*250*126.46*(460-126.46/2)/1e6
             = 179.4 kN.m
        """
        inp = BearingCapacityInput(
            b=250, h=500, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, as_type='single', as_given=1256,
        )
        r = calculate_bearing_capacity(inp)

        # 手算期望值
        h0_exp = 460
        x_exp = 360 * 1256 / (1.0 * 14.3 * 250)  # 126.46
        mu_exp = 1.0 * 14.3 * 250 * x_exp * (h0_exp - x_exp / 2) / 1e6  # ≈179.4

        assert r.h0 == h0_exp, f"h0: {r.h0} != {h0_exp}"
        assert abs(r.x - x_exp) < 0.1, f"x: {r.x} != {x_exp}"
        assert abs(r.mu - mu_exp) < 0.5, f"Mu: {r.mu} != {mu_exp}"
        assert r.status == "ok", f"status: {r.status}"
        print(f"  [PASS] 校核 4Φ20: Mu={r.mu:.1f} kN.m (手算 {mu_exp:.1f})")

    def test_check_single_3d25(self):
        """
        校核: 单筋截面 3Φ25

        手算:
          b=300, h=600, C30, HRB400, a_s=40
          h0 = 560
          As = 1472.7 (3Φ25, 3×490.9)
          x = 360*1472.7/(1.0*14.3*300) = 123.7 mm
          Mu = 14.3*300*123.7*(560-123.7/2)/1e6 = 264.3 kN.m
        """
        As_3d25 = 3 * 490.9  # 1472.7
        inp = BearingCapacityInput(
            b=300, h=600, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, as_type='single', as_given=As_3d25,
        )
        r = calculate_bearing_capacity(inp)

        h0_exp = 560
        x_exp = 360 * As_3d25 / (1.0 * 14.3 * 300)
        mu_exp = 1.0 * 14.3 * 300 * x_exp * (h0_exp - x_exp / 2) / 1e6

        assert abs(r.x - x_exp) < 0.2, f"x: {r.x} != {x_exp}"
        assert abs(r.mu - mu_exp) < 0.5, f"Mu: {r.mu} != {mu_exp}"
        print(f"  [PASS] 校核 3Φ25: Mu={r.mu:.1f} kN.m (手算 {mu_exp:.1f})")

    def test_check_over_reinforced(self):
        """校核: 超筋截面"""
        # 超大配筋 → 超筋
        inp = BearingCapacityInput(
            b=300, h=600, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, as_type='single', as_given=8000,  # 远超最大配筋
        )
        r = calculate_bearing_capacity(inp)

        assert r.status == "over_reinforced", f"Expected over_reinforced, got {r.status}"
        print(f"  [PASS] 超筋判定: xi={r.xi:.4f} > xi_b={r.xi_b:.4f}")

    def test_min_reinforcement(self):
        """校核: 少筋截面"""
        inp = BearingCapacityInput(
            b=300, h=600, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, as_type='single', as_given=100,  # 极少配筋
        )
        r = calculate_bearing_capacity(inp)

        assert r.status == "under_reinforced", f"Expected under_reinforced, got {r.status}"
        print(f"  [PASS] 少筋判定")

    def test_different_concrete_grades(self):
        """测试不同混凝土等级的系数"""
        # alpha1
        assert get_alpha1('C30') == 1.0
        assert get_alpha1('C50') == 1.0
        assert 0.97 < get_alpha1('C60') < 1.0
        assert get_alpha1('C80') == 0.94, f"C80 alpha1 should be 0.94, got {get_alpha1('C80')}"
        # epsilon_cu
        assert get_epsilon_cu('C30') == 0.0033
        assert get_epsilon_cu('C50') == 0.0033
        assert get_epsilon_cu('C80') == 0.0030
        # xi_b decreases with concrete grade
        xi_b_C30 = get_xi_b('C30', 'HRB400')
        xi_b_C80 = get_xi_b('C80', 'HRB400')
        assert xi_b_C80 < xi_b_C30, f"xi_b(C80)={xi_b_C80:.4f} < xi_b(C30)={xi_b_C30:.4f}"
        assert abs(xi_b_C30 - 0.518) < 0.001
        print(f"  [PASS] alpha1: C30=1.0, C80={get_alpha1('C80')}")
        print(f"  [PASS] epsilon_cu: C30={get_epsilon_cu('C30')}, C80={get_epsilon_cu('C80')}")
        print(f"  [PASS] xi_b(HRB400): C30={xi_b_C30:.4f}, C80={xi_b_C80:.4f}")

    def test_design_mode_single(self):
        """测试单筋设计模式输出两档配筋方案（最小+最大）"""
        inp = BearingCapacityInput(
            b=300, h=600, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, as_type='single', as_given=None,  # 设计模式
        )
        r = calculate_bearing_capacity(inp)

        assert r.design_points is not None, "设计模式应有 design_points"
        assert len(r.design_points) == 2, f"应有2档，实际 {len(r.design_points)}"

        pt_min, pt_max = r.design_points
        assert pt_min['label'] == '最小配筋'
        assert pt_max['label'] == '最大配筋(界限)'
        assert pt_min['rho'] == round(r.rho_min, 4)
        assert pt_max['rho'] == round(r.rho_max, 4)
        assert pt_min['As'] < pt_max['As']
        assert pt_min['Mu'] < pt_max['Mu']

        print(f"  [PASS] 单筋设计: 最小 ρ={pt_min['rho']:.4f} As={pt_min['As']:.1f} Mu={pt_min['Mu']:.3f}")
        print(f"         最大 ρ={pt_max['rho']:.4f} As={pt_max['As']:.1f} Mu={pt_max['Mu']:.3f}")

    def test_design_mode_double(self):
        """测试双筋设计模式：不再回退到单筋"""
        inp = BearingCapacityInput(
            b=300, h=600, concrete_grade='C30', rebar_grade='HRB400',
            a_s=40, a_s_prime=40, as_type='double', as_given=None,
        )
        r = calculate_bearing_capacity(inp)

        # 双筋设计模式下应有 design_points
        assert r.design_points is not None, "双筋设计也应该有 design_points"
        # 每个点应有 As, As_prime 等字段
        for pt in r.design_points:
            assert 'As_prime' in pt
            assert pt['As_prime'] > 0, f"M={pt.get('M')} 应有受压钢筋"
        # status 应该是 ok 而不是 need_double（因为这是设计参考，不是校核报错）
        assert r.status == 'ok'

        print(f"  [PASS] 双筋设计: 单筋上限 Mu={r.mu:.3f} kN·m, {len(r.design_points)}个参考方案")


# =============================================================================
# 配筋计算测试
# =============================================================================

class TestReinforcement:
    """配筋计算测试"""

    def test_design_m150(self):
        """
        配筋设计: M=150 kN.m

        手算:
          b=250, h=500, C30, HRB400, a_s=40, h0=460
          M=150e6 N.mm
          alphas = 150e6 / (1.0*14.3*250*460^2) = 0.1982
          xi = 1-√(1-2*0.1982) = 0.2233
          gammas = 1-0.5*0.2233 = 0.8884
          As = 150e6 / (360*0.8884*460) = 1020.6 mm^2
        """
        inp = ReinforcementInput(
            M=150, b=250, h=500, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        # 手算期望值
        h0 = 460
        alpha_s_exp = 150e6 / (1.0 * 14.3 * 250 * 460 * 460)
        xi_exp = 1 - math.sqrt(1 - 2 * alpha_s_exp)
        gamma_s_exp = 1 - 0.5 * xi_exp
        as_exp = 150e6 / (360 * gamma_s_exp * 460)

        assert abs(r.alpha_s - alpha_s_exp) < 0.002, f"alphas: {r.alpha_s} vs {alpha_s_exp}"
        assert abs(r.xi - xi_exp) < 0.002, f"xi: {r.xi} vs {xi_exp}"
        assert abs(r.as_req - as_exp) < 2, f"As: {r.as_req} vs {as_exp}"
        assert not r.need_double, "Should be single reinforcement"
        print(f"  [PASS] M=150: As={r.as_req:.1f} mm^2 (手算 {as_exp:.1f}), xi={r.xi:.4f}")

    def test_design_m200(self):
        """
        配筋设计: M=200 kN.m (更大弯矩)

        手算:
          b=300, h=600, C30, HRB400, a_s=40, h0=560
          alphas = 200e6 / (1.0*14.3*300*560^2) = 0.1486
          xi = 1-√(1-2*0.1486) = 0.1617
          gammas = 0.9192
          As = 200e6 / (360*0.9192*560) = 1079.4 mm^2
        """
        inp = ReinforcementInput(
            M=200, b=300, h=600, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        h0 = 560
        alpha_s_exp = 200e6 / (1.0 * 14.3 * 300 * h0 * h0)
        xi_exp = 1 - math.sqrt(1 - 2 * alpha_s_exp)
        as_exp = 200e6 / (360 * (1 - 0.5 * xi_exp) * h0)

        assert abs(r.as_req - as_exp) < 2, f"As: {r.as_req} vs {as_exp}"
        assert not r.need_double
        print(f"  [PASS] M=200: As={r.as_req:.1f} mm^2 (手算 {as_exp:.1f}), xi={r.xi:.4f}")

    def test_double_reinforcement_needed(self):
        """
        需要双筋的大弯矩

        300×600, C30, HRB400
        单筋最大承载力 Mu_max ≈ alpha1*fc*b*xib*h0*(h0-xib*h0/2)/1e6
          = 14.3*300*0.518*560*(560-0.518*560/2)/1e6
          ≈ 14.3*300*290.1*414.9/1e6 = 516 kN.m
        所以 M=600 应该需要双筋
        """
        inp = ReinforcementInput(
            M=600, b=300, h=600, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        assert r.need_double, f"Expected double reinforcement for M=600 kN.m"
        assert r.as_prime_req > 0, f"Should have compression reinforcement"
        print(f"  [PASS] 双筋判定: As={r.as_req:.1f} mm^2, As'={r.as_prime_req:.1f} mm^2")

    def test_schemes_generated(self):
        """验证选筋方案生成"""
        inp = ReinforcementInput(
            M=150, b=250, h=500, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        assert len(r.schemes) > 0, "Should generate reinforcement schemes"
        # 第一个方案应该最接近 As_req
        best = r.schemes[0]
        diff = abs(best.area - r.as_req) / r.as_req
        assert diff < 0.15, f"Best scheme diff too large: {diff:.1%}"
        print(f"  [PASS] 选筋方案: {best.description} (面积 {best.area:.1f} mm^2, 误差 {diff:.1%})")

    def test_min_reinforcement_handling(self):
        """验证最小配筋率处理"""
        # 极小弯矩 → 按最小配筋率
        inp = ReinforcementInput(
            M=5, b=300, h=600, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        assert r.status == "min_reinforcement", f"Expected min_reinforcement, got {r.status}"
        assert r.as_req >= r.as_min * 0.99, f"As should be at least As_min"
        print(f"  [PASS] 最小配筋: As={r.as_req:.1f} >= As_min={r.as_min:.1f} mm^2")

    def test_as_min_uses_h(self):
        """验证 As_min 使用全截面高度 h 而非有效高度 h0"""
        inp = ReinforcementInput(
            M=5, b=300, h=600, concrete_grade='C30', rebar_grade='HRB400', a_s=40,
        )
        r = calculate_reinforcement(inp)

        # rho_min = max(0.002, 0.45*1.43/360) = max(0.002, 0.00179) = 0.002
        rho_min = max(0.002, 0.45 * 1.43 / 360)
        as_min_correct = rho_min * 300 * 600  # 用 h=600
        as_min_wrong = rho_min * 300 * 560    # 用 h0=560（旧错误做法）

        assert abs(r.as_min - as_min_correct) < 1, \
            f"As_min={r.as_min:.1f} should be ~{as_min_correct:.1f} (using h=600), not {as_min_wrong:.1f} (using h0=560)"
        print(f"  [PASS] As_min 使用 h: As_min={r.as_min:.1f} (正: {as_min_correct:.1f}, 误: {as_min_wrong:.1f})")


# =============================================================================
# API 集成测试
# =============================================================================

class TestAPI:
    """FastAPI 端点集成测试"""

    def test_bearing_capacity_api(self):
        """测试正截面承载力 API"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        resp = client.post('/api/calculate/bearing-capacity', json={
            'b': 300, 'h': 600, 'concrete_grade': 'C30', 'rebar_grade': 'HRB400',
            'a_s': 40, 'as_type': 'single', 'as_given': 1256,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert abs(data['data']['mu'] - 229.4) < 2  # 手算 Mu≈229.4
        assert data['data']['status'] == 'ok'
        print(f"  [PASS] API 正截面承载力: status=200, Mu={data['data']['mu']}")

    def test_reinforcement_api(self):
        """测试配筋计算 API"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        resp = client.post('/api/calculate/reinforcement', json={
            'M': 200, 'b': 300, 'h': 600, 'concrete_grade': 'C30',
            'rebar_grade': 'HRB400', 'a_s': 40,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert abs(data['data']['as_req'] - 1079) < 10
        assert len(data['data']['schemes']) > 0
        print(f"  [PASS] API 配筋计算: status=200, As={data['data']['as_req']} mm^2")

    def test_references_api(self):
        """测试材料参考表 API"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        resp = client.get('/api/references')
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert 'C30' in data['concrete']['fc']
        assert 'HRB400' in data['rebar']['fy']
        print(f"  [PASS] API 材料参考: 混凝土{len(data['concrete']['grades'])}种, "
              f"钢筋{len(data['rebar']['grades'])}种")

    def test_validation_error(self):
        """测试参数校验"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # 无效混凝土等级
        resp = client.post('/api/calculate/bearing-capacity', json={
            'b': 300, 'h': 600, 'concrete_grade': 'INVALID',
            'rebar_grade': 'HRB400', 'a_s': 40, 'as_type': 'single',
        })
        assert resp.status_code == 422  # Pydantic validation error
        print(f"  [PASS] API 参数校验: 无效混凝土等级 → 422")

        # 无效钢筋牌号（应在后端计算时检测）
        resp = client.post('/api/calculate/bearing-capacity', json={
            'b': 300, 'h': 600, 'concrete_grade': 'C30',
            'rebar_grade': 'INVALID', 'a_s': 40, 'as_type': 'single',
        })
        assert resp.status_code == 422
        print(f"  [PASS] API 参数校验: 无效钢筋牌号 → 422")

    def test_section_design_api(self):
        """测试截面统一设计 API"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        resp = client.post('/api/calculate/section-design', json={
            'b': 300, 'h': 600,
            'concrete_grade': 'C30', 'rebar_grade': 'HRB400',
            'stirrup_grade': 'HPB300', 'a_s': 40,
            'load_type': 'uniform',
            'stirrup_diameter': 8, 'stirrup_legs': 2, 'stirrup_spacing': 200,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        # 正截面结果
        assert 'flexural' in data['data']
        assert data['data']['flexural']['mu'] > 0
        assert 'design_points' in data['data']['flexural']
        # 斜截面结果
        assert 'shear' in data['data']
        assert data['data']['shear']['V_cs'] > data['data']['shear']['V_c']
        assert data['data']['shear']['V_max'] > 0
        print(f"  [PASS] API 截面设计: Mu={data['data']['flexural']['mu']:.3f}, V_cs={data['data']['shear']['V_cs']:.3f}")

    def test_section_properties_api(self):
        """测试截面几何性质 API"""
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # 矩形
        resp = client.post('/api/calculate/section-properties', json={
            'shape': 'rectangle', 'b': 200, 'h': 400,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert abs(data['data']['A'] - 80000) < 1
        assert abs(data['data']['I_x'] - 1066666667) < 10000
        print(f"  [PASS] API 截面性质-矩形: A={data['data']['A']}, I_x={data['data']['I_x']}")

        # 圆形
        resp = client.post('/api/calculate/section-properties', json={
            'shape': 'circle', 'd': 200,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data['data']['I_y'] == data['data']['I_x']
        print(f"  [PASS] API 截面性质-圆形: I_x={data['data']['I_x']:.0f}, 对称验证通过")


# =============================================================================
# 斜截面承载力测试
# =============================================================================

class TestShearCapacity:
    """斜截面受剪承载力测试"""

    def test_shear_uniform_Vc(self):
        """
        均布荷载下混凝土项 V_c 手算验证

        b=250, h=500, C30, a_s=40, h0=460
        ft=1.43, beta_h=1.0 (h0<800)
        V_c = 0.7 × 1.0 × 1.43 × 250 × 460 / 1000 = 115.115 kN
        """
        inp = ShearCapacityInput(
            b=250, h=500, concrete_grade='C30', a_s=40,
            load_type='uniform',
        )
        r = calculate_shear_capacity(inp)

        V_c_exp = 0.7 * 1.0 * 1.43 * 250 * 460 / 1000  # 115.115
        assert abs(r.V_c - V_c_exp) < 0.5, f"V_c: {r.V_c} != {V_c_exp}"
        assert r.beta_h == 1.0
        assert r.beta_c == 1.0
        assert r.h0 == 460
        print(f"  [PASS] 均布 V_c: {r.V_c:.3f} kN (手算 {V_c_exp:.3f})")

    def test_shear_concentrated_Vc(self):
        """
        集中荷载下混凝土项 V_c

        b=300, h=600, C30, lam=2.0, h0=560
        ft=1.43
        V_c = 1.75/(2+1) × 1.43 × 300 × 560 / 1000 = 140.140 kN
        """
        inp = ShearCapacityInput(
            b=300, h=600, concrete_grade='C30', a_s=40,
            load_type='concentrated', shear_span_ratio=2.0,
        )
        r = calculate_shear_capacity(inp)

        V_c_exp = 1.75 / (2.0 + 1) * 1.43 * 300 * 560 / 1000
        assert abs(r.V_c - V_c_exp) < 0.5, f"V_c: {r.V_c} != {V_c_exp}"
        print(f"  [PASS] 集中 V_c (λ=2.0): {r.V_c:.3f} kN (手算 {V_c_exp:.3f})")

    def test_shear_with_stirrups(self):
        """
        配箍筋后 V_cs 手算验证

        b=250, h=500, C30, HPB300, Φ8@200(2), a_s=40, h0=460
        ft=1.43, fyv=270
        V_c = 115.115 kN
        A_sv = 2×50.3 = 100.6 mm²
        V_sv = 270 × 100.6 / 200 × 460 / 1000 = 62.473 kN
        V_cs = 115.115 + 62.473 = 177.588 kN
        """
        inp = ShearCapacityInput(
            b=250, h=500, concrete_grade='C30', stirrup_grade='HPB300',
            a_s=40, load_type='uniform',
            stirrup_diameter=8, stirrup_legs=2, stirrup_spacing=200,
        )
        r = calculate_shear_capacity(inp)

        V_c_exp = 0.7 * 1.0 * 1.43 * 250 * 460 / 1000
        V_sv_exp = 270 * 100.6 / 200 * 460 / 1000
        V_cs_exp = V_c_exp + V_sv_exp

        assert abs(r.V_cs - V_cs_exp) < 0.5, f"V_cs: {r.V_cs} != {V_cs_exp}"
        assert r.A_sv == 100.6
        assert r.status == 'ok'
        print(f"  [PASS] 配箍 V_cs: {r.V_cs:.3f} kN (手算 {V_cs_exp:.3f}), ρ_sv={r.rho_sv:.4f}")

    def test_shear_V_max(self):
        """截面限制条件 V_max"""
        inp = ShearCapacityInput(
            b=300, h=600, concrete_grade='C30', a_s=40,
            load_type='uniform',
        )
        r = calculate_shear_capacity(inp)

        V_max_exp = 0.25 * 1.0 * 14.3 * 300 * 560 / 1000  # 600.6
        assert abs(r.V_max - V_max_exp) < 1.0
        assert r.V_c < r.V_max, "V_c must be less than V_max"
        print(f"  [PASS] V_max: {r.V_max:.3f} kN, V_c={r.V_c:.3f} kN")

    def test_shear_stirrup_insufficient(self):
        """配箍率不足检测"""
        # 大间距 → 配箍率低于最小
        inp = ShearCapacityInput(
            b=300, h=600, concrete_grade='C30', stirrup_grade='HPB300',
            a_s=40, load_type='uniform',
            stirrup_diameter=6, stirrup_legs=2, stirrup_spacing=400,
        )
        r = calculate_shear_capacity(inp)

        # ρ_sv_min = 0.24*1.43/270 = 0.00127
        # ρ_sv = 2*28.3/(300*400) = 56.6/120000 = 0.00047
        assert r.rho_sv < r.rho_sv_min, f"ρ_sv={r.rho_sv:.5f} should be < ρ_sv_min={r.rho_sv_min:.5f}"
        assert r.status == 'insufficient'
        print(f"  [PASS] 配箍不足: ρ_sv={r.rho_sv:.5f} < ρ_sv_min={r.rho_sv_min:.5f}")

    def test_beta_c_beta_h(self):
        """β_c 和 β_h 系数测试"""
        assert get_beta_c('C30') == 1.0
        assert get_beta_c('C50') == 1.0
        assert get_beta_c('C80') == 0.8
        assert get_beta_h(460) == 1.0    # h0<800
        assert get_beta_h(1000) < 1.0    # h0>800, reduction
        assert get_beta_h(2500) < 0.85   # h0>2000, clamped
        print(f"  [PASS] β_c: C30=1.0, C80=0.8; β_h(1000)={get_beta_h(1000):.4f}")


# =============================================================================
# 截面几何性质测试
# =============================================================================

class TestSectionProperties:
    """截面几何性质计算测试"""

    def test_rectangle_200x400(self):
        """矩形 200×400
        手算:
          A = 200×400 = 80000 mm²
          I_x = 200×400³/12 = 200×64000000/12 = 1,066,666,667 mm⁴
          I_y = 400×200³/12 = 400×8000000/12 = 266,666,667 mm⁴
          W_x = 200×400²/6 = 200×160000/6 = 5,333,333 mm³
          W_y = 400×200²/6 = 400×40000/6 = 2,666,667 mm³
          i_x = 400/√12 = 115.47 mm
          i_y = 200/√12 = 57.74 mm
          S_x = 200×400²/8 = 4,000,000 mm³
        """
        inp = SectionPropertiesInput(shape='rectangle', b=200, h=400)
        r = calculate_section_properties(inp)

        assert r.status == 'ok'
        assert abs(r.A - 80000) < 1, f"A: {r.A}"
        assert abs(r.I_x - 1066666667) < 10000, f"I_x: {r.I_x}"
        assert abs(r.I_y - 266666667) < 10000, f"I_y: {r.I_y}"
        assert abs(r.W_x - 5333333) < 100, f"W_x: {r.W_x}"
        assert abs(r.W_y - 2666667) < 100, f"W_y: {r.W_y}"
        assert abs(r.i_x - 115.47) < 0.1, f"i_x: {r.i_x}"
        assert abs(r.i_y - 57.74) < 0.1, f"i_y: {r.i_y}"
        assert abs(r.S_x - 4000000) < 100, f"S_x: {r.S_x}"
        print(f"  [PASS] 矩形200×400: A={r.A}, I_x={r.I_x:.0f}, W_x={r.W_x:.0f}, i_x={r.i_x}")

    def test_circle_d200(self):
        """圆形 d=200
        手算:
          A = π×200²/4 = 31,415.9 mm²
          I_x = π×200⁴/64 = 78,539,816 mm⁴
          W_x = π×200³/32 = 785,398 mm³
          i_x = 200/4 = 50 mm
          S_x = 200³/12 = 666,667 mm³
        """
        inp = SectionPropertiesInput(shape='circle', d=200)
        r = calculate_section_properties(inp)

        assert r.status == 'ok'
        assert abs(r.A - 31415.9) < 1, f"A: {r.A}"
        assert abs(r.I_x - 78539816) < 1000, f"I_x: {r.I_x}"
        assert abs(r.I_y - r.I_x) < 1, f"I_y should == I_x"
        assert abs(r.W_x - 785398) < 10, f"W_x: {r.W_x}"
        assert abs(r.i_x - 50) < 0.1, f"i_x: {r.i_x}"
        assert abs(r.S_x - 666667) < 100, f"S_x: {r.S_x}"
        print(f"  [PASS] 圆形d=200: A={r.A}, I_x={r.I_x:.0f}, i_x={r.i_x}")

    def test_annular_D200_d100(self):
        """环形 D=200, d=100
        手算:
          A = π×(40000-10000)/4 = 23,561.9 mm²
          I_x = π×(200⁴-100⁴)/64 = π×(1.6e9-1e8)/64 = 73,631,078 mm⁴
          S_x = (200³-100³)/12 = (8e6-1e6)/12 = 583,333 mm³
        """
        inp = SectionPropertiesInput(shape='annular', D=200, d=100)
        r = calculate_section_properties(inp)

        assert r.status == 'ok'
        assert abs(r.A - 23561.9) < 1, f"A: {r.A}"
        assert abs(r.I_x - 73631078) < 1000, f"I_x: {r.I_x}"
        assert abs(r.S_x - 583333) < 100, f"S_x: {r.S_x}"
        # 内外径验证：环形 i 应介于实心圆和薄壁之间
        # 实心圆 d=200: i=50; 环形: i=√(200²+100²)/4=55.9
        assert abs(r.i_x - 55.9) < 0.1, f"i_x: {r.i_x} (expected ~55.9)"
        print(f"  [PASS] 环形D200/d100: A={r.A}, I_x={r.I_x:.0f}, i_x={r.i_x}")

    def test_t_section(self):
        """T形截面: b_f=400, h_f=100, b_w=200, h=500
        手算:
          A = 400×100 + 200×400 = 120,000 mm²
          y_c = [400×100×450 + 200×400×200] / 120000
              = [18,000,000 + 16,000,000] / 120000 = 283.33 mm
        """
        inp = SectionPropertiesInput(
            shape='t-section', b_f=400, h_f=100, b_w=200, h=500,
        )
        r = calculate_section_properties(inp)

        assert r.status == 'ok'
        assert abs(r.A - 120000) < 1, f"A: {r.A}"
        assert abs(r.y_c - 283.3) < 1.0, f"y_c: {r.y_c} (expected ~283.3)"
        # I_x 应大于同尺寸矩形的一半（T形材料偏上，惯性矩偏小）
        rect_I_x = 400 * 500**3 / 12  # 整个矩形
        assert r.I_x < rect_I_x, f"I_x should be < full rectangle ({rect_I_x:.0f})"
        assert r.I_x > rect_I_x * 0.3, f"I_x should be > 30% of full rectangle"
        print(f"  [PASS] T形: A={r.A}, y_c={r.y_c}, I_x={r.I_x:.0f}, W_x={r.W_x:.0f}")

    def test_i_beam(self):
        """工字钢: b_f=300, h=400, t_f=20, t_w=12
        手算:
          h_w = 400 - 2×20 = 360
          A = 2×300×20 + 360×12 = 12000 + 4320 = 16,320 mm²
          I_x = 300×400³/12 - (300-12)×360³/12
              = 300×64e6/12 - 288×46.656e6/12
              = 1,600,000,000 - 1,119,744,000 = 480,256,000
        """
        inp = SectionPropertiesInput(
            shape='i-beam', b_f=300, h=400, t_f=20, t_w=12,
        )
        r = calculate_section_properties(inp)

        assert r.status == 'ok'
        assert abs(r.A - 16320) < 1, f"A: {r.A}"
        I_x_exp = 300*400**3/12 - (300-12)*(400-2*20)**3/12
        assert abs(r.I_x - I_x_exp) < 10000, f"I_x: {r.I_x} (expected {I_x_exp:.0f})"
        # 双轴对称: y_c = h/2
        assert abs(r.y_c - 200) < 0.1, f"y_c: {r.y_c} (expected 200)"
        print(f"  [PASS] 工字钢: A={r.A}, I_x={r.I_x:.0f}, I_y={r.I_y:.0f}, W_x={r.W_x:.0f}")

    def test_symmetry_circle(self):
        """圆形截面：I_x==I_y, W_x==W_y, i_x==i_y"""
        inp = SectionPropertiesInput(shape='circle', d=300)
        r = calculate_section_properties(inp)

        assert r.I_x == r.I_y, f"I_x({r.I_x}) should equal I_y({r.I_y})"
        assert r.W_x == r.W_y, f"W_x should equal W_y"
        assert r.i_x == r.i_y, f"i_x should equal i_y"
        print(f"  [PASS] 圆形对称性: I_x=I_y={r.I_x:.0f}, i_x=i_y={r.i_x}")

    def test_rectangle_i_x_vs_i_y(self):
        """矩形 b > h 时 I_y > I_x"""
        inp = SectionPropertiesInput(shape='rectangle', b=600, h=300)
        r = calculate_section_properties(inp)

        assert r.I_y > r.I_x, f"For b>h, I_y({r.I_y}) should > I_x({r.I_x})"
        assert r.i_y > r.i_x, f"For b>h, i_y({r.i_y}) should > i_x({r.i_x})"
        print(f"  [PASS] b>h矩形: I_x={r.I_x:.0f}, I_y={r.I_y:.0f}, I_y > I_x OK")

    def test_invalid_shape(self):
        """不支持的截面形状应抛出 ValueError"""
        try:
            inp = SectionPropertiesInput(shape='triangle')
            calculate_section_properties(inp)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"  [PASS] 无效形状检测: {e}")

    def test_validation_missing_params(self):
        """缺少必要参数应抛出 ValueError"""
        # 矩形缺少 h
        try:
            inp = SectionPropertiesInput(shape='rectangle', b=200, h=0)
            calculate_section_properties(inp)
            assert False, "Should have raised ValueError for h=0"
        except ValueError as e:
            print(f"  [PASS] 参数校验: h=0 → ValueError")

        # 环形内径大于外径
        try:
            inp = SectionPropertiesInput(shape='annular', D=100, d=200)
            calculate_section_properties(inp)
            assert False, "Should have raised ValueError for d > D"
        except ValueError as e:
            print(f"  [PASS] 参数校验: d>D → ValueError")


# =============================================================================
# 运行所有测试
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("土木工程计算工具箱 — 单元测试")
    print("=" * 60)

    tests_bearing = TestBearingCapacity()
    tests_rebar = TestReinforcement()
    tests_shear = TestShearCapacity()
    tests_api = TestAPI()
    tests_section = TestSectionProperties()

    all_passed = 0
    all_total = 0

    # 收集测试方法
    for name in dir(tests_bearing):
        if name.startswith('test_'):
            try:
                getattr(tests_bearing, name)()
                all_passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} FAILED: {e}")
            all_total += 1

    print()
    for name in dir(tests_rebar):
        if name.startswith('test_'):
            try:
                getattr(tests_rebar, name)()
                all_passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} FAILED: {e}")
            all_total += 1

    print()
    for name in dir(tests_shear):
        if name.startswith('test_'):
            try:
                getattr(tests_shear, name)()
                all_passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} FAILED: {e}")
            all_total += 1

    print()
    for name in dir(tests_api):
        if name.startswith('test_'):
            try:
                getattr(tests_api, name)()
                all_passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} FAILED: {e}")
            all_total += 1

    print()
    for name in dir(tests_section):
        if name.startswith('test_'):
            try:
                getattr(tests_section, name)()
                all_passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} FAILED: {e}")
            all_total += 1

    print()
    print("=" * 60)
    print(f"结果: {all_passed}/{all_total} 通过")
    if all_passed == all_total:
        print("[PASS] 全部测试通过！")
    else:
        print(f"[FAIL] {all_total - all_passed} 个测试失败")
    print("=" * 60)
