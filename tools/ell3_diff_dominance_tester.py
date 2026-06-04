#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
@dataclass(frozen=True)
class DiffTerm:
    q:int; diff:int; coefficient:Fraction; rows:int; positive_rows:int; negative_rows:int

def F(s,d=Fraction(0)):
    return d if s is None or str(s).strip()=='' else Fraction(str(s).strip())
def I(s,d=0):
    return d if s is None or str(s).strip()=='' else int(str(s).strip())
def fs(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
def sg(x): return '+' if x>0 else '-' if x<0 else '0'
def pick(row,*names):
    for n in names:
        if n in row and row[n] not in (None,''): return row[n]
    return None

def load_diff_terms(path,q_mode):
    B=defaultdict(Fraction); C=defaultdict(int); P=defaultdict(int); N=defaultdict(int)
    with Path(path).open(newline='') as h:
        r=csv.DictReader(h); fields=set(r.fieldnames or [])
        for row in r:
            c=F(pick(row,'coefficient','coeff','c'))
            if {'q','diff'}.issubset(fields): q=I(row['q']); diff=I(row['diff'])
            elif {'q_coordinate','diff'}.issubset(fields): q=I(row['q_coordinate']); diff=I(row['diff'])
            elif {'qd_power','qdm1_power','Y_power'}.issubset(fields):
                qd=I(row['qd_power']); p=I(row['qdm1_power']); y=I(row['Y_power'])
                if q_mode=='two_qd': q=2*qd
                elif q_mode=='qd': q=qd
                elif q_mode=='qd_plus_p': q=qd+p
                elif q_mode=='two_qd_plus_p': q=2*(qd+p)
                else: raise ValueError(f'unknown q mode: {q_mode}')
                diff=y-p
            else:
                raise ValueError('input must contain q,diff or qd_power,qdm1_power,Y_power')
            k=(q,diff); B[k]+=c; C[k]+=1; P[k]+=int(c>0); N[k]+=int(c<0)
    return [DiffTerm(q,d,c,C[(q,d)],P[(q,d)],N[(q,d)]) for (q,d),c in sorted(B.items()) if c]

def write_diff_table(path,terms):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=['q','diff','coefficient','sign','source_or_deficit','rows','positive_rows','negative_rows']); w.writeheader()
        for t in terms:
            w.writerow({'q':t.q,'diff':t.diff,'coefficient':fs(t.coefficient),'sign':sg(t.coefficient),'source_or_deficit':'source' if t.coefficient>0 else 'deficit','rows':t.rows,'positive_rows':t.positive_rows,'negative_rows':t.negative_rows})

def scan_betas(src,defi,maxpow):
    S=sum(t.coefficient for t in src); D=sum(-t.coefficient for t in defi); rows=[]
    for r in range(maxpow+1):
        b=Fraction(1,2**r); m=b*S-D
        rows.append({'beta':fs(b),'beta_power':r,'transported_source':fs(b*S),'deficit':fs(D),'margin':fs(m),'passes':int(m>=0)})
    return rows,S,D

def greedy_cover(src,defi,beta):
    supply=[{'diff':t.diff,'rem':beta*t.coefficient} for t in sorted(src,key=lambda z:(abs(z.diff),z.diff),reverse=True)]
    demand=[{'diff':t.diff,'rem':-t.coefficient} for t in sorted(defi,key=lambda z:(abs(z.diff),z.diff))]
    rows=[]
    for d in demand:
        for s in sorted(supply,key=lambda u:(abs(u['diff']-d['diff']),u['diff'])):
            if d['rem']<=0: break
            if s['rem']<=0: continue
            a=min(s['rem'],d['rem']); s['rem']-=a; d['rem']-=a
            rows.append({'source_diff':s['diff'],'deficit_diff':d['diff'],'amount':fs(a),'beta':fs(beta),'distance':abs(s['diff']-d['diff'])})
    return rows,sum(d['rem'] for d in demand),sum(s['rem'] for s in supply)

