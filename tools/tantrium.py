#!/usr/bin/env python3
"""Tantrium Proof Foundry v1.2 command line entrypoint."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from tantrium.atlas.atlas_db import AtlasDB
from tantrium.atlas.comparative import compare_manifest, write_report as write_compare_report
from tantrium.certificates.certificate import Cell
from tantrium.discovery.structure_miner import mine, write_report
from tantrium.preprocess.preprocessor import preprocess_csv
from tantrium.theorem_graph.graph_store import GraphStore
from tantrium.transport.dyadic_flow import FlowPolicy, solve_greedy


def q_value(qd: int, p: int, mode: str) -> int:
    if mode == "two_qd": return 2 * qd
    if mode == "qd": return qd
    if mode == "qd_plus_p": return qd + p
    if mode == "two_qd_plus_p": return 2 * (qd + p)
    raise ValueError(mode)

def count_rows(path: Path) -> int:
    if not path.exists(): return 0
    with path.open(newline='') as h: return max(0, sum(1 for _ in h)-1)

def load_mixed_depth(path: Path, q_target: int, q_mode: str, source_policy: str):
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

def mixed_q_values(path: Path, q_mode: str):
    vals=set()
    if not path.exists(): return []
    with path.open(newline='') as h:
        for r in csv.DictReader(h): vals.add(q_value(int(r.get('qd_power',0)),int(r.get('qdm1_power',0)),q_mode))
    return sorted(vals)

def run_cmd(cmd):
    print('$ '+' '.join(cmd)); subprocess.run(cmd,check=True)

def register_kernel_artifacts(ell:int, atlas:AtlasDB):
    for kind in ['cumulant_kernel_terms','kernel_Rj_specialized','kernel_qd','mixed_depth_kernel','mixed_depth_summary','delta_seed_decomposition']:
        p=Path(f'results/engine/ell{ell}_{kind}.csv')
        if p.exists(): atlas.register_kernel(f'ell{ell}_{kind}',str(p),ell=ell,kind=kind,rows=count_rows(p))

def run_structure_miner(ell:int, mixed:Path, atlas:AtlasDB, q_mode:str):
    if not mixed.exists(): return
    summary=mine(mixed,q_mode); report=Path(f'results/engine/ell{ell}_structure_miner_report.md')
    write_report(report,summary); atlas.register_structure_report(f'ell{ell}_structure',f'ell{ell}_mixed_depth',str(report),summary)
    print(f'wrote {report}')

def cmd_graph(args):
    store=GraphStore(args.graph_store); graph=store.load(); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(graph.markdown())
    if args.status=='all': print(graph.markdown())
    else: print(f'wrote {out}')

def cmd_status(args):
    atlas=AtlasDB(args.atlas_root); store=GraphStore(args.graph_store)
    graph=store.update_from_atlas(atlas.manifest()) if args.update else store.load()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(graph.markdown()+"\n\n"+atlas.status_table())
    Path(args.graph_output).parent.mkdir(parents=True,exist_ok=True); Path(args.graph_output).write_text(graph.markdown())
    print(f'wrote {args.graph_output} and {out}')

def cmd_build_kernel(args):
    ell=args.ell; atlas=AtlasDB(args.atlas_root)
    cmd=[sys.executable,'tools/build_kernel.py','--ell',str(ell)]
    if args.skip_auto_atom_map: cmd.append('--skip-auto-atom-map')
    if args.atom_map: cmd += ['--atom-map',args.atom_map]
    run_cmd(cmd); register_kernel_artifacts(ell,atlas); run_structure_miner(ell,Path(f'results/engine/ell{ell}_mixed_depth_kernel.csv'),atlas,args.q_mode)

def certify_one(input_path:Path,q_target:int,q_mode:str,source_policy:str,model:str,theorem_id:str,kernel_id:str,output:Path,atlas_root:str,graph_store:str,allow_q_down=False,allow_diff_down=False):
    sources,deficits=load_mixed_depth(input_path,q_target,q_mode,source_policy)
    policy=FlowPolicy(theorem_id=theorem_id,kernel_id=kernel_id,map_name=model,require_q_ge=not allow_q_down,require_diff_ge=not allow_diff_down)
    cert=solve_greedy(sources,deficits,policy); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(cert.markdown())
    atlas=AtlasDB(atlas_root); atlas.register_certificate(theorem_id,cert.summary(),str(output),q_target=q_target,model=model)
    ok,_=cert.verify()
    if not ok:
        missing=cert.uncovered_deficits(); mass=sum(missing.values(),Fraction(0)); coords={'q_target':q_target,'model':model,'missing_targets':{k:str(v) for k,v in missing.items()}}
        obs_id=f'{theorem_id}_obstruction'; atlas.register_obstruction(obs_id,theorem_id,kernel_id,str(mass),coords); GraphStore(graph_store).add_obstruction(obs_id,f'Obstruction for {theorem_id}',artifacts=[str(output)],note=str(coords))
    else:
        GraphStore(graph_store).update_from_atlas(atlas.manifest())
    return cert

def cmd_certify(args):
    if args.scan=='all': return cmd_scan(args)
    if not args.input: raise SystemExit('--input is required unless --scan all')
    cert=certify_one(Path(args.input),args.q_target,args.q_mode,args.source_policy,args.model,args.theorem_id,args.kernel_id,Path(args.output),args.atlas_root,args.graph_store,args.allow_q_down,args.allow_diff_down)
    print(cert.markdown())

def ensure_kernel(ell:int,args):
    mixed=Path(f'results/engine/ell{ell}_mixed_depth_kernel.csv')
    if mixed.exists() or not args.build_missing: return mixed
    try: run_cmd([sys.executable,'tools/build_kernel.py','--ell',str(ell)])
    except Exception as exc: print(f'build failed for ell={ell}: {exc}')
    return mixed

def cmd_scan(args):
    atlas=AtlasDB(args.atlas_root); rows=[]; first_fail=None
    for ell in range(1,args.max_ell+1):
        mixed=Path(args.input) if args.input else ensure_kernel(ell,args)
        if not mixed.exists(): rows.append({'ell':ell,'q':'','status':'missing_kernel','details':str(mixed)}); continue
        atlas.register_kernel(f'ell{ell}_mixed_depth',str(mixed),ell=ell,kind='mixed_depth',rows=count_rows(mixed)); run_structure_miner(ell,mixed,atlas,args.q_mode)
        for q in mixed_q_values(mixed,args.q_mode):
            out=Path(f'results/certificates/ell{ell}_q{q}_{args.model}.md'); theorem_id=f'ell{ell}_q{q}_{args.model}'
            cert=certify_one(mixed,q,args.q_mode,args.source_policy,args.model,theorem_id,f'ell{ell}_mixed_depth',out,args.atlas_root,args.graph_store,args.allow_q_down,args.allow_diff_down)
            ok,errs=cert.verify(); rows.append({'ell':ell,'q':q,'status':'pass' if ok else 'fail','details':'; '.join(errs[:3])})
            if not ok and first_fail is None: first_fail=(ell,q,errs)
    report=Path(args.report); report.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Tantrium scan-all report','']+[f"- ell={r['ell']} q={r['q']} status={r['status']} {r['details']}" for r in rows]
    lines.append(f"\nFirst obstruction: ell={first_fail[0]} q={first_fail[1]} errors={first_fail[2]}" if first_fail else '\nNo obstruction found in scanned kernels.')
    report.write_text('\n'.join(lines)); print(f'wrote {report}')

def cmd_preprocess(args):
    rec=preprocess_csv(args.input,args.output); atlas=AtlasDB(args.atlas_root); atlas.register_kernel(args.kernel_id,args.output,ell=args.ell,kind='external_preprocessed',rows=rec['rows']); print(rec)

def cmd_compare_atlas(args):
    atlas=AtlasDB(args.atlas_root); summary=compare_manifest(atlas.manifest()); write_compare_report(args.output,summary); print(f'wrote {args.output}')

def main():
    parser=argparse.ArgumentParser(description='Tantrium Proof Foundry v1.2'); sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('graph'); p.add_argument('--status',default='write',choices=['write','all']); p.add_argument('--output',default='docs/THEOREM_GRAPH.md'); p.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); p.set_defaults(func=cmd_graph)
    p=sub.add_parser('status'); p.add_argument('--update',action='store_true'); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); p.add_argument('--graph-output',default='docs/THEOREM_GRAPH.md'); p.add_argument('--output',default='results/atlas/status.md'); p.set_defaults(func=cmd_status)
    p=sub.add_parser('build-kernel'); p.add_argument('--ell',type=int,required=True); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--q-mode',default='two_qd'); p.add_argument('--atom-map',default=''); p.add_argument('--skip-auto-atom-map',action='store_true'); p.set_defaults(func=cmd_build_kernel)
    p=sub.add_parser('certify'); p.add_argument('--input'); p.add_argument('--scan',default='one',choices=['one','all']); p.add_argument('--max-ell',type=int,default=4); p.add_argument('--build-missing',action='store_true',default=True); p.add_argument('--q-target',type=int,default=20); p.add_argument('--q-mode',default='two_qd',choices=['two_qd','qd','qd_plus_p','two_qd_plus_p']); p.add_argument('--source-policy',default='q_ge_target',choices=['all','target_only','q_ge_target','q_gt_target']); p.add_argument('--model',default='qdiff',choices=['unit','qgap','diffgap','qdiff','qdiffp','ell2_depth','conservative']); p.add_argument('--allow-q-down',action='store_true'); p.add_argument('--allow-diff-down',action='store_true'); p.add_argument('--theorem-id',default='manual_certificate'); p.add_argument('--kernel-id',default='mixed_depth_kernel'); p.add_argument('--output',default='results/certificates/manual_certificate.md'); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); p.add_argument('--report',default='results/certificates/scan_all_report.md'); p.set_defaults(func=cmd_certify)
    p=sub.add_parser('preprocess'); p.add_argument('--input',required=True); p.add_argument('--output',required=True); p.add_argument('--kernel-id',default='external_kernel'); p.add_argument('--ell',type=int); p.add_argument('--atlas-root',default='results/atlas'); p.set_defaults(func=cmd_preprocess)
    p=sub.add_parser('compare-atlas'); p.add_argument('--atlas-root',default='results/atlas'); p.add_argument('--output',default='results/atlas/comparative_report.md'); p.set_defaults(func=cmd_compare_atlas)
    args=parser.parse_args(); args.func(args)
if __name__=='__main__': main()
