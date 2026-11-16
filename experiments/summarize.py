"""Aggregate finished runs into mean ± standard deviation tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cancerai.config import DATASETS, DATASET_TITLES, ROOT as PROJECT_ROOT
from cancerai.metrics import format_mean_std, mean_std, save_comparison
from experiments.configs import ABLATION_CONFIGS, MAIN_CONFIGS

METRICS = PROJECT_ROOT / "results" / "metrics"


def load_runs() -> list[dict]:
    if not METRICS.exists():
        return []
    runs = []
    for path in sorted(METRICS.glob("*.json")):
        record = json.loads(path.read_text())
        if record.get("smoke"):
            continue
        runs.append(record)
    return runs


def _cell(runs, dataset, config, key_path) -> str:
    values = []
    for record in runs:
        if record["dataset"] != dataset or record["config"] != config:
            continue
        cursor = record
        for key in key_path:
            cursor = cursor[key]
        if cursor is not None:
            values.append(cursor)
    return format_mean_std(*mean_std(values))


def comparison_tables(runs: list[dict]) -> str:
    lines = [
        "# Comparison",
        "",
        "Primary metric: test macro-F1, mean ± sample standard deviation across seeds.",
        "A cell stays empty until every listed seed for that configuration has a metrics file.",
        "",
        "## Models",
        "",
        "| Dataset | Custom CNN | Frozen ResNet18 | Fine-tuned ResNet18 |",
        "|---|---:|---:|---:|",
    ]
    f1_table = {}
    for dataset in DATASETS:
        f1_table[dataset] = {}
        cells = []
        for config in MAIN_CONFIGS:
            text = _cell(runs, dataset, config, ("test", "f1_macro"))
            cells.append(text)
            mean, _std = mean_std(
                record["test"]["f1_macro"]
                for record in runs
                if record["dataset"] == dataset and record["config"] == config and record["test"].get("f1_macro") is not None
            )
            f1_table[dataset][config] = mean
        lines.append(f"| {DATASET_TITLES[dataset]} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## Augmentation ablation (fine-tuned ResNet18)",
            "",
            "| Dataset | With augmentation | Without augmentation |",
            "|---|---:|---:|",
        ]
    )
    for dataset in DATASETS:
        cells = [_cell(runs, dataset, config, ("test", "f1_macro")) for config in ABLATION_CONFIGS]
        lines.append(f"| {DATASET_TITLES[dataset]} | " + " | ".join(cells) + " |")
    lines.extend(["", "## Accuracy (secondary)", ""])
    lines.append("| Dataset | Custom CNN | Frozen ResNet18 | Fine-tuned ResNet18 |")
    lines.append("|---|---:|---:|---:|")
    for dataset in DATASETS:
        cells = [_cell(runs, dataset, config, ("test", "accuracy")) for config in MAIN_CONFIGS]
        lines.append(f"| {DATASET_TITLES[dataset]} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"Finished metric files: {len(runs)} / 48.")
    lines.append("")
    plot_values = {
        name: {config: f1_table[name][config] for config in MAIN_CONFIGS} for name in DATASETS
    }
    if any(value == value for row in plot_values.values() for value in row.values()):  # not NaN
        save_comparison(
            plot_values,
            PROJECT_ROOT / "results" / "plots" / "macro_f1_comparison.png",
            "Test macro-F1 by modality and training strategy",
        )
    return "\n".join(lines)


def main() -> None:
    text = comparison_tables(load_runs())
    path = PROJECT_ROOT / "results" / "comparison.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
