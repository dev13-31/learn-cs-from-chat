#!/usr/bin/env python3
"""
log_decision.py - Append a validated 4-column row to a CS decision log (TSV)
and automatically regenerate the rich HTML dashboard and Markdown guide.
Usage:
  python log_decision.py --dir "D:/gemini/CS decisions/<slug>" --slug "<slug>" \
                         --did "<what did>" \
                         --why "<why decided>" \
                         --happened "<what happened>" \
                         --next "<what decision taken next and why>"
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def sanitize_cell(text: str) -> str:
    """Strips tabs/newlines/CR so cells stay on one line, and prefix any cell
    whose first char a spreadsheet would parse as a formula (=, +, -, @) with a single quote."""
    if not text:
        return ""
    v = text.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    v = " ".join(v.split())  # normalize internal spaces
    if v and v[0] in ("=", "+", "-", "@"):
        return f"'{v}"
    return v

def main():
    parser = argparse.ArgumentParser(description="Log a 4-column decision to CS decisions TSV")
    parser.add_argument("--dir", type=str, required=True, help="Session directory (e.g. D:/gemini/CS decisions/my-session)")
    parser.add_argument("--slug", type=str, required=False, help="Session slug identifier")
    parser.add_argument("--did", type=str, required=True, help="What the agent did")
    parser.add_argument("--why", type=str, required=True, help="Why decided to do it")
    parser.add_argument("--happened", type=str, required=True, help="What happened after doing it")
    parser.add_argument("--next", type=str, required=True, help="What decision taken next and why")
    parser.add_argument("--no-render", action="store_true", help="Skip automatic HTML/MD rendering")
    args = parser.parse_args()

    session_dir = Path(args.dir).resolve()
    session_slug = args.slug or session_dir.name
    session_dir.mkdir(parents=True, exist_ok=True)

    tsv_path = session_dir / f"{session_slug}.tsv"

    # Write header if file does not exist or is empty
    if not tsv_path.exists() or tsv_path.stat().st_size == 0:
        with open(tsv_path, "w", encoding="utf-8") as f:
            f.write("what the agent did\twhy decided to do it\twhat happened after doing it\twhat decision taken next and why\n")

    # Sanitize fields
    c_did = sanitize_cell(args.did)
    c_why = sanitize_cell(args.why)
    c_hap = sanitize_cell(args.happened)
    c_nxt = sanitize_cell(args.next)

    # Append row
    with open(tsv_path, "a", encoding="utf-8") as f:
        f.write(f"{c_did}\t{c_why}\t{c_hap}\t{c_nxt}\n")

    print(f"Logged decision to: {tsv_path}")

    # Auto-render HTML and MD
    if not args.no_render:
        render_script = Path(__file__).parent / "render_cs_mentor.py"
        if render_script.exists():
            subprocess.run([sys.executable, str(render_script), "--dir", str(session_dir), "--slug", session_slug], check=True)

if __name__ == "__main__":
    main()
