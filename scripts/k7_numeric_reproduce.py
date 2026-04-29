from __future__ import annotations

import json
from pathlib import Path
import sys
import time

try:
    import mpmath as mp
except ModuleNotFoundError:  # local sandbox helper
    sys.path.append('/opt/pyvenv/lib/python3.13/site-packages')
    import mpmath as mp

mp.mp.dps = 100


def top_coefficients_numeric(d: int, rmax: int, lam: mp.mpf) -> list[mp.mpf]:
    total = {0: mp.mpf(1)}
    current = {0: mp.mpf(1)}
    for k in range(1, rmax + 1):
        new: dict[int, mp.mpf] = {}
        for drop, coeff in current.items():
            m = d - drop
            if m >= 2 and drop + 1 <= rmax:
                new[drop + 1] = new.get(drop + 1, mp.mpf(0)) + coeff * lam * m * (m - 1)
            if m >= 2 and drop + 2 <= rmax:
                new[drop + 2] = new.get(drop + 2, mp.mpf(0)) - coeff * mp.mpf(1) / 4 * m * (m - 1)
            if m >= 3 and drop + 3 <= rmax:
                new[drop + 3] = new.get(drop + 3, mp.mpf(0)) - coeff * mp.mpf(1) / 24 * lam * m * (m - 1) * (m - 2)
        current = new
        for drop, coeff in current.items():
            total[drop] = total.get(drop, mp.mpf(0)) + coeff / mp.factorial(k)
    return [total.get(r, mp.mpf(0)) for r in range(rmax + 1)]


def bezout_entry_numeric(d: int, coeffs: list[mp.mpf], r_drop: int, s_drop: int) -> mp.mpf:
    out = mp.mpf(0)
    max_drop = len(coeffs) - 1
    target = r_drop + s_drop - 2
    for u in range(max_drop + 1):
        v = target - u
        if v < 0 or v > max_drop:
            continue
        if u <= v:
            sign = 1
        elif u >= v + 2:
            sign = -1
        else:
            sign = 0
        if sign:
            out += sign * coeffs[u] * (d - v) * coeffs[v]
    return out


def det_k(d: int, j: int, t_value: mp.mpf) -> mp.mpf:
    lam = mp.sqrt(t_value)
    size = j + 1
    coeffs = top_coefficients_numeric(d, 2 * (size - 1), lam)
    drops = list(range(size, 0, -1))
    matrix = mp.matrix([
        [bezout_entry_numeric(d, coeffs, r, s) for s in drops]
        for r in drops
    ])
    return mp.det(matrix)


def normalized_det(d: int, j: int, t_value: mp.mpf) -> mp.mpf:
    return det_k(d, j, t_value) / det_k(d, j, mp.mpf(0))


def bisect_root(d: int, lo: mp.mpf, hi: mp.mpf, steps: int = 90) -> mp.mpf:
    flo = normalized_det(d, 6, lo)
    fhi = normalized_det(d, 6, hi)
    if flo * fhi > 0:
        raise ValueError(f"No sign change on [{lo}, {hi}]: {flo}, {fhi}")
    for _ in range(steps):
        mid = (lo + hi) / 2
        fmid = normalized_det(d, 6, mid)
        if flo * fmid <= 0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid
    return (lo + hi) / 2


def main() -> None:
    out_dir = Path('results')
    out_dir.mkdir(exist_ok=True)
    sample_points = ['0', '0.001', '0.01', '0.02', '0.04', '0.041', '0.042', '0.05', '0.1', '1']
    lines = [
        '# K7 sharpness reproduction',
        '',
        'This report locally reevaluates the trailing `7 x 7` Bezoutian block used for `H_{d,6}`.',
        'It avoids the full symbolic determinant and instead evaluates the same recurrence numerically at high precision.',
        '',
        'The decisive sharpness certificate is the `d=7` sign change near `t=0.041`.',
        '',
    ]
    payload = {}
    for d in [7, 8]:
        start = time.time()
        values = []
        for point in sample_points:
            value = normalized_det(d, 6, mp.mpf(point))
            values.append((point, value))
        root = None
        if d == 7:
            root = bisect_root(d, mp.mpf('0.04'), mp.mpf('0.05'))
        elapsed = time.time() - start
        lines += [
            f'## d={d}',
            '',
            f'- elapsed seconds: `{elapsed:.3f}`',
        ]
        if root is not None:
            lines.append(f'- positive root in `[0.04,0.05]`: `{mp.nstr(root, 40)}`')
        lines += ['', '| t | normalized det K7 | sign |', '|---:|---:|:---:|']
        values_dict = {}
        for point, value in values:
            sign = '+' if value > 0 else '-' if value < 0 else '0'
            lines.append(f'| `{point}` | `{mp.nstr(value, 32)}` | {sign} |')
            values_dict[point] = mp.nstr(value, 80)
        lines.append('')
        payload[str(d)] = {
            'elapsed_seconds': elapsed,
            'root_0p04_0p05': None if root is None else mp.nstr(root, 80),
            'values': values_dict,
        }
    lines += [
        '## Conclusion',
        '',
        '- The `d=7` sign change is reproduced and is enough to prove that universal `j=6` positivity fails.',
        '- The `d=8` sample is negative at `t=0.001`, matching the small-positive failure signal.',
        '- The sampled `d=8` sign profile is not monotone in this normalized determinant evaluation, so the stronger phrase `H_{8,6}(t)<0 for all t>0` should be treated as requiring an exact artifact audit before being used as a proof claim.',
        '',
    ]
    (out_dir / 'k7_sharpness_reproduction.md').write_text('\n'.join(lines), encoding='utf-8')
    (out_dir / 'k7_sharpness_reproduction.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
