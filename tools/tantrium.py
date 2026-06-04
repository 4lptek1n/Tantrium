#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re,subprocess,sys
from fractions import Fraction
from pathlib import Path
from tantrium.atlas.atlas_db import AtlasDB
from tantrium.atlas.comparative import compare_manifest, write_report as write_compare_report
from tantrium.certificates.certificate import Cell
from tantrium.discovery.structure_miner import mine, write_report
from tantrium.preprocess.preprocessor import preprocess_csv
from tantrium.theorem_graph.graph_store import GraphStore
from tantrium.transport.dyadic_flow import FlowPolicy, solve_greedy
from tantrium.transport.model_dispatch import solve_auto_greedy, auto_select_model, source_policy_for_model

def q_value(qd,p,mode):
    return {'two_qd':2*qd,'qd':qd,'qd_plus_p':qd+p,'two_qd_plus_p':2*(qd+p)}[mode]
def count_rows(path):
    p=Path(path)
    if not p.exists(): return 0
    with p.open(newline='') as h: return max(0,sum(1 for _ in h)-1)
def mixed_q_values(path,q_mode):
    vals=set(); p=Path(path)
    if not p.exists(): return []
    with p.open(newline='') as h:
        for r in csv.DictReader(h): vals.add(q_value(int(r.get('qd_power',0)),int(r.get('qdm1_power',0)),q_mode))
    return sorted(vals)
def load_mixed_depth(path,q_target,q_mode,source_policy):
    sources=[]; deficits=[]
    with Path(path).open(newline='') as h:
        for idx,r in enumerate(csv.DictReader(h),1):
            qd=int(r.get('qd_power',0)); p=int(r.get('qdm1_power',0)); y=int(r.get('Y_power',0)); c=Fraction(r.get('coefficient','0')); q=q_value(qd,p,q_mode); diff=y-p; cid=f'row_{idx}'
            if c<0 and q==q_target: deficits.append(Cell.make(cid,-c,q=q,qd=qd,p=p,Y=y,diff=diff))
            elif c>0:
                ok=source_policy=='all' or (source_policy=='target_only' and q==q_target) or (source_policy=='q_ge_target' and q>=q_target) or (source_policy=='q_gt_target' and q>q_target)
                if ok: sources.append(Cell.make(cid,c,q=q,qd=qd,p=p,Y=y,diff=diff))
    return sources,deficits
def run_cmd(cmd): print('$ '+' '.join(cmd)); subprocess.run(cmd,check=True)
def register_kernel_artifacts(ell,atlas):
    for kind in ['cumulant_kernel_terms','kernel_Rj_specialized','kernel_qd','mixed_depth_kernel','mixed_depth_summary','delta_seed_decomposition']:
        p=Path(f'results/engine/ell{ell}_{kind}.csv')
        if p.exists(): atlas.register_kernel(f'ell{ell}_{kind}',str(p),ell=ell,kind=kind,rows=count_rows(p))
def run_structure_miner(ell,mixed,atlas,q_mode):
    p=Path(mixed)
    if not p.exists(): return
    summary=mine(p,q_mode); report=Path(f'results/engine/ell{ell}_structure_miner_report.md')
    write_report(report,summary); atlas.register_structure_report(f'ell{ell}_structure',f'ell{ell}_mixed_depth',str(report),summary)
def extract_ell(path):
    m=re.search(r'ell(\d+)',Path(path).name); return int(m.group(1)) if m else 0
def selected_policy(ell,q,max_q,model,default_policy):
    if model!='auto' or default_policy!='q_ge_target': return model,default_policy
    selected=auto_select_model(ell,q,max_q=max_q)
    return selected,source_policy_for_model(selected)
