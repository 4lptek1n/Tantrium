#!/usr/bin/env python3
"""F5 quantitative test: compare the rational model P_{lambda,d}(z) Jensen
polynomials against the REAL Riemann Xi Jensen polynomials J_Xi^{d,n}, in the
affine-invariant (mean 0, var 1) root normalization. Records that the model is
xi's LEADING ASYMPTOTIC Jensen family (lambda(n)~1/sqrt(n)) but not exact
(residual grows with degree d). See proofs/ell2_diagonal_residue/f5_model_vs_real_xi.md."""
import importlib.util, numpy as np
import mpmath as mp
from mpmath import binomial

spec = importlib.util.spec_from_file_location("eng", "tools/run_positivity_engine_v1.py")
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
mp.mp.dps = 22

def Xi(z):
    s = mp.mpf('0.5') + 1j*z
    return mp.mpf('0.5')*s*(s-1)*mp.pi**(-s/2)*mp.gamma(s/2)*mp.zeta(s)

def xi_jensen_coeffs(NN):
    tay = mp.taylor(Xi, 0, 2*NN+1)
    return [float(((-1)**k)*mp.re(tay[2*k])) for k in range(NN+1)]

def xi_norm(g, d, n):
    c = [float(binomial(d, j))*g[n+j] for j in range(d+1)]
    r = np.sort(np.roots(c[::-1]).real); return (r-r.mean())/r.std()

def model_grid(d, lams, L=12):
    P = eng.P_coeffs(d, L); out = []
    for lam in lams:
        zc = [sum(float(cc[k])*lam**k for k in range(len(cc))) for cc in P]
        r = np.roots(zc[::-1]); r = r[np.abs(r.imag) < 1e-6].real
        if len(r) < d: continue
        r = np.sort(r); out.append((lam, (r-r.mean())/r.std()))
    return out

def main():
    NN = 14; g = xi_jensen_coeffs(NN)
    lams = np.linspace(-0.1, 3.5, 260)
    print("F5: best-fit lambda(n) and residual (model vs real xi Jensen, normalized roots)")
    for d in [3, 4, 5, 6, 7]:
        if 1+d > NN: continue
        G = model_grid(d, lams)
        for n in [1, 4, 8]:
            if n+d > NN: continue
            t = xi_norm(g, d, n)
            err, lam = min((float(np.sqrt(((mv-t)**2).sum())), float(l)) for l, mv in G)
            print(f"  d={d} n={n}: lambda={lam:.3f} residual={err:.3e}")

if __name__ == "__main__":
    main()
