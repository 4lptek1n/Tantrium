#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from collections import Counter,defaultdict
from fractions import Fraction
from math import factorial
from pathlib import Path

def F(x): return Fraction(0) if x is None or str(x).strip()=='' else Fraction(str(x).strip())
def I(x): return 0 if x is None or str(x).strip()=='' else int(str(x).strip())
def S(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
def parts(n,m=None):
    if m is None or m>n: m=n
    if n==0: yield []; return
    for a in range(m,0,-1):
        for r in parts(n-a,min(a,n-a) if n-a else 0): yield [a]+r
def sym(p):
    c=Counter(p); d=1
    for v in c.values(): d*=factorial(v)
    return Fraction(1,d)
def qv(qd,p,y,mode):
    if mode=='two_qd': return 2*qd
    if mode=='qd': return qd
    if mode=='qd_plus_p': return qd+p
    return 2*(qd+p)
def load_mixed(fn,mode):
    out=[]
    with Path(fn).open(newline='') as h:
        for n,r in enumerate(csv.DictReader(h),1):
            qd=I(r.get('qd_power')); p=I(r.get('qdm1_power')); y=I(r.get('Y_power')); c=F(r.get('coefficient'))
            if c: out.append({'id':n,'q':qv(qd,p,y,mode),'qd':qd,'p':p,'y':y,'diff':y-p,'c':c})
    return out
def cost(s,d,model,ell):
    q=max(0,(s['q']-d['q'])//2); df=max(0,s['diff']-d['diff']); p=abs(s['p']-d['p']); dep=max(0,d['p']-s['p'])
    if model=='unit': return 0
    if model=='qgap': return q
    if model=='diffgap': return df
    if model=='qdiff': return q+df
    if model=='depth': return ell*dep
    if model=='dyadic_ell': return ell*(q+df+p)
    return 3*(q+df+p)
def cover(pos,neg,model,ell,reqq=True,reqdiff=True):
    stock={x['id']:x['c'] for x in pos}; need={x['id']:-x['c'] for x in neg}; edges=[]
    for d in sorted(neg,key=lambda z:(-abs(z['c']),-z['diff'],z['p'])):
        while need[d['id']]>0:
            cand=[]
            for s in pos:
                if stock[s['id']]<=0: continue
                if reqq and s['q']<d['q']: continue
                if reqdiff and s['diff']<d['diff']: continue
                r=cost(s,d,model,ell); b=Fraction(1,2**r); cap=stock[s['id']]*b
                if cap>0: cand.append((r,abs(s['diff']-d['diff']),abs(s['p']-d['p']),s['id'],s,b))
            if not cand: break
            r,_,_,_,s,b=sorted(cand)[0]
            got=min(need[d['id']],stock[s['id']]*b); raw=got/b
            stock[s['id']]-=raw; need[d['id']]-=got
            edges.append({'source_row':s['id'],'target_row':d['id'],'source_q':s['q'],'source_p':s['p'],'source_Y':s['y'],'source_diff':s['diff'],'target_q':d['q'],'target_p':d['p'],'target_Y':d['y'],'target_diff':d['diff'],'half_power':r,'beta':S(b),'raw_used':S(raw),'delivered':S(got)})
    return edges,sum(need.values(),Fraction(0)),sum(stock.values(),Fraction(0))
def wc(fn,rows,fields):
    Path(fn).parent.mkdir(parents=True,exist_ok=True)
    with Path(fn).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)
def atom_coverage(atom_map,total):
    if not atom_map or not Path(atom_map).exists(): return [],list(range(1,total+1))
    seen=set()
    with Path(atom_map).open(newline='') as h:
        for r in csv.DictReader(h): seen.add(I(r.get('s')))
    miss=[s for s in range(1,total+1) if s not in seen]
    return sorted(seen),miss
def write_skeleton(fn,ell):
    total=2*ell; rows=[]
    for i,p in enumerate(parts(total),1):
        pp=sorted(p); rows.append({'term_id':i,'ell':ell,'total_weight':total,'num_atoms':len(pp),'partition':'+'.join(map(str,pp)),'coefficient':S(sym(pp))})
    wc(fn,rows,['term_id','ell','total_weight','num_atoms','partition','coefficient']); return rows
def main():
    ap=argparse.ArgumentParser(description='Probe the Uniform Lift Lemma by mixed-depth dyadic transport covers.')
    ap.add_argument('--ell',type=int,default=4); ap.add_argument('--input',default=''); ap.add_argument('--q-target',type=int,default=20); ap.add_argument('--q-mode',default='two_qd'); ap.add_argument('--source-policy',default='q_ge_target'); ap.add_argument('--model',default='qdiff'); ap.add_argument('--atom-map',default='results/engine/ell_atom_to_Rj_map.csv'); ap.add_argument('--report',default='results/engine/uniform_lift_lemma_report.md'); ap.add_argument('--cover',default='results/engine/uniform_lift_lemma_cover.csv'); ap.add_argument('--model-scan',default='results/engine/uniform_lift_lemma_model_scan.csv'); ap.add_argument('--skeleton',default='results/engine/uniform_lift_lemma_skeleton.csv'); a=ap.parse_args()
    total=2*a.ell; sk=write_skeleton(a.skeleton,a.ell); seen,miss=atom_coverage(a.atom_map,total)
    inp=a.input or f'results/engine/ell{a.ell}_mixed_depth_kernel.csv'
    lines=[]; status='probe_only'
    lines.append(f'# Uniform Lift Lemma Tester Report\n')
    lines.append(f'ell = {a.ell}, total cumulant weight = {total}\n')
    lines.append(f'skeleton terms = {len(sk)}\n')
    lines.append(f'atom map covered s = {seen}\n')
    lines.append(f'atom map missing s = {miss}\n')
    if not Path(inp).exists():
        status='missing_mixed_depth_input'
        lines.append(f'\nNo mixed-depth input found at `{inp}`.\n')
        lines.append('This is the first obstruction for this ell: generate atom reductions through total weight and run the Rj -> qd -> mixed-depth pipeline.\n')
        lines.append(f'Wrote skeleton to `{a.skeleton}`.\n')
        Path(a.report).parent.mkdir(parents=True,exist_ok=True); Path(a.report).write_text('\n'.join(lines)); print(status); return
    z=load_mixed(inp,a.q_mode)
    neg=[x for x in z if x['q']==a.q_target and x['c']<0]
    if a.source_policy=='target_only': pos=[x for x in z if x['c']>0 and x['q']==a.q_target]
    elif a.source_policy=='q_gt_target': pos=[x for x in z if x['c']>0 and x['q']>a.q_target]
    elif a.source_policy=='all': pos=[x for x in z if x['c']>0]
    else: pos=[x for x in z if x['c']>0 and x['q']>=a.q_target]
    models=['unit','qgap','diffgap','qdiff','depth','dyadic_ell','conservative']; scans=[]
    for m in models:
        ed,u,l=cover(pos,neg,m,a.ell); scans.append({'model':m,'edges':len(ed),'uncovered':S(u),'leftover':S(l),'passes':int(u==0),'max_half_power':max([int(e['half_power']) for e in ed],default=0)})
    ed,u,l=cover(pos,neg,a.model,a.ell)
    wc(a.cover,ed,['source_row','target_row','source_q','source_p','source_Y','source_diff','target_q','target_p','target_Y','target_diff','half_power','beta','raw_used','delivered'])
    wc(a.model_scan,scans,['model','edges','uncovered','leftover','passes','max_half_power'])
    P=sum((x['c'] for x in pos),Fraction(0)); N=sum((-x['c'] for x in neg),Fraction(0))
    lines.append(f'\nInput = `{inp}`\n')
    lines.append(f'q_target = {a.q_target}, q_mode = {a.q_mode}, source_policy = {a.source_policy}\n')
    lines.append(f'positive source rows = {len(pos)}, negative target rows = {len(neg)}\n')
    lines.append(f'total source mass = {S(P)}\n')
    lines.append(f'total target deficit = {S(N)}\n')
    lines.append(f'chosen model = {a.model}\n')
    lines.append(f'uncovered deficit = {S(u)}\n')
    lines.append(f'leftover source = {S(l)}\n')
    lines.append('\n## Model scan\n\n| model | pass | uncovered | leftover | max half power |\n|---|---:|---:|---:|---:|')
    for r in scans: lines.append(f"| {r['model']} | {r['passes']} | {r['uncovered']} | {r['leftover']} | {r['max_half_power']} |")
    if u==0: lines.append('\nResult: candidate cover found for this finite target. This is evidence for the Uniform Lift Lemma at this coordinate, not a global proof.\n')
    else: lines.append('\nResult: obstruction found at this coordinate. Inspect the cover and model scan files.\n')
    Path(a.report).parent.mkdir(parents=True,exist_ok=True); Path(a.report).write_text('\n'.join(lines))
    print(f'wrote {a.report}; uncovered={S(u)}')
if __name__=='__main__': main()
