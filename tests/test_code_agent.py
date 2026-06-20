"""ASI §12 P4 — kod ajanı: grounding + halüsinasyon-tespiti + izole test-runner + agentic."""

from tantrium.core.code_agent import (
    check_grounded,
    ground_api,
    ground_codebase,
    run_tests,
    verify_api_symbol,
)


def test_verify_api_symbol_hallucination_guard():
    """Dış API çağrısı GERÇEK mi (introspection) — uydurma sembol reddedilir (Tier 3.5)."""
    assert verify_api_symbol("json.dumps") and verify_api_symbol("math.sqrt")
    assert not verify_api_symbol("json.nonexistent")  # HAYALİ API → False
    assert not verify_api_symbol("nosuchmodule.foo")  # import edilemez → False


def test_ground_api_returns_real_symbol():
    """Hint → GERÇEK API sembolü (var olmayan asla üretilmez); allowlist geçidi."""
    g = ground_api("math", "square root sqrt")
    assert g and g["qualname"] == "math.sqrt" and g["exists"]
    assert ground_api("os", "anything", allowlist={"math", "json"}) is None  # allowlist DIŞI


def test_ground_codebase():
    g = ground_codebase({"u.py": "def helper(x):\n    return x+1\ndef double(x):\n    return x*2"})
    assert "helper" in g["symbols"] and "double" in g["symbols"]
    assert ("u.py", "DEFINES", "helper") in g["edges"]


def test_check_grounded_catches_hallucination():
    """Var olmayan sembol = halüsinasyon → grounded=False (LLM yakalayamaz, biz yakalarız)."""
    g = ground_codebase({"u.py": "def double(x):\n    return x*2"})
    assert check_grounded("def f(x):\n    return double(x)+1", g)["grounded"] is True
    bad = check_grounded("def f(x):\n    return nonexistent_fn(x)", g)
    assert bad["grounded"] is False and "nonexistent_fn" in bad["ungrounded"]


def test_check_grounded_syntax():
    assert check_grounded("def f(:\n  bad syntax")["syntax_ok"] is False


def test_run_tests_isolated():
    code = "def solve(x):\n    return x*2+1\n"
    assert run_tests(code, "def test_a():\n    assert solve(1)==3 and solve(2)==5")["passed"]
    assert not run_tests(code, "def test_b():\n    assert solve(1)==999")["passed"]


def test_ai_code_task_agentic():
    """ai.code_task: sentez → köklülük → test, üç kapı (kapalı döngü)."""
    import tantrium

    ai = tantrium.AI()
    r = ai.code_task(
        examples=[(1, 3), (2, 5), (3, 7)], tests="def test():\n    assert solve(5)==11"
    )
    assert r["verified"] is True and r["grounded"] is True and r["tests_passed"] is True


def test_ai_verify_code_rejects_hallucination():
    import tantrium

    ai = tantrium.AI()
    r = ai.verify_code(
        "def f(x):\n    return imaginary_api(x)", codebase={"l.py": "def base(x):\n    return x"}
    )
    assert r["verified"] is False and "imaginary_api" in r["ungrounded"]
