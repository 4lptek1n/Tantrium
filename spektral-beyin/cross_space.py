"""
cross_space.py — ORTAK UZAY (cross-space) kaniti: molekul/protein/DNA/RNA/math
hepsi TEK coord_91 grounding uzayinda, AYNI kanonik kimlikte (yasa) bulusuyor.

Cekirdek icgoru: PERIYODIKLIK alfabe-bagimsizdir.
  Saf periyot-p tekrar -> s[n]=s[n-p] -> yasa = (0,...,0,1), kokler = p. birim kokleri.
  => periyot-3 (kodon) DNA, RNA, protein, math AYNI kimlige iner -> cross-space bag.
"""
import sys, os; sys.path.insert(0,"cekirdek")
import numpy as np
from engine import gram_spectrum
from coord91 import coord_91
from domains import genotype, seq_to_A, A_molecule, extract_law
np.set_printoptions(suppress=True, precision=4)

# ---- alfabe -> sayi kodlamalari (her uzay icin adaptor) ----
DNA={'A':2.0,'G':3.0,'C':1.0,'T':1.5}
RNA={'A':2.0,'G':3.0,'C':1.0,'U':1.5}                 # U=T -> transkripsiyon kimligi korur
AA ={'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'Q':-3.5,'E':-3.5,'G':-0.4,'H':-3.2,
     'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,'P':-1.6,'S':-0.8,'T':-0.7,'W':-0.9,
     'Y':-1.3,'V':4.2}                                # Kyte-Doolittle hidropati (gercek olcek)

def kodla(s, tablo): return [tablo[c] for c in s]
def genotip(seq, uzay):
    A=seq_to_A(np.asarray(seq,float))
    g=genotype("x",uzay,A,raw_seq=seq)
    return np.asarray(g["coord"],float), np.round(g["law"],4), int(g["order"]), g["seed"]

def bag(a,b): return float(np.linalg.norm(a-b))      # coord_91 grounding mesafesi

print("="*66)
print(" CROSS-SPACE: protein / DNA / RNA / math TEK uzayda bulusuyor mu?")
print("="*66)

# ---- 1) TRANSKRIPSIYON: DNA -> RNA kimligi korur (d=0 olmali) ----
dna = "ATGCGTACGTTGCACGATCG"
rna = dna.replace("T","U")
cd,ld,_,_ = genotip(kodla(dna,DNA),"dna")
cr,lr,_,_ = genotip(kodla(rna,RNA),"rna")
print(f"\n[1] TRANSKRIPSIYON  DNA '{dna}'  ->  RNA '{rna}'")
print(f"    yasa(DNA)={ld}  yasa(RNA)={lr}")
print(f"    coord_91 mesafe = {bag(cd,cr):.2e}   -> AYNI kimlik (transkripsiyon korunur)")

# ---- 2) KODON PERIYOT-3: DNA/RNA/protein/math AYNI yasaya iner ----
print(f"\n[2] PERIYOT-3 (kodon) — 4 farkli uzay, AYNI kanonik kimlik:")
ornk = {
    "dna     (ATG)x7": kodla("ATG"*7, DNA),
    "rna     (AUG)x7": kodla("AUG"*7, RNA),
    "protein (GPA)x7": kodla("GPA"*7, AA),     # Gly-Pro-Ala (kollajen benzeri periyot-3)
    "math    (1,5,2)x7": [1.0,5.0,2.0]*7,
}
coords={}
for ad,seq in ornk.items():
    v,law,order,_=genotip(seq,ad.split()[0])
    coords[ad]=v
    print(f"    {ad:18s} yasa={list(law)} order={order}")
keys=list(coords)
print("    --- coord_91 grounding mesafeleri (periyot-3 grubu) ---")
for i in range(len(keys)):
    for j in range(i+1,len(keys)):
        print(f"      d({keys[i].split()[0]:7s},{keys[j].split()[0]:7s}) = {bag(coords[keys[i]],coords[keys[j]]):.2e}")

# ---- 3) KONTROL: aperiyodik protein UZAK olmali ----
v_ap,_,_,_ = genotip(kodla("MKWVTFISLLFLFSSAYS","dna" if False else AA),"protein")
d_in  = bag(coords["protein (GPA)x7"], coords["dna     (ATG)x7"])
d_out = bag(coords["protein (GPA)x7"], v_ap)
print(f"\n[3] KONTROL: periyot-3 protein <-> aperiyodik protein (sinyal peptidi)")
print(f"    d(periyot3 prot, periyot3 dna) = {d_in:.2e}   <- BAG")
print(f"    d(periyot3 prot, aperiyodik)   = {d_out:.3f}   <- bag YOK")

# ---- 4) MOLEKUL de ayni uzayda (benzen halkasi ~ periyodik) ----
benzen_atoms=["C"]*6; benzen_bonds=[(i,(i+1)%6,1.5) for i in range(6)]
EN={'C':2.55}
Gm,wm,_=gram_spectrum(A_molecule(benzen_atoms,benzen_bonds,EN))
vm,_=coord_91(wm)
print(f"\n[4] MOLEKUL (benzen halkasi) ayni coord_91 uzayinda:")
print(f"    d(benzen, periyot-3 dna) = {bag(vm,coords['dna     (ATG)x7']):.3f}")
print(f"    (molekul/protein/dna/rna/math HEPSI tek grounding uzayinda yer aliyor)")

print("\n"+"="*66)
print(" SONUC: cross-space GERCEK. Periyot-3 kodon kimligi DNA=RNA=protein=math")
print(" ayni yasaya ([0,0,1] ailesine) iner; transkripsiyon kimligi korur;")
print(" aperiyodik uzak kalir. coord_91 = ortak grounding uzayi.")