def certify_one(input_path,q_target,q_mode,source_policy,model,theorem_id,kernel_id,output,atlas_root,graph_store,allow_q_down=False,allow_diff_down=False,ell=0,max_q=None):
    ell=ell or extract_ell(input_path); selected,policy_name=selected_policy(ell,q_target,max_q,model,source_policy)
    sources,defs=load_mixed_depth(input_path,q_target,q_mode,policy_name)
    if model=='auto' or selected in {'split_pair','diagonal_residue','q6_low_family','low_q_family','boundary_family'}:
        cert=solve_auto_greedy(sources,defs,ell=ell,q_target=q_target,theorem_id=theorem_id,kernel_id=kernel_id,model=selected,max_q=max_q)
    else:
        policy=FlowPolicy(theorem_id=theorem_id,kernel_id=kernel_id,map_name=selected,require_q_ge=not allow_q_down,require_diff_ge=not allow_diff_down)
        cert=solve_greedy(sources,defs,policy)
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(cert.markdown()+f'\n\nSelected model: `{selected}`\nSource policy: `{policy_name}`\n')
    atlas=AtlasDB(atlas_root); atlas.register_certificate(theorem_id,cert.summary(),str(out),q_target=q_target,model=selected)
    ok,_=cert.verify()
    if not ok:
        missing=cert.uncovered_deficits(); coords={'ell':ell,'q_target':q_target,'model':selected,'source_policy':policy_name,'missing_targets':{k:str(v) for k,v in missing.items()}}
        atlas.register_obstruction(f'{theorem_id}_obstruction',theorem_id,kernel_id,str(sum(missing.values(),Fraction(0))),coords)
        GraphStore(graph_store).add_obstruction(f'{theorem_id}_obstruction',f'Obstruction for {theorem_id}',artifacts=[str(out)],note=str(coords))
    else: GraphStore(graph_store).update_from_atlas(atlas.manifest())
    return cert,selected,policy_name
def cmd_graph(args):
    g=GraphStore(args.graph_store).load(); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(g.markdown()); print(g.markdown() if args.status=='all' else f'wrote {out}')
def cmd_status(args):
    atlas=AtlasDB(args.atlas_root); store=GraphStore(args.graph_store); g=store.update_from_atlas(atlas.manifest()) if args.update else store.load()
    Path(args.graph_output).parent.mkdir(parents=True,exist_ok=True); Path(args.graph_output).write_text(g.markdown())
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(g.markdown()+'\n\n'+atlas.status_table()); print(f'wrote {args.graph_output} and {out}')
def cmd_build_kernel(args):
    cmd=[sys.executable,'tools/build_kernel.py','--ell',str(args.ell)]
    if args.skip_auto_atom_map: cmd.append('--skip-auto-atom-map')
    if args.atom_map: cmd+=['--atom-map',args.atom_map]
    run_cmd(cmd); atlas=AtlasDB(args.atlas_root); register_kernel_artifacts(args.ell,atlas); run_structure_miner(args.ell,Path(f'results/engine/ell{args.ell}_mixed_depth_kernel.csv'),atlas,args.q_mode)
def ensure_kernel(ell,args):
    p=Path(f'results/engine/ell{ell}_mixed_depth_kernel.csv')
    if p.exists() or not args.build_missing: return p
    try: run_cmd([sys.executable,'tools/build_kernel.py','--ell',str(ell)])
    except Exception as e: print(f'build failed for ell={ell}: {e}')
    return p
def cmd_certify(args):
    if args.scan=='all': return cmd_scan(args)
    if not args.input: raise SystemExit('--input is required unless --scan all')
    qv=mixed_q_values(args.input,args.q_mode); cert,sel,pol=certify_one(Path(args.input),args.q_target,args.q_mode,args.source_policy,args.model,args.theorem_id,args.kernel_id,Path(args.output),args.atlas_root,args.graph_store,args.allow_q_down,args.allow_diff_down,max_q=max(qv) if qv else None)
    print(cert.markdown()); print(f'Selected model: {sel}; Source policy: {pol}')
def cmd_scan(args):
    atlas=AtlasDB(args.atlas_root); rows=[]; first_fail=None
    for ell in range(1,args.max_ell+1):
        mixed=Path(args.input) if args.input else ensure_kernel(ell,args)
        if not mixed.exists(): rows.append((ell,'','missing_kernel',str(mixed),'')); continue
        atlas.register_kernel(f'ell{ell}_mixed_depth',str(mixed),ell=ell,kind='mixed_depth',rows=count_rows(mixed)); run_structure_miner(ell,mixed,atlas,args.q_mode)
        qs=mixed_q_values(mixed,args.q_mode); max_q=max(qs) if qs else None
        for q in qs:
            theorem_id=f'ell{ell}_q{q}_{args.model}'; out=Path(f'results/certificates/{theorem_id}.md')
            cert,sel,pol=certify_one(mixed,q,args.q_mode,args.source_policy,args.model,theorem_id,f'ell{ell}_mixed_depth',out,args.atlas_root,args.graph_store,args.allow_q_down,args.allow_diff_down,ell=ell,max_q=max_q)
            ok,errs=cert.verify(); rows.append((ell,q,'pass' if ok else 'fail','; '.join(errs[:3]),sel))
            if not ok and first_fail is None: first_fail=(ell,q,sel,errs)
    report=Path(args.report); report.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Tantrium scan-all report','']+[f'- ell={e} q={q} model={m} status={s} {d}' for e,q,s,d,m in rows]
    lines.append(f'\nFirst obstruction: ell={first_fail[0]} q={first_fail[1]} model={first_fail[2]} errors={first_fail[3]}' if first_fail else '\nNo obstruction found in scanned kernels.')
    report.write_text('\n'.join(lines)); print(f'wrote {report}')
