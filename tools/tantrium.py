#!/usr/bin/env python3
"""Tantrium Proof Foundry v1 command line entrypoint."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from tantrium.atlas.atlas_db import AtlasDB
from tantrium.certificates.certificate import Cell
from tantrium.discovery.structure_miner import mine, write_report
from tantrium.theorem_graph.state_machine import default_graph, write_default_graph
from tantrium.transport.dyadic_flow import FlowPolicy, solve_greedy


def q_value(qd: int, p: int, mode: str) -> int:
    if mode == "two_qd": return 2 * qd
    if mode == "qd": return qd
    if mode == "qd_plus_p": return qd + p
    if mode == "two_qd_plus_p": return 2 * (qd + p)
    raise ValueError(mode)

def count_rows(path: Path) -> int:
    if not path.exists(): return 0
    with path.open(newline='') as h:
        return max(0, sum(1 for _ in h) - 1)

def load_mixed_depth(path: Path, q_target: int, q_mode: str, source_policy: str) -> tuple[list[Cell], list[Cell]]:
    sources=[]; deficits=[]
    with path.open(newline='') as handle:
        for idx,row in enumerate(csv.DictReader(handle),start=1):
            qd=int(row.get('qd_power',0)); p=int(row.get('qdm1_power',0)); y=int(row.get('Y_power',0)); diff=y-p; q=q_value(qd,p,q_mode); coeff=Fraction(row.get('coefficient','0')); cid=f'row_{idx}'
            if coeff < 0 and q == q_target:
                deficits.append(Cell.make(cid,-coeff,q=q,qd=qd,p=p,Y=y,diff=diff))
            elif coeff > 0:
                ok=(source_policy=='all' or (source_policy=='target_only' and q==q_target) or (source_policy=='q_ge_target' and q>=q_target) or (source_policy=='q_gt_target' and q>q_target))
                if ok: sources.append(Cell.make(cid,coeff,q=q,qd=qd,p=p,Y=y,diff=diff))
    return sources,deficits

def mixed_q_values(path: Path, q_mode: str) -> list[int]:
    vals=set()
    if not path.exists(): return []
    with path.open(newline='') as h:
        for r in csv.DictReader(h):
            vals.add(q_value(int(r.get('qd_power',0)),int(r.get('qdm1_power',0)),q_mode))
    return sorted(vals)

def run_cmd(cmd: list[str]) -> None:
    print('$ '+' '.join(cmd)); subprocess.run(cmd,check=True)

def cmd_graph(args):
    path=write_default_graph(args.output)
    if args.status=='all': print(default_graph().markdown())
    else: print(f'wrote {path}')

def cmd_status(args):
    graph_path=write_default_graph(args.graph_output)
    atlas=AtlasDB(args.atlas_root)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(default_graph().markdown()+"\n\n"+atlas.status_table())
    print(f'wrote {graph_path} and {out}')

def cmd_build_kernel(args):
    ell=args.ell
    if ell==3:
        run_cmd([sys.executable,'tools/ell3_cumulant_kernel_generator.py'])
        run_cmd([sys.executable,'tools/ell3_rj_specialized_kernel.py'])
        run_cmd([sys.executable,'tools/ell3_qd_reducer.py'])
        run_cmd([sys.executable,'tools/ell3_delta_transform.py'])
        mixed=Path('results/engine/ell3_mixed_depth_kernel.csv')
    else:
        sk=Path(f'results/engine/ell{ell}_cumulant_kernel_terms.csv')
        if not sk.exists():
            run_cmd([sys.executable,'tools/uniform_lift_lemma_tester.py','--ell',str(ell),'--skeleton',str(sk),'--report',f'results/engine/ell{ell}_build_probe.md'])
        mixed=Path(f'results/engine/ell{ell}_mixed_depth_kernel.csv')
        if not mixed.exists():
            print(f'missing {mixed}; kernel skeleton/probe generated, full generic builder still needs ell{ell} atom/Rj pipeline')
    atlas=AtlasDB(args.atlas_root)
    for kind in ['cumulant_kernel_terms','kernel_Rj_specialized','kernel_qd','mixed_depth_kernel']:
        p=Path(f'results/engine/ell{ell}_{kind}.csv')
        if p.exists(): atlas.register_kernel(f'ell{ell}_{kind}',str(p),ell=ell,kind=kind,rows=count_rows(p))
    if mixed.exists():
        summary=mine(mixed,args.q_mode); report=Path(f'results/engine/ell{ell}_structure_miner_report.md'); write_report(report,summary); atlas.register_structure_report(f'ell{ell}_structure',f'ell{ell}_mixed_depth',str(report),summary)
        print(f'wrote {report}')

def certify_one(input_path: Path, q_target: int, q_mode: str, source_policy: str, model: str, theorem_id: str, kernel_id: str, output: Path, atlas_root: str, allow_q_down=False, allow_diff_down=False):
    sources,deficits=load_mixed_depth(input_path,q_target,q_mode,source_policy)
    policy=FlowPolicy(theorem_id=theorem_id,kernel_id=kernel_id,map_name=model,require_q_ge=not allow_q_down,require_diff_ge=not allow_diff_down)
    cert=solve_greedy(sources,deficits,policy)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(cert.markdown())
    atlas=AtlasDB(atlas_root); atlas.register_certificate(theorem_id,cert.summary(),str(output),q_target=q_target,model=model)
    ok,errs=cert.verify()
    if not ok:
        missing=cert.uncovered_deficits(); mass=sum(missing.values(),Fraction(0)); atlas.register_obstruction(f'{theorem_id}_obstruction',theorem_id,kernel_id,str(mass),{'q_target':q_target,'model':model,'missing_targets':{k:str(v) for k,v in missing.items()}})
    return cert

def cmd_certify(args):
    if args.scan=='all': return cmd_scan(args)
    cert=certify_one(Path(args.input),args.q_target,args.q_mode,args.source_policy,args.model,args.theorem_id,args.kernel_id,Path(args.output),args.atlas_root,args.allow_q_down,args.allow_diff_down)
    print(cert.markdown())

def cmd_scan(args):
    atlas=AtlasDB(args.atlas_root); rows=[]; first_fail=None
    for ell in range(1,args.max_ell+1):
        mixed=Path(args.input or f'results/engine/ell{ell}_mixed_depth_kernel.csv')
        if not mixed.exists():
            rows.append({'ell':ell,'q':'','status':'missing_kernel','details':str(mixed)}); continue
        atlas.register_kernel(f'ell{ell}_mixed_depth',str(mixed),ell=ell,kind='mixed_depth',rows=count_rows(mixed))
        summary=mine(mixed,args.q_mode); rep=Path(f'results/engine/ell{ell}_structure_miner_report.md'); write_report(rep,summary); atlas.register_structure_report(f'ell{ell}_structure',f'ell{ell}_mixed_depth',str(rep),summary)
        for q in mixed_q_values(mixed,args.q_mode):
            out=Path(f'results/certificates/ell{ell}_q{q}_{args.model}.md')
            theorem_id=f'ell{ell}_q{q}_{args.model}'
            cert=certify_one(mixed,q,args.q_mode,args.source_policy,args.model,theorem_id,f'ell{ell}_mixed_depth',out,args.atlas_root,args.allow_q_down,args.allow_diff_down)
            ok,errs=cert.verify(); rows.append({'ell':ell,'q':q,'status':'pass' if ok else 'fail','details':'; '.join(errs[:3])})
            if not ok and first_fail is None: first_fail=(ell,q,errs)
    report=Path(args.report); report.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Tantrium scan-all report','']+[f"- ell={r['ell']} q={r['q']} status={r['status']} {r['details']}" for r in rows]
    if first_fail: lines.append(f"\nFirst obstruction: ell={first_fail[0]} q={first_fail[1]} errors={first_fail[2]}")
    else: lines.append('\nNo obstruction found in scanned kernels.')
    report.write_text('\n'.join(lines)); print(f'wrote {report}')

def main():
    parser=argparse.ArgumentParser(description='Tantrium Proof Foundry v1'); sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('graph'); p.add_argument('--status',default='write',choices=['write','all']); p.add_argument('--output',default='docs/THEOREM_GRAPH.md'); p.set_defaults(func=cmd_graph)
    p=sub.add_parser('status'); p.add_argument('--update',action='store_true'); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--graph-output',default='docs/THEOREM_GRAPH.md'); p.add_argument('--output',default='results/atlas/status.md'); p.set_defaults(func=cmd_status)
    p=sub.add_parser('build-kernel'); p.add_argument('--ell',type=int,required=True); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--q-mode',default='two_qd'); p.set_defaults(func=cmd_build_kernel)
    p=sub.add_parser('certify'); p.add_argument('--input'); p.add_argument('--scan',default='one',choices=['one','all']); p.add_argument('--max-ell',type=int,default=4); p.add_argument('--q-target',type=int,default=20); p.add_argument('--q-mode',default='two_qd',choices=['two_qd','qd','qd_plus_p','two_qd_plus_p']); p.add_argument('--source-policy',default='q_ge_target',choices=['all','target_only','q_ge_target','q_gt_target']); p.add_argument('--model',default='qdiff',choices=['unit','qgap','diffgap','qdiff','qdiffp','ell2_depth','conservative']); p.add_argument('--allow-q-down',action='store_true'); p.add_argument('--allow-diff-down',action='store_true'); p.add_argument('--theorem-id',default='manual_certificate'); p.add_argument('--kernel-id',default='mixed_depth_kernel'); p.add_argument('--output',default='results/certificates/manual_certificate.md'); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--report',default='results/certificates/scan_all_report.md'); p.set_defaults(func=cmd_certify)
    args=parser.parse_args(); args.func(args)
if __name__=='__main__': main()
