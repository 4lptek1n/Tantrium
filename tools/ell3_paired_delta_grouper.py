#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from pathlib import Path
Key=tuple[int,int,int]
@dataclass(frozen=True)
class Pair:
    pid:int; base:Key; high:Key; coef:Fraction; exact:bool; low0:Fraction; high0:Fraction

def F(s,d=Fraction(0)):
    return d if s is None or str(s).strip()=='' else Fraction(str(s).strip())
def I(s,d=0):
    return d if s is None or str(s).strip()=='' else int(str(s).strip())
def fs(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
def sg(x): return '+' if x>0 else '-' if x<0 else '0'
def lcm(a,b): return abs(a//gcd(a,b)*b) if a and b else abs(a or b)
def mono(k,j,a):
    z=[]
    if a: z.append('Y' if a==1 else f'Y^{a}')
    if k: z.append('q_d' if k==1 else f'q_d^{k}')
    if j: z.append('q_{d-1}' if j==1 else f'q_{{d-1}}^{j}')
    return '*'.join(z) if z else '1'
def dfac(k,j,a):
    m=mono(k,j,a)
    return '(1 - Y*q_d*q_{d-1})' if m=='1' else f'{m}*(1 - Y*q_d*q_{{d-1}})'
def load(path):
    d=defaultdict(Fraction)
    with Path(path).open(newline='') as h:
        for r in csv.DictReader(h):
            d[(I(r.get('qd_power')),I(r.get('qdm1_power')),I(r.get('Y_power')))] += F(r.get('coefficient'))
    return {k:v for k,v in d.items() if v}
def scan(d):
    rows=[]; exact=0
    for k,c in sorted(d.items(),key=lambda it:(it[0][2],it[0][1],it[0][0])):
        h=(k[0]+1,k[1]+1,k[2]+1); hc=d.get(h)
        if hc is None or c*hc>=0: continue
        if abs(hc)==abs(c): exact+=1
        rows.append({'base_qd_power':k[0],'base_qdm1_power':k[1],'base_Y_power':k[2],
        'high_qd_power':h[0],'high_qdm1_power':h[1],'high_Y_power':h[2],
        'base_coefficient':fs(c),'high_coefficient':fs(hc),'abs_high_over_base':fs(abs(hc/c)),
        'exact_opposite':int(abs(hc)==abs(c)),'natural_transport_candidate':('1' if k[1]==0 else f'1/{2**k[1]}'),
        'conservative_cube_candidate':('1' if k[1]==0 else f'1/{2**(3*k[1])}')})
    return exact,rows
def pair(d):
    r=dict(d); out=[]; pid=1
    for k in sorted(d,key=lambda x:(x[2],x[1],x[0])):
        c=r.get(k,Fraction(0)); h=(k[0]+1,k[1]+1,k[2]+1); hc=r.get(h,Fraction(0))
        if not c or not hc or c*hc>=0: continue
        amt=min(abs(c),abs(hc)); dc=amt if c>0 else -amt
        out.append(Pair(pid,k,h,dc,abs(c)==abs(hc),c,hc)); pid+=1
        r[k]=c-dc; r[h]=hc+dc
        if r.get(k)==0: r.pop(k,None)
        if r.get(h)==0: r.pop(h,None)
    return out,{k:v for k,v in r.items() if v}
def write_kernel(path,pairs,res):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    f=['row_type','pair_id','base_qd_power','base_qdm1_power','base_Y_power','high_qd_power','high_qdm1_power','high_Y_power','coefficient','sign','exact_pair','delta_factor','low_monomial','high_monomial','low_initial_residual','high_initial_residual']
    with Path(path).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=f); w.writeheader()
        for p in pairs:
            w.writerow({'row_type':'paired_delta','pair_id':p.pid,'base_qd_power':p.base[0],'base_qdm1_power':p.base[1],'base_Y_power':p.base[2],'high_qd_power':p.high[0],'high_qdm1_power':p.high[1],'high_Y_power':p.high[2],'coefficient':fs(p.coef),'sign':sg(p.coef),'exact_pair':int(p.exact),'delta_factor':dfac(*p.base),'low_monomial':mono(*p.base),'high_monomial':mono(*p.high),'low_initial_residual':fs(p.low0),'high_initial_residual':fs(p.high0)})
        for i,(k,c) in enumerate(sorted(res.items(),key=lambda it:(it[0][1],it[0][0],it[0][2])),1):
            w.writerow({'row_type':'residual','pair_id':f'R{i}','base_qd_power':k[0],'base_qdm1_power':k[1],'base_Y_power':k[2],'coefficient':fs(c),'sign':sg(c),'low_monomial':mono(*k)})
def summary(pairs,res,scanrows):
    ds=sorted(set([p.base[1] for p in pairs]+[k[1] for k in res]+[int(r['base_qdm1_power']) for r in scanrows])); rows=[]
    for m in ds:
        ps=[p for p in pairs if p.base[1]==m]; rs=[c for k,c in res.items() if k[1]==m]
        ratios=[Fraction(str(r['abs_high_over_base'])) for r in scanrows if int(r['base_qdm1_power'])==m]
        den=1
        for p in ps: den=lcm(den,p.coef.denominator)
        for c in rs: den=lcm(den,c.denominator)
        rows.append({'base_qdm1_depth':m,'paired_delta_rows':len(ps),'exact_delta_rows':sum(p.exact for p in ps),'paired_positive':sum(p.coef>0 for p in ps),'paired_negative':sum(p.coef<0 for p in ps),'residual_rows':len(rs),'residual_positive':sum(c>0 for c in rs),'residual_negative':sum(c<0 for c in rs),'common_denominator':den,'opposite_shift_candidates':len(ratios),'min_abs_high_over_base':fs(min(ratios)) if ratios else '','max_abs_high_over_base':fs(max(ratios)) if ratios else '','natural_transport_candidate':'1' if m==0 else f'1/{2**m}','conservative_cube_candidate':'1' if m==0 else f'1/{2**(3*m)}'})
    return rows
def wc(path,rows,fields):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)
def status(path,d,exact,pairs,res,scanrows):
    touch={x for p in pairs for x in (p.base,p.high)}; pa=sum(abs(p.coef) for p in pairs); ra=sum(abs(v) for v in res.values())
    txt=f'''# ELL=3 Paired Delta Grouping Status\n\nInput monomial rows: {len(d)}\nInput positive rows: {sum(v>0 for v in d.values())}\nInput negative rows: {sum(v<0 for v in d.values())}\nExact C/-C shifted Delta pairs: {exact}\nOpposite-sign shifted candidates: {len(scanrows)}\nGreedy paired Delta rows: {len(pairs)}\nRows touched by paired Deltas: {len(touch)}\nResidual rows: {len(res)}\nResidual positive rows: {sum(v>0 for v in res.values())}\nResidual negative rows: {sum(v<0 for v in res.values())}\nTotal paired absolute coefficient mass: {fs(pa)}\nTotal residual absolute coefficient mass: {fs(ra)}\n\nPaired factor: `Y^a q_d^k q_(d-1)^j * (1 - Y q_d q_(d-1))`\n\nTransport candidates: beta_m = 2^-m and conservative beta_m = 2^(-3m) = 8^-m.\n'''
    Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(txt)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',default='results/engine/ell3_mixed_depth_kernel.csv'); ap.add_argument('--output',default='results/engine/ell3_paired_delta_kernel.csv'); ap.add_argument('--summary',default='results/engine/ell3_paired_delta_summary.csv'); ap.add_argument('--transport-scan',default='results/engine/ell3_paired_delta_transport_scan.csv'); ap.add_argument('--status',default='docs/ELL3_PAIRED_DELTA_STATUS.md'); a=ap.parse_args()
    d=load(a.input); exact,sc=scan(d); ps,res=pair(d); sm=summary(ps,res,sc)
    write_kernel(a.output,ps,res)
    wc(a.summary,sm,['base_qdm1_depth','paired_delta_rows','exact_delta_rows','paired_positive','paired_negative','residual_rows','residual_positive','residual_negative','common_denominator','opposite_shift_candidates','min_abs_high_over_base','max_abs_high_over_base','natural_transport_candidate','conservative_cube_candidate'])
    wc(a.transport_scan,sc,['base_qd_power','base_qdm1_power','base_Y_power','high_qd_power','high_qdm1_power','high_Y_power','base_coefficient','high_coefficient','abs_high_over_base','exact_opposite','natural_transport_candidate','conservative_cube_candidate'])
    status(a.status,d,exact,ps,res,sc)
    print(f'read {len(d)} mixed-depth rows from {a.input}'); print(f'found {exact} exact shifted Delta pairs'); print(f'found {len(sc)} opposite-sign shifted candidates'); print(f'wrote {len(ps)} paired Delta rows plus {len(res)} residual rows to {a.output}')
if __name__=='__main__': main()
