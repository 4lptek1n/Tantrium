#!/usr/bin/env python3
"""Build the ell=2 rho diagonal atlas from stored rho coefficients.

Input CSV columns: lemma,r,k,rho
Outputs:
- ell2_rho_support_laws.csv
- ell2_rho_diagonal_difference_audit.csv

This script is intentionally small: it analyzes an already-generated rho atlas.
To extend to r=30, first produce ell2_rho_atlas_extended.csv with the same schema.
"""
import argparse, csv
from fractions import Fraction
from pathlib import Path


def F(x):
    return Fraction(str(x)) if str(x).strip() else Fraction(0)


def S(x):
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def read(path):
    rows=[]
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({'lemma':r['lemma'],'r':int(r['r']),'k':int(r['k']),'rho':F(r['rho'])})
    return rows


def write(path, rows, fields):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def forward_diffs(vals):
    layers=[vals]
    while len(layers[-1])>1:
        prev=layers[-1]
        layers.append([prev[i+1]-prev[i] for i in range(len(prev)-1)])
    return layers


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', default='results/engine/ell2_rho_atlas.csv')
    ap.add_argument('--out-dir', default='results/engine')
    args=ap.parse_args()
    rows=read(args.input)
    out=Path(args.out_dir)

    support=[]
    maxk={}
    for lemma in sorted(set(r['lemma'] for r in rows)):
        for rr in sorted(set(r['r'] for r in rows if r['lemma']==lemma)):
            sub=[r for r in rows if r['lemma']==lemma and r['r']==rr]
            ks=[x['k'] for x in sub]; vals=[x['rho'] for x in sub]
            maxk[(lemma,rr)]=max(ks)
            support.append({'lemma':lemma,'r':rr,'k_min':min(ks),'k_max':max(ks),'num_k':len(ks),'min_rho':S(min(vals)),'max_rho':S(max(vals)),'neg_count':sum(v<0 for v in vals),'zero_count':sum(v==0 for v in vals)})
    write(out/'ell2_rho_support_laws.csv', support, ['lemma','r','k_min','k_max','num_k','min_rho','max_rho','neg_count','zero_count'])

    bydiag={}
    for x in rows:
        m=maxk[(x['lemma'],x['r'])]-x['k']
        bydiag.setdefault((x['lemma'],m),[]).append((x['r'],x['rho']))
    audit=[]
    for (lemma,m), seq in sorted(bydiag.items()):
        seq=sorted(seq)
        vals=[v for _,v in seq]
        layers=forward_diffs(vals)
        neg=sum(1 for layer in layers for v in layer if v<0)
        row={'lemma':lemma,'m':m,'num_points':len(vals),'max_order':len(layers)-1,'negative_differences':neg}
        for i in range(4):
            row[f'min_order{i}']=S(min(layers[i])) if i<len(layers) else ''
        audit.append(row)
    write(out/'ell2_rho_diagonal_difference_audit.csv', audit, ['lemma','m','num_points','max_order','negative_differences','min_order0','min_order1','min_order2','min_order3'])

if __name__ == '__main__':
    main()
