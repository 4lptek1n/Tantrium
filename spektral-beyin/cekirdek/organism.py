"""
YAŞAYAN ORGANİZMA — arka beyin + ön beyin TEK döngüde.
İlke: AĞIZ ASLA ÇEKİRDEK OLMADAN KONUŞMAZ. Her söz çekirdeğin o anki
durumundan doğar. Boş laf yok.

Akış (insan gibi):
  girdi -> ÇEKİRDEK işler (yasa, coord, sürpriz) -> AĞIZ o durumu söyler
        -> sürpriz büyükse: ağırlığa çök (yaşarken öğren) + grafa ekle
        -> sürpriz küçükse: sadece konuş (tanıdık, öğrenme yok)
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, torch
from domains import genotype, A_math, A_dna, A_molecule, A_finance, A_material
from neural_brain import NeuralBrain

class Organism:
    def __init__(self, surprise_thresh=0.3, lr=1e-3):
        self.nb=NeuralBrain(lr=lr, k_tokens=4, rank=8)   # ön beyin (LoRA, yaşayan)
        self.brain={}                                     # arka beyin (graf)
        self.coords=None; self.names=[]
        self.thresh=surprise_thresh
        self.seen_count={}

    # ---- arka beyin: bir girdiyi genotipe indir ----
    def _ingest(self, name, domain, A, raw=None):
        return genotype(name, domain, A, raw_seq=raw)

    # ---- SÜRPRİZ = en yakın komşuya coord uzaklığı (prediction error) ----
    def _surprise(self, coord):
        if not self.names: return 1e9, None
        d=np.linalg.norm(self.coords-coord, axis=1)
        j=int(d.argmin())
        return float(d[j]), self.names[j]

    # ---- TEK NEFES: çekirdek işler + ağız konuşur + (gerekirse) öğrenir ----
    def perceive(self, name, domain, A, raw=None):
        g=self._ingest(name, domain, A, raw)
        coord=g['coord']
        d, komsu=self._surprise(coord)
        seed=round(float(np.real(g['seed'][0])),3) if len(g['seed']) else 0.0

        # AĞIZ: çekirdek durumundan konuşur (boş laf değil)
        prompt='Bu yapinin kurali ve karakteri:'
        # çekirdeğin söyleyeceği gerçek (context = çekirdek durumu)
        cekirdek_durum=(f'order {g["order"]}, yasa {np.round(g["law"],2).tolist()}, '
                        f'sabit {seed}, en yakin {komsu if komsu else "(ilk nesne)"}, '
                        f'surpriz {d:.2f}')

        karar=''
        if d > self.thresh:        # SÜRPRİZ -> yaşarken öğren
            # bu deneyimi ağırlığa çök (LoRA), grafa ekle
            target=f' {cekirdek_durum}.'
            loss=self.nb.learn_step(coord, prompt, target)
            self._add_node(name, g, coord)
            karar=f'YENİ/SÜRPRİZ (d={d:.2f}>{self.thresh}) -> ÖĞRENDİ (loss={loss:.3f}), grafa eklendi'
        else:                       # TANIDIK -> sadece konuş, öğrenme yok
            self.seen_count[komsu]=self.seen_count.get(komsu,0)+1
            karar=f'TANIDIK (d={d:.2f}<={self.thresh}, ~{komsu}) -> sadece konuştu, öğrenme yok'

        return dict(durum=cekirdek_durum, karar=karar, surpriz=d, komsu=komsu)

    def _add_node(self, name, g, coord):
        self.brain[name]=g
        self.names.append(name)
        self.coords=coord[None] if self.coords is None else np.vstack([self.coords, coord])
