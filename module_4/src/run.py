# module_3/run.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent        # .../module_3
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))             

from app import create_app                    # app/__init__.py must define create_app
from app.pipeline import run_pipeline         # Run pipeline


def cmd_web(host: str, port: int, debug: bool) -> None:
    app = create_app()
    app.run(host=host, port=port, debug=debug)


def cmd_pipeline(max_records: int, delay: float) -> None:
    summary = run_pipeline(max_records=max_records, delay=delay)
    print(summary["message"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run web app or data pipeline.")
    sub = parser.add_subparsers(dest="cmd")

    # Default to web if no subcommand
    p_web = sub.add_parser("web", help="Run the Flask web server")
    p_web.add_argument("--host", default="0.0.0.0")
    p_web.add_argument("--port", type=int, default=8080)
    p_web.add_argument("--debug", action="store_true")

    p_pipe = sub.add_parser("pipeline", help="Run scrape → clean → LLM → load")
    p_pipe.add_argument("--max-records", type=int, default=100)
    p_pipe.add_argument("--delay", type=float, default=0.5)

    args = parser.parse_args()

    if args.cmd == "pipeline":
        cmd_pipeline(args.max_records, args.delay)
    else:
        # default: web
        # allow `python run.py` (no subcommand) to start the server
        ns = args if args.cmd == "web" else argparse.Namespace(
            host="0.0.0.0", port=8080, debug=True
        )
        cmd_web(ns.host, ns.port, ns.debug)


if __name__ == "__main__":
    main()