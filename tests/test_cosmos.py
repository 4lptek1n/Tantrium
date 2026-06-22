"""Cosmos yaşam-döngüsü testleri — bir tohumun T₀→T₁₀ evren ömrü, mühürlü.

Tek yasa (pozitiflik) baştan sona; akış deterministik, çağlar sıralı, çıktı
denetlenebilir tek bir sertifika."""
import tantrium
from tantrium.cosmos import Lifecycle, run_cosmos


def test_all_epochs_present_in_order():
    """T₀…T₁₀: on bir çağ, doğru sırada."""
    life = run_cosmos(inflation_steps=12)
    ts = [e.t for e in life.epochs]
    assert ts == ["T₀", "T₁", "T₂", "T₃", "T₄", "T₅", "T₆", "T₇", "T₈", "T₉", "T₁₀"]


def test_deterministic_lifecycle():
    """Aynı tohum → birebir aynı ömür ve aynı ana mühür (dış veri/rastgelelik yok)."""
    a = run_cosmos(seed=[0.5**k for k in range(6)], inflation_steps=12)
    b = run_cosmos(seed=[0.5**k for k in range(6)], inflation_steps=12)
    assert a.master_seal == b.master_seal
    assert [e.reading for e in a.epochs] == [e.reading for e in b.epochs]


def test_law_held_and_critical_line():
    """Tek yasa korunur ve evren kritik çizgide doğar (Li>0 ∧ Λ≤0)."""
    life = run_cosmos(inflation_steps=15)
    assert life.on_critical_line is True
    assert life.paradigms_frozen == 23
    assert life.effective_dim >= 1
    assert len(life.master_seal) == 64


def test_two_fates_recorded():
    """T₁₀ iki kaderi de kaydeder: Büyük Çöküş (μ*) ve Büyük Yırtılma (kondisyon)."""
    life = run_cosmos(inflation_steps=12)
    end = life.epochs[-1]
    assert "Büyük Çöküş" in end.reading and "Büyük Yırtılma" in end.reading
    assert "μ*" in life.fate_crunch


def test_sdk_facade():
    """ai.cosmos(...) yaşam-döngüsü sertifikası döndürür ve özetlenebilir."""
    life = tantrium.AI().cosmos(inflation_steps=10)
    assert isinstance(life, Lifecycle)
    assert "COSMOS" in life.summary()
    assert "kritik çizgide" in life.summary()


def test_grid_depth_axis_present():
    """Izgaranın derinlik ekseni: T₁ doğuş + T₁₀ son dört-katman okuması Cosmos'ta."""
    from tantrium.core.spectral_reading import SpectralReading
    life = run_cosmos(inflation_steps=15)
    assert isinstance(life.genesis_reading, SpectralReading)   # doğuşta 4 katman
    assert isinstance(life.final_reading, SpectralReading)     # sonda 4 katman
    assert life.universality_path                              # mikro yörünge örneklendi
    assert "4-katman ızgarası" in life.summary()
    assert "ÖZVEKTÖR" in life.summary()


def test_lifecycle_phase_transition_detected():
    """Izgara faz geçişini yakalar: genişleyen evren özvektörde localize olur (ergodik→yerleşik)."""
    life = run_cosmos(inflation_steps=30)
    g, f = life.genesis_reading, life.final_reading
    # özvektör katmanı ömür boyunca değişir (localization dinamiği)
    assert g.ergodicity is not None and f.ergodicity is not None
    assert f.ergodicity < g.ergodicity            # genişledikçe yerleşikleşir
    assert any("özvektör" in t for t in life.transitions)
