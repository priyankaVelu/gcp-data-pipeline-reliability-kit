"""Generate a Markdown table from a paper-suite summary JSON. No manual values."""
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("summary"); p.add_argument("--output")
a=p.parse_args(); src=Path(a.summary); d=json.loads(src.read_text(encoding="utf-8"))
lines=["# Machine-generated experiment summary","",
       f"- Commit: \u0060{d['commit_sha']}\u0060",f"- Python: {d['python']}",
       f"- Observations: {d['observation_count']}","",
       "| Scenario | Variant | N | Runs | Detection rate | Correct-run rate | Median ms | Mean ms |",
       "|---|---|---:|---:|---:|---:|---:|---:|"]
for r in d["results"]:
    lines.append(f"| {r['scenario']} | {r['variant']} | {r['dataset_size']} | {r['runs']} | {r['detection_rate']} | {r['correct_run_rate']} | {r['runtime_ms_median']} | {r['runtime_ms_mean']} |")
text="\n".join(lines)+"\n"; out=Path(a.output) if a.output else src.with_suffix(".md")
out.write_text(text,encoding="utf-8"); print(out)
