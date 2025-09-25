"""
Unit tests for the pipeline module.

These tests cover:
- run_llm_hosting: verifying subprocess invocation and error bubbling.
- run_pipeline: verifying both the no-new-rows short-circuit and the full
  happy path (cleaning, LLM hosting, reading JSON, and DB insert).
"""
import subprocess
from pathlib import Path

import pytest
import app.pipeline as pipeline


# --------------------------
# run_llm_hosting tests
# --------------------------


def test_run_llm_hosting_invokes_subprocess(monkeypatch, tmp_path):
    """Success path: ensure subprocess.run is called with our paths and flags."""
    called = {}

    def fake_run(cmd, **kwargs):
        called["cmd"] = cmd
        called["kwargs"] = kwargs

        class _CP:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return _CP()

    monkeypatch.setattr(subprocess, "run", fake_run)

    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"

    pipeline.run_llm_hosting(inp, out)

    cmd = called["cmd"]
    # verify flags + arguments
    assert "--file" in cmd and "--out" in cmd
    assert cmd[cmd.index("--file") + 1] == str(inp)
    assert cmd[cmd.index("--out") + 1] == str(out)

    # verify run options
    assert called["kwargs"]["check"] is True
    assert called["kwargs"]["capture_output"] is True
    assert called["kwargs"]["text"] is True


def test_run_llm_hosting_bubbles_error_and_logs(monkeypatch, tmp_path):
    """Failure path: subprocess raises CalledProcessError; we log and re-raise."""

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    logged = {}

    def fake_error(fmt, *args):
        logged["msg"] = fmt % args if args else fmt

    # pipeline.logger is module-level; patch its error()
    monkeypatch.setattr(pipeline.logger, "error", fake_error)

    with pytest.raises(subprocess.CalledProcessError):
        pipeline.run_llm_hosting(tmp_path / "in.json", tmp_path / "out.json")

    assert "LLM hosting script failed" in logged.get("msg", "")


# --------------------------
# run_pipeline tests
# --------------------------


def test_run_pipeline_returns_no_new_rows(monkeypatch):
    """When run_clean returns 0, pipeline should short-circuit and not call LLM."""
    # existing rids doesn't matter here
    monkeypatch.setattr(pipeline, "existing_rids", lambda: {"r1"})
    # make run_clean return 0 (nothing new)
    monkeypatch.setattr(pipeline, "run_clean", lambda **kwargs: 0)

    # guard: if these were called we'd notice (they shouldn't be)
    monkeypatch.setattr(
        pipeline,
        "run_llm_hosting",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not run LLM")),
    )
    monkeypatch.setattr(
        pipeline,
        "read_json",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not read json")),
    )
    monkeypatch.setattr(
        pipeline,
        "insert_records_by_url",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not insert")),
    )

    result = pipeline.run_pipeline(max_records=3, delay=0.0)
    assert result == {"cleaned": 0, "llm": 0, "inserted": 0, "message": "No new rows"}


def test_run_pipeline_happy_path(monkeypatch):
    """Full happy path: clean -> LLM -> read -> insert, returning a summary."""
    # 1) already-have set
    monkeypatch.setattr(pipeline, "existing_rids", lambda: {"abc", "def"})

    # 2) run_clean returns N new rows written to CLEAN_JSON by the cleaner
    monkeypatch.setattr(pipeline, "run_clean", lambda **kwargs: 3)  # report 3 cleaned

    # 3) LLM hosting is a no-op (we just need it to be called without error)
    llm_called = {}

    def fake_llm(in_path: Path, out_path: Path):
        llm_called["args"] = (in_path, out_path)

    monkeypatch.setattr(pipeline, "run_llm_hosting", fake_llm)

    # 4) read_json returns two normalized rows
    rows = [{"url": "u1"}, {"url": "u2"}]
    monkeypatch.setattr(pipeline, "read_json", lambda _p: rows)

    # 5) DB insert returns number inserted (e.g., 2)
    inserted_capture = {}

    def fake_insert(objs, dt):
        inserted_capture["objs"] = objs
        inserted_capture["dt"] = dt
        return 2

    monkeypatch.setattr(pipeline, "insert_records_by_url", fake_insert)

    # Execute
    result = pipeline.run_pipeline(max_records=10, delay=0.0)

    # Assertions
    assert llm_called["args"] == (pipeline.CLEAN_JSON, pipeline.FINAL_JSON)
    assert inserted_capture["objs"] is rows  # same list passed through
    assert result["cleaned"] == 3
    assert result["llm"] == 2
    assert result["inserted"] == 2
    assert "Cleaned 3, LLM rows 2, inserted 2" in result["message"]