def cmd_preprocess(args):
    rec=preprocess_csv(args.input,args.output); AtlasDB(args.atlas_root).register_kernel(args.kernel_id,args.output,ell=args.ell,kind='external_preprocessed',rows=rec['rows']); print(rec)
def cmd_compare_atlas(args):
    summary=compare_manifest(AtlasDB(args.atlas_root).manifest()); write_compare_report(args.output,summary); print(f'wrote {args.output}')
def main():
    p=argparse.ArgumentParser(description='Tantrium Proof Foundry v1.3'); sub=p.add_subparsers(dest='cmd',required=True)
    g=sub.add_parser('graph'); g.add_argument('--status',default='write',choices=['write','all']); g.add_argument('--output',default='docs/THEOREM_GRAPH.md'); g.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); g.set_defaults(func=cmd_graph)
    st=sub.add_parser('status'); st.add_argument('--update',action='store_true'); st.add_argument('--atlas-root',default='results/atlas'); st.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); st.add_argument('--graph-output',default='docs/THEOREM_GRAPH.md'); st.add_argument('--output',default='results/atlas/status.md'); st.set_defaults(func=cmd_status)
    b=sub.add_parser('build-kernel'); b.add_argument('--ell',type=int,required=True); b.add_argument('--atlas-root',default='results/atlas'); b.add_argument('--q-mode',default='two_qd'); b.add_argument('--atom-map',default=''); b.add_argument('--skip-auto-atom-map',action='store_true'); b.set_defaults(func=cmd_build_kernel)
    c=sub.add_parser('certify'); c.add_argument('--input'); c.add_argument('--scan',default='one',choices=['one','all']); c.add_argument('--max-ell',type=int,default=4); c.add_argument('--build-missing',action='store_true',default=True); c.add_argument('--q-target',type=int,default=20); c.add_argument('--q-mode',default='two_qd',choices=['two_qd','qd','qd_plus_p','two_qd_plus_p']); c.add_argument('--source-policy',default='q_ge_target',choices=['all','target_only','q_ge_target','q_gt_target']); c.add_argument('--model',default='qdiff',choices=['unit','qgap','diffgap','qdiff','qdiffp','ell2_depth','conservative','split_pair','diagonal_residue','q6_low_family','low_q_family','boundary_family','auto']); c.add_argument('--allow-q-down',action='store_true'); c.add_argument('--allow-diff-down',action='store_true'); c.add_argument('--theorem-id',default='manual_certificate'); c.add_argument('--kernel-id',default='mixed_depth_kernel'); c.add_argument('--output',default='results/certificates/manual_certificate.md'); c.add_argument('--atlas-root',default='results/atlas'); c.add_argument('--graph-store',default='tantrium/theorem_graph/theorem_graph.yaml'); c.add_argument('--report',default='results/certificates/scan_all_report.md'); c.set_defaults(func=cmd_certify)
    pr=sub.add_parser('preprocess'); pr.add_argument('--input',required=True); pr.add_argument('--output',required=True); pr.add_argument('--kernel-id',default='external_kernel'); pr.add_argument('--ell',type=int); pr.add_argument('--atlas-root',default='results/atlas'); pr.set_defaults(func=cmd_preprocess)
    ca=sub.add_parser('compare-atlas'); ca.add_argument('--atlas-root',default='results/atlas'); ca.add_argument('--output',default='results/atlas/comparative_report.md'); ca.set_defaults(func=cmd_compare_atlas)
    args=p.parse_args(); args.func(args)
if __name__=='__main__': main()