def wc(path,rows,fields):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)

def report(path,input_path,q_target,q_mode,src,defi,S,D,betas,cover,uncovered,leftover):
    pos='\n'.join([f'- diff {t.diff}: {fs(t.coefficient)} from {t.rows} rows' for t in src]) or '- none'
    neg='\n'.join([f'- diff {t.diff}: {fs(-t.coefficient)} deficit from {t.rows} rows' for t in defi]) or '- none'
    best=next((b for b in betas if b['passes']),None); req='undefined' if S==0 else fs(D/S)
    cv='\n'.join([f"- S(diff {r['source_diff']}) -> D(diff {r['deficit_diff']}): {r['amount']}" for r in cover[:20]]) or '- no transfers'
    text=f'''# ELL=3 Diff-Dominance Report\n\nInput: `{input_path}`\nq coordinate mode: `{q_mode}`\nTarget q: {q_target}\n\n## q={q_target} diff table\n\nSources:\n{pos}\n\nDeficits:\n{neg}\n\nTotal source mass S = {fs(S)}\nTotal deficit mass D = {fs(D)}\nNet S-D = {fs(S-D)}\nRequired aggregate beta = D/S = {req}\n\n## Power-of-two transport scan\n\nFirst passing beta in this aggregate projection: {best['beta'] if best else 'none'}\n\nThis certifies only the diff-projected dominance for the chosen q coordinate. If only beta=1 passes, the projection is too coarse to certify a stricter 2^-r transport and the next pass must keep the internal split-family indices.\n\n## Greedy source-to-deficit cover at beta=1\n\nUncovered deficit after greedy cover: {fs(uncovered)}\nLeftover source after greedy cover: {fs(leftover)}\n\n{cv}\n\n## Generated tables\n\n- `results/engine/ell3_diff_dominance_table.csv`\n- `results/engine/ell3_diff_dominance_beta_scan.csv`\n- `results/engine/ell3_diff_dominance_cover.csv`\n'''
    Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(text)

def main():
    ap=argparse.ArgumentParser(description='Test ell=3 diff-dominance at a selected q coordinate.')
    ap.add_argument('--input',default='results/engine/ell3_mixed_depth_kernel.csv'); ap.add_argument('--q-target',type=int,default=20)
    ap.add_argument('--q-mode',default='two_qd',choices=['two_qd','qd','qd_plus_p','two_qd_plus_p']); ap.add_argument('--max-beta-power',type=int,default=18)
    ap.add_argument('--diff-table',default='results/engine/ell3_diff_dominance_table.csv'); ap.add_argument('--beta-scan',default='results/engine/ell3_diff_dominance_beta_scan.csv')
    ap.add_argument('--cover',default='results/engine/ell3_diff_dominance_cover.csv'); ap.add_argument('--report',default='results/engine/ell3_diff_dominance_report.md'); a=ap.parse_args()
    terms=[t for t in load_diff_terms(Path(a.input),a.q_mode) if t.q==a.q_target]
    if not terms: raise SystemExit(f'no terms found for q={a.q_target} in {a.input} with mode {a.q_mode}')
    src=[t for t in terms if t.coefficient>0]; defi=[t for t in terms if t.coefficient<0]
    write_diff_table(Path(a.diff_table),terms); br,S,D=scan_betas(src,defi,a.max_beta_power)
    wc(Path(a.beta_scan),br,['beta','beta_power','transported_source','deficit','margin','passes'])
    cov,unc,left=greedy_cover(src,defi,Fraction(1)); wc(Path(a.cover),cov,['source_diff','deficit_diff','amount','beta','distance'])
    report(Path(a.report),a.input,a.q_target,a.q_mode,src,defi,S,D,br,cov,unc,left)
    print(f'q={a.q_target} sources={len(src)} deficits={len(defi)}')
    print(f'S={fs(S)} D={fs(D)} net={fs(S-D)} required_beta={fs(D/S) if S else "undefined"}')
    print(f'wrote {a.report}')
if __name__=='__main__': main()
