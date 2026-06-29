import os

# numpy/BLAS import'undan ÖNCE: tek-thread BLAS. Çok sayıda ağır lineer-cebir testi
# (Cosmos topoloji homotopisi, spektral okumalar) art arda koşunca threaded OpenBLAS
# fork/thread deadlock'una giriyordu (donmuş utime, %0 CPU). Tek-thread küçük matrislerde
# zaten daha hızlı ve kilidi tamamen önler. (Bu blok ilk import'tan önce çalışmalı.)
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "1")

import pytest

import tantrium
from tantrium import CertificationEngine


@pytest.fixture(scope="session")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="session")
def ai():
    return tantrium.AI()
