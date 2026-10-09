"""Opt-in real sandbox round trip; uses synthetic fixtures, not submitted reports."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH
from research import _configured_sandbox
from sandbox import download, upload


def main():
    root = Path(__file__).resolve().parents[1]
    with _configured_sandbox() as backend:
        print(f"Sandbox: {type(backend).__name__}", flush=True)
        response = backend.execute("mkdir -p /tmp/work/research/notes /tmp/work/report")
        assert response.exit_code == 0, response.output
        source = [{"n": 4, "id": "fixture", "url": "https://example.org/fixture",
                   "title": "Synthetic integration fixture", "date": "n.d.", "source": "web"}]
        upload(backend, {VALIDATOR_PATH: (root / "check_citations.py").read_bytes(),
                         FINALIZER_PATH: (root / "finalize_citations.py").read_bytes(),
                         REPORT_PATH: b"# Synthetic fixture\nEvidence [4].\n",
                         SOURCES_PATH: json.dumps(source).encode()})
        for script in (FINALIZER_PATH, VALIDATOR_PATH):
            response = backend.execute(f"python3 {script}")
            assert response.exit_code == 0, response.output
            print(response.output.strip(), flush=True)
        outputs = download(backend, [REPORT_PATH, SOURCES_PATH])
        assert b"## References" in outputs[REPORT_PATH]
        assert json.loads(outputs[SOURCES_PATH])[0]["n"] == 1
        upload(backend, {REPORT_PATH: b"# Invalid fixture\n[99]\n"})
        response = backend.execute(f"python3 {VALIDATOR_PATH}")
        assert response.exit_code != 0
        print("Invalid report rejected; exiting context to clean up sandbox.", flush=True)
    print("Sandbox round trip OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
