from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'engine'


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(K=8, J=8, N=8):
    OUT.mkdir(parents=True, exist_ok=True)

    write_csv(
        OUT / 'v1_atlas.csv',
        ['K', 'J', 'N', 'status'],
        [{'K': K, 'J': J, 'N': N, 'status': 'pending_tau_engine_restore'}],
    )

    write_csv(
        OUT / 'v1_cumulants.csv',
        ['level', 'status'],
        [
            {'level': 'L2', 'status': 'pending_cumulant_atlas'},
            {'level': 'L4', 'status': 'pending_cumulant_atlas'},
            {'level': 'L6', 'status': 'pending_cumulant_atlas'},
            {'level': 'L8', 'status': 'pending_cumulant_atlas'},
        ],
    )

    report = OUT / 'v1_failure_report.md'
    report.write_text(
        '# Positivity Engine v1 Failure Report\n\n'
        f'Target window: K={K}, J={J}, N={N}.\n\n'
        'Status: pending tau-engine restoration.\n\n'
        'This runner creates the v1 output contract but does not claim a new atlas computation yet.\n'
        'Next step: connect the restored Bareiss tau engine and cumulant atlas.\n',
        encoding='utf-8',
    )


if __name__ == '__main__':
    main()
