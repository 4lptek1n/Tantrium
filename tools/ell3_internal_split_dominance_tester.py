#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import argparse,csv

def F(x): return Fraction(str(x).strip()) if x and str(x).strip() else Fraction(0)
def I(x): return int(str(x).strip()) if x and str(x).strip() else 0
def S(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
def qv(qd,p,y,mode):
    if mode=='two_qd': return 2*qd
    if mode=='qd': return qd
    if mode=='qd_plus_p': return qd+p
    return 2*(qd+p)
def load(fn,mode):
    a=[]
    with open(fn,newline='') as h:
        for n,r in enumerate(csv.DictReader(h),1):
            qd=I(r.get('qd_power')); p=I(r.get('qdm1_power')); y=I(r.get('Y_power')); c=F(r.get('coefficient'))
            if c: a.append({'id':n,'q':qv(qd,p,y,mode),'qd':qd,'p':p,'y':y,'df':y-p,'c':c})
    return a
def cost(s,d,model):
    q=max(0,(s['q']-d['q'])//2); df=max(0,s['df']-d['df']); p=abs(s['p']-d['p']); y=abs(s['y']-d['y']); dep=max(0,d['p']-s['p'])
    return {'unit':0,'qgap':q,'diffgap':df,'pgap':p,'qdiff':q+df,'qdiffp':q+df+p,'qdiffy':q+df+y,'ell2_depth':3*dep,'conservative':3*(q+df+p)}[model]
def run(pos,neg,model,reqdf,reqq):
    stock={x['id']:x['c'] for x in pos}; need={x['id']:-x['c'] for x in neg}; out=[]
    for d in sorted(neg,key=lambda z:(-abs(z['c']),-z['df'])):
        while need[d['id']]>0:
            cand=[]
            for s in pos:
                if stock[s['id']]<=0: continue
                if reqq and s['q']<d['q']: continue
                if reqdf and s['df']<d['df']: continue
                r=cost(s,d,model); b=Fraction(1,2**r); cap=stock[s['id']]*b
                if cap>0: cand.append((r,abs(s['df']-d['df']),abs(s['p']-d['p']),s['id'],s,b))
            if not cand: break
            r,_,_,_,s,b=sorted(cand)[0]; got=min(need[d['id']],stock[s['id']]*b); use=got/b
            stock[s['id']]-=use; need[d['id']]-=got
            out.append({'source_row':s['id'],'target_row':d['id'],'source_q':s['q'],'source_p':s['p'],'source_Y':s['y'],'source_diff':s['df'],'target_p':d['p'],'target_Y':d['y'],'target_diff':d['df'],'half_power':r,'beta':S(b),'raw_used':S(use),'delivered':S(got)})
    return out,sum(need.values(),Fraction(0)),sum(stock.values(),Fraction(0))
def wc(fn,rows,cols):
    Path(fn).parent.mkdir(parents=True,exist_ok=True)
    with open(fn,'w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=cols); w.writeheader(); w.writerows(rows)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',default='results/engine/ell3_mixed_depth_kernel.csv'); p.add_argument('--q-target',type=int,default=20); p.add_argument('--q-mode',default='two_qd'); p.add_argument('--source-policy',default='q_ge_target'); p.add_argument('--model',default='qdiff'); p.add_argument('--allow-diff-down',action='store_true'); p.add_argument('--allow-q-down',action='store_true'); p.add_argument('--report',default='results/engine/ell3_internal_split_dominance_report.md'); p.add_argument('--cover',default='results/engine/ell3_internal_split_cover.csv'); p.add_argument('--model-scan',default='results/engine/ell3_internal_split_model_scan.csv'); p.add_argument('--terms',default='results/engine/ell3_internal_split_terms.csv'); a=p.parse_args()
    z=load(a.input,a.q_mode); neg=[x for x in z if x['q']==a.q_target and x['c']<0]
    pos=[x for x in z if x['c']>0 and ((a.source_policy=='target_only' and x['q']==a.q_target) or (a.source_policy=='q_ge_target' and x['q']>=a.q_target) or (a.source_policy=='q_gt_target' and x['q']>a.q_target) or a.source_policy=='all')]
    models=['unit','qgap','diffgap','pgap','qdiff','qdiffp','qdiffy','ell2_depth','conservative']; scan=[]
    for m in models:
        tr,u,l=run(pos,neg,m,not a.allow_diff_down,not a.allow_q_down); scan.append({'model':m,'transfers':len(tr),'uncovered':S(u),'leftover':S(l),'passes':int(u==0),'max_half_power':max([int(t['half_power']) for t in tr],default=0)})
    tr,u,l=run(pos,neg,a.model,not a.allow_diff_down,not a.allow_q_down)
    wc(a.cover,tr,['source_row','target_row','source_q','source_p','source_Y','source_diff','target_p','target_Y','target_diff','half_power','beta','raw_used','delivered'])
    wc(a.model_scan,scan,['model','transfers','uncovered','leftover','passes','max_half_power'])
    wc(a.terms,[{'role':'N' if x['c']<0 else 'P','row_id':x['id'],'q':x['q'],'qd_power':x['qd'],'qdm1_power':x['p'],'Y_power':x['y'],'diff':x['df'],'coefficient':S(x['c'])} for x in neg+pos],['role','row_id','q','qd_power','qdm1_power','Y_power','diff','coefficient'])
    P=sum((x['c'] for x in pos),Fraction(0)); N=sum((-x['c'] for x in neg),Fraction(0)); lines='\n'.join([f"| {r['model']} | {r['passes']} | {r['uncovered']} | {r['leftover']} | {r['max_half_power']} |" for r in scan])
    Path(a.report).parent.mkdir(parents=True,exist_ok=True); Path(a.report).write_text(f"# ELL=3 Internal Split Report\n\nq={a.q_target}, model={a.model}, policy={a.source_policy}\n\nrows P={len(pos)}, N={len(neg)}\nP={S(P)}\nN={S(N)}\nP-N={S(P-N)}\nchosen uncovered={S(u)}\nchosen leftover={S(l)}\n\n| model | pass | uncovered | leftover | max half power |\n|---|---:|---:|---:|---:|\n{lines}\n")
    print(f'rows P={len(pos)} N={len(neg)} uncovered={S(u)} leftover={S(l)}')
if __name__=='__main__': main()
