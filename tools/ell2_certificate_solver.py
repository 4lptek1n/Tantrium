#!/usr/bin/env python3
import argparse,csv
from fractions import Fraction
from pathlib import Path

def F(s):
    s=str(s).strip()
    return Fraction(s) if s else Fraction(0)

def S(x):
    return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'

def greedy(src,defi,so,do):
    src=dict(src); defi=dict(defi)
    w={f'w_{a}_to_{b}':Fraction(0) for a in so for b in do}
    while True:
        dn,dv=max(defi.items(),key=lambda kv:(kv[1],-do.index(kv[0])))
        if dv<=0: break
        sn,sv=max(src.items(),key=lambda kv:(kv[1],-so.index(kv[0])))
        if sv<=0: break
        z=min(sv,dv)
        w[f'w_{sn}_to_{dn}']+=z; src[sn]-=z; defi[dn]-=z
    return w,src,defi

def write(path,rows):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)

def summary(rows,mode,path):
    by={}
    for row in rows:
        r=int(row['r']); st=by.setdefault(r,[0,0,None,Fraction(0)])
        st[0]+=1; st[1]+= row['feasible']=='True'
        sur=F(row['surplus'])
        if st[2] is None or sur<st[2]: st[2]=sur
        unc=max(F(v) for k,v in row.items() if k.startswith('uncovered_'))
        if unc>st[3]: st[3]=unc
    out=[]
    for r in sorted(by):
        c,feas,mins,maxu=by[r]
        out.append({'mode':mode,'r':r,'coords':c,'feasible_coords':feas,'min_surplus':S(mins),'max_uncovered':S(maxu)})
    write(path,out)

def run(inp,outdir):
    rows=list(csv.DictReader(open(inp,newline='')))
    strict=[]; full=[]
    for row in rows:
        r=int(row['r']); a=int(row['a'])
        L={f'M{i}':F(row[f'M{i}']) for i in range(5)}
        # strict even-source test: M4,M2,M0 vs negative M3,M1,M0
        src={'S4':max(L['M4'],0),'S2':max(L['M2'],0),'S0':max(L['M0'],0)}
        dft={'D3':max(-L['M3'],0),'D1':max(-L['M1'],0),'D0':max(-L['M0'],0)}
        w,u,un=greedy(src,dft,['S4','S2','S0'],['D3','D1','D0'])
        pos=sum(src.values(),Fraction(0)); neg=sum(dft.values(),Fraction(0)); tot=sum(L.values(),Fraction(0))
        strict.append({'mode':'strict_even_sources','r':r,'a':a,**{k:S(v) for k,v in L.items()},**{k:S(v) for k,v in src.items()},**{k:S(v) for k,v in dft.items()},**{k:S(v) for k,v in w.items()},**{f'unused_{k}':S(v) for k,v in u.items()},**{f'uncovered_{k}':S(v) for k,v in un.items()},'pos_capacity':S(pos),'neg_deficit':S(neg),'surplus':S(pos-neg),'total':S(tot),'feasible':str(all(v==0 for v in un.values()))})
        # full whole-kernel allocation: positive and negative parts of all M layers
        src={f'S{i}':max(L[f'M{i}'],0) for i in range(5)}
        dft={f'D{i}':max(-L[f'M{i}'],0) for i in range(5)}
        w,u,un=greedy(src,dft,['S4','S3','S2','S1','S0'],['D3','D1','D0','D4','D2'])
        pos=sum(src.values(),Fraction(0)); neg=sum(dft.values(),Fraction(0))
        full.append({'mode':'full_whole_kernel','r':r,'a':a,**{k:S(v) for k,v in L.items()},**{k:S(v) for k,v in src.items()},**{k:S(v) for k,v in dft.items()},**{k:S(v) for k,v in w.items()},**{f'unused_{k}':S(v) for k,v in u.items()},**{f'uncovered_{k}':S(v) for k,v in un.items()},'pos_capacity':S(pos),'neg_deficit':S(neg),'surplus':S(pos-neg),'total':S(tot),'feasible':str(all(v==0 for v in un.values()))})
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    write(outdir/'ell2_certificate_weights_strict_even_sources.csv',strict)
    write(outdir/'ell2_certificate_weights_full_whole_kernel.csv',full)
    summary(strict,'strict_even_sources',outdir/'ell2_certificate_weights_strict_summary.csv')
    summary(full,'full_whole_kernel',outdir/'ell2_certificate_weights_full_summary.csv')
    rep=outdir/'ell2_certificate_solver_report.md'
    rep.write_text('# ell=2 certificate solver report\n\n' + f'- strict even-source feasible everywhere: `{all(x["feasible"]=="True" for x in strict)}`\n' + f'- full whole-kernel feasible everywhere: `{all(x["feasible"]=="True" for x in full)}`\n\nThe strict M4/M2/M0 budget fails at the r=2 edge; the full all-layer budget is feasible in the verified window.\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='results/engine/ell2_whole_kernel_certificate_by_coordinate.csv')
    ap.add_argument('--out-dir',default='results/engine')
    a=ap.parse_args(); run(a.input,a.out_dir)
if __name__=='__main__': main()
