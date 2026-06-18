#!/usr/bin/env python3
from __future__ import annotations
import csv
from fractions import Fraction
from pathlib import Path

def qv(qd,p,mode='two_qd'):
    if mode=='two_qd': return 2*qd
    if mode=='qd': return qd
    if mode=='qd_plus_p': return qd+p
    return 2*(qd+p)
def load(path,mode='two_qd'):
    out=[]
    with Path(path).open(newline='') as h:
        for r in csv.DictReader(h):
            qd=int(r.get('qd_power',0)); p=int(r.get('qdm1_power',0)); y=int(r.get('Y_power',0)); c=Fraction(r.get('coefficient','0'))
            if c: out.append({'qd':qd,'p':p,'y':y,'q':qv(qd,p,mode),'diff':y-p,'c':c})
    return out
def mine(path,q_mode='two_qd'):
    z=load(path,q_mode)
    if not z: return {'path':str(path),'terms':0,'suggested_model':'none'}
    qs=sorted({x['q'] for x in z}); dif=[x['diff'] for x in z]; dep=[x['p'] for x in z]
    mp={(x['qd'],x['p'],x['y']):x['c'] for x in z}; opp=0; exact=0
    for x in z:
        h=(x['qd']+1,x['p']+1,x['y']+1); hc=mp.get(h)
        if hc is not None and x['c']*hc<0:
            opp+=1; exact+=int(abs(hc)==abs(x['c']))
    byq={}
    for q in qs:
        a=[x for x in z if x['q']==q]
        byq[str(q)]={'terms':len(a),'positive':sum(x['c']>0 for x in a),'negative':sum(x['c']<0 for x in a),'diff_min':min(x['diff'] for x in a),'diff_max':max(x['diff'] for x in a)}
    return {'path':str(path),'terms':len(z),'positive_terms':sum(x['c']>0 for x in z),'negative_terms':sum(x['c']<0 for x in z),'q_min':min(qs),'q_max':max(qs),'q_values':qs,'diff_min':min(dif),'diff_max':max(dif),'depth_min':min(dep),'depth_max':max(dep),'opposite_shift_candidates':opp,'exact_shift_pairs':exact,'suggested_model':'qdiff' if opp or any(x['c']<0 for x in z) else 'unit','by_q':byq}
def write_report(path,summary):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    lines=['# Structure Miner Report','']
    for k,v in summary.items():
        if k!='by_q': lines.append(f'- {k}: {v}')
    lines.append(''); lines.append('## q families')
    for q,r in summary.get('by_q',{}).items(): lines.append(f'- q={q}: {r}')
    Path(path).write_text('\n'.join(lines))
