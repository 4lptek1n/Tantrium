#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any

def compare_manifest(manifest:dict[str,Any])->dict[str,Any]:
    reps=manifest.get('structure_reports',{})
    by_model={}; by_depth={}; by_qspan={}; shared=[]
    for rid,r in reps.items():
        model=r.get('suggested_model','unknown'); by_model.setdefault(model,[]).append(rid)
        dr=f"{r.get('depth_min')}..{r.get('depth_max')}"; by_depth.setdefault(dr,[]).append(rid)
        qr=f"{r.get('q_min')}..{r.get('q_max')}"; by_qspan.setdefault(qr,[]).append(rid)
    for name,bucket in [('model',by_model),('depth_range',by_depth),('q_range',by_qspan)]:
        for key,ids in bucket.items():
            if len(ids)>1: shared.append({'pattern':name,'value':key,'reports':ids})
    return {'structure_reports':len(reps),'by_model':by_model,'by_depth':by_depth,'by_qspan':by_qspan,'shared_patterns':shared}
def write_report(path,summary):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Comparative Atlas Report','',f"structure_reports: {summary.get('structure_reports',0)}",'','## shared patterns']
    for x in summary.get('shared_patterns',[]): lines.append(f"- {x['pattern']}={x['value']}: {', '.join(x['reports'])}")
    lines += ['','## model buckets']
    for k,v in summary.get('by_model',{}).items(): lines.append(f'- {k}: {v}')
    p.write_text('\n'.join(lines))
