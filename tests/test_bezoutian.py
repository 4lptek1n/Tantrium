"""Bezoutian polinom ispat-makinesi testleri (tce-collapse-engine Gate-B izolasyonu)."""
from __future__ import annotations

import sympy as sp

from tantrium.core import bezoutian as bz

# (x-1)(x-2)(x-3) = x^3 - 6x^2 + 11x - 6  ; artan kuvvet katsayılar
HYPERBOLIC_CUBIC = [-6, 11, -6, 1]
NON_HYPERBOLIC = [1, 0, 1]  # x^2 + 1


def test_hyperbolic_detection():
    r = bz.analyze(HYPERBOLIC_CUBIC)
    assert r.hyperbolic is True
    # gerçek-kök olmayan
    r2 = bz.analyze(NON_HYPERBOLIC)
    assert r2.hyperbolic is False


def test_hyperbolic_pivots_positive():
    r = bz.analyze(HYPERBOLIC_CUBIC)
    # tüm Sturm pivotları pozitif (gerçek-kök poli için)
    assert all(sp.sympify(p) > 0 for p in r.pivots)
    assert r.first_five_positive["all_positive"] is True


def test_lah_reference_is_squares():
    # ρ_j(L_d) = (d-j)^2
    assert bz.lah_pivot_reference(5) == [16, 9, 4, 1]
    assert bz.lah_pivot_reference(4) == [9, 4, 1]
    # genel doğrulama: her giriş tam kare ve (d-j)^2
    for d in range(2, 9):
        ref = bz.lah_pivot_reference(d)
        assert ref == [(d - j) ** 2 for j in range(1, d)]


def test_staircase_top_coeff_formula():
    # j=2, n=0: T_2=3 -> 2^3 * (0+1)^1 * (0+2)^2 = 8*1*4 = 32
    assert bz.staircase_top_coeff(2, 0) == 32
    # genel: 2^{T_j} * prod (n+m)^m
    for j in range(1, 5):
        for n in range(0, 4):
            T = j * (j + 1) // 2
            prod = 1
            for m in range(1, j + 1):
                prod *= (n + m) ** m
            assert bz.staircase_top_coeff(j, n) == (2 ** T) * prod
    # T_j ve staircase_degree
    # K6_J5: K_6 blok -> H_{d,5} -> T_5 = 5*6/2 = 15 üst-katsayı indeksi
    assert bz.staircase_T(5) == 15
    assert bz.staircase_T(6) == 21
    assert bz.staircase_degree(2, 1) == 1


def test_first_five_pivots():
    r = bz.first_five_pivots_positive(HYPERBOLIC_CUBIC)
    assert r["all_positive"] is True
    # K7 sharpness referans kökü taşınmış mı
    assert r["k7_reference_root"].startswith("0.0409")
    assert "j=6" in r["k7_sharpness_note"]


def test_bezoutian_matrix_size_and_symmetry():
    # derece d poli -> d x d Bezoutian
    B = bz.bezoutian_matrix(HYPERBOLIC_CUBIC)
    assert len(B) == 3
    assert all(len(row) == 3 for row in B)
    # simetrik
    for i in range(3):
        for j in range(3):
            assert sp.simplify(B[i][j] - B[j][i]) == 0
    # K_2 trailing blok doc formülü: [[(d-1)a1^2-2a2, (d-1)a1],[(d-1)a1, d]]
    # monic P = z^3 + a1 z^2 + a2 z + a3 ; burada a1=-6, a2=11, d=3
    d, a1, a2 = 3, -6, 11
    assert B[2][2] == d
    assert B[1][2] == (d - 1) * a1            # -12
    assert B[1][1] == (d - 1) * a1 ** 2 - 2 * a2  # 50


def test_hidden_factors_ldlt_minor_ratio():
    # LDLᵀ köşegeni D[k,k] = det(K[:k+1])/det(K[:k]) ; çarpımları = tam det
    B = bz.bezoutian_matrix(HYPERBOLIC_CUBIC)
    M = sp.Matrix(B)
    hf = bz.hidden_factors(HYPERBOLIC_CUBIC)
    assert len(hf) == 3
    prod = sp.Integer(1)
    for v in hf:
        prod *= sp.sympify(v)
    assert sp.simplify(prod - M.det()) == 0
    # gerçek-kök poli -> Bezoutian PSD -> tüm köşegen > 0
    assert all(sp.sympify(v) > 0 for v in hf)


def test_lah_deviation_length_and_values():
    dev = bz.lah_deviation(HYPERBOLIC_CUBIC)
    # pivot sayısı 2, lah ref (d=3) = [4,1] -> 2 sapma
    assert len(dev) == 2
    piv = bz.normalized_sturm_pivots_coeffs(HYPERBOLIC_CUBIC)
    ref = bz.lah_pivot_reference(3)
    for j in range(len(dev)):
        assert sp.simplify(dev[j] - (sp.sympify(piv[j]) - ref[j])) == 0


def test_determinism():
    # aynı girdi -> bit-bit aynı çıktı
    a = bz.analyze(HYPERBOLIC_CUBIC).as_dict()
    b = bz.analyze(HYPERBOLIC_CUBIC).as_dict()
    assert a == b
    # bezoutian da deterministik
    assert bz.bezoutian_matrix(HYPERBOLIC_CUBIC) == bz.bezoutian_matrix(HYPERBOLIC_CUBIC)


def test_report_as_dict_and_summary():
    r = bz.analyze(HYPERBOLIC_CUBIC)
    d = r.as_dict()
    assert d["degree"] == 3
    assert d["hyperbolic"] is True
    assert d["bezoutian_size"] == 3
    assert d["lah_reference"] == [4, 1]
    assert isinstance(r.summary(), str) and "Bezoutian" in r.summary()


def test_trailing_block_determinants():
    dets = bz.trailing_block_determinants(HYPERBOLIC_CUBIC)
    # K_1 (1x1) = B[d-1][d-1] = d = 3
    assert dets[0] == 3
    # K_3 = tam Bezoutian determinantı
    M = sp.Matrix(bz.bezoutian_matrix(HYPERBOLIC_CUBIC))
    assert sp.simplify(dets[-1] - M.det()) == 0
