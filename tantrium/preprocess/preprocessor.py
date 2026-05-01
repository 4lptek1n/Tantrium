#!/usr/bin/env python3
from __future__ import annotations
import csv
from fractions import Fraction
from pathlib import Path

def fs(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
def pick(r,*names,default='0'):
    for n in names:
        if n in r and r[n] not in (None,''): return r[n]
    return default
def preprocess_csv(input_path,output_path):
    inp=Path(input_path); out=Path(output_path); out.parent.mkdir(parents=True,exist_ok=True); rows=[]
    with inp.open(newline='') as h:
        for i,r in enumerate(csv.DictReader(h),1):
            c=Fraction(pick(r,'coefficient','coeff','c','mass'))
            qd=int(pick(r,'qd_power','qd',default=pick(r,'q',default='0')))
            p=int(pick(r,'qdm1_power','p','depth',default='0'))
            y=int(pick(r,'Y_power','y_power','Y',default=pick(r,'diff',default='0')))
            rows.append({'qd_power':qd,'qdm1_power':p,'Y_power':y,'coefficient':fs(c),'sign':'+' if c>0 else '-' if c<0 else '0','source_row':i})
    with out.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=['qd_power','qdm1_power','Y_power','coefficient','sign','source_row']); w.writeheader(); w.writerows(rows)
    return {'input':str(inp),'output':str(out),'rows':len(rows)}
