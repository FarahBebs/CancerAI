"""Train one cell of the study, or the full 48-run grid.

The split file is read, not rewritten, once results/splits exists.
The test loader is used only after the best validation epoch is restored.

Examples
--------
python -m experiments.run_experiments --smoke
python -m experiments.run_experiments --dataset brain --config custom_cnn --seed 42
python -m experiments.run_experiments
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from cancerai.config import BATCH_SIZE, DATASETS, DATASET_TITLES, ROOT as PROJECT_ROOT
from cancerai.datasets import prepare
from cancerai.explain import save_failure_grid, save_gradcam_grid
from cancerai.metrics import classification_metrics, save_confusion, save_curves, worst_mistakes
from cancerai.models import build_model, count_params
from cancerai.training import get_device, inference_milliseconds, make_loader, run_eval, seed_everything, train_model
from experiments.configs import CONFIGS

METRICS = PROJECT_ROOT / "results" / "metrics"
PLOTS = PROJECT_ROOT / "results" / "plots"
GRADCAM = PROJECT_ROOT / "results" / "gradcam"
CHECKPOINTS = PROJECT_ROOT / "results" / "checkpoints"
MODELS = PROJECT_ROOT / "models"


def inference_ms(model, dataset, device, dataset_name: str) -> float:
    return inference_milliseconds(model, dataset, device, dataset_name)


def run_one(dataset: str, config_name: str, seed: int, smoke: bool = False, max_batches=None, epochs=None) -> dict:
    config = CONFIGS[config_name]
    device = get_device()
    seed_everything(seed)
    bundle = prepare(dataset, augment=config["augment"])
    seed_everything(seed)
    model = build_model(
        config["model"],
        len(bundle.classes),
        freeze_backbone=config["freeze_backbone"],
        pretrained=config["pretrained"] and not smoke,
    )
    total, trainable = count_params(model)
    train_loader = make_loader(bundle.train_ds, BATCH_SIZE, shuffle=True, seed=seed, device=device)
    val_loader = make_loader(bundle.val_ds, BATCH_SIZE, shuffle=False, seed=seed, device=device)
    test_loader = make_loader(bundle.test_ds, BATCH_SIZE, shuffle=False, seed=seed, device=device)
    prefix = f"[{dataset} {config_name} seed {seed}]"
    print(prefix, DATASET_TITLES[dataset], "device", device, flush=True)
    print(f"  params total {total:,}  trainable {trainable:,}  augment {config['augment']}", flush=True)
    trained = train_model(
        model,
        train_loader,
        val_loader,
        bundle.class_weights,
        device,
        epochs=1 if smoke else (epochs or config["epochs"]),
        lr=config["lr"],
        patience=1 if smoke else config["patience"],
        freeze_backbone=config["freeze_backbone"],
        n_classes=len(bundle.classes),
        max_batches=2 if smoke else max_batches,
        log=lambda message, prefix=prefix: print(f"{prefix} {message}", flush=True),
    )
    model = trained["model"]
    test_loss, y_true, y_pred, probs = run_eval(
        model, test_loader, device, bundle.class_weights, max_batches=2 if smoke else max_batches
    )
    test_metrics = classification_metrics(y_true, y_pred, probs, bundle.classes)
    test_metrics["loss"] = float(test_loss)
    record = {
        "dataset": dataset,
        "config": config_name,
        "seed": seed,
        "smoke": smoke,
        "model": config["model"],
        "augment": config["augment"],
        "freeze_backbone": config["freeze_backbone"],
        "lr": config["lr"],
        "best_epoch": trained["best_epoch"],
        "epochs_ran": trained["epochs_ran"],
        "training_seconds": trained["training_seconds"],
        "total_params": total,
        "trainable_params": trainable,
        "val": trained["best_val"],
        "test": test_metrics,
        "history": trained["history"],
        "grouping": bundle.grouping,
        "patient_independent": bundle.patient_independent,
        "leakage_note": bundle.leakage_note,
    }
    if not smoke:
        record["inference_ms"] = inference_ms(model, bundle.test_ds, device, dataset)
        _save_outputs(record, model, bundle, device, y_true, y_pred, probs)
    else:
        smoke_dir = PROJECT_ROOT / "results" / "smoke"
        smoke_dir.mkdir(parents=True, exist_ok=True)
        (smoke_dir / f"{dataset}__{config_name}__seed{seed}.json").write_text(json.dumps(_public(record), indent=2) + "\n")
    print(
        f"{prefix} test macro-F1 {test_metrics['f1_macro']:.3f}  accuracy {test_metrics['accuracy']:.3f}",
        flush=True,
    )
    return record


def _public(record: dict) -> dict:
    copied = json.loads(json.dumps(record, default=_json_default))
    return copied


def _json_default(value):
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    raise TypeError(type(value))


def _save_outputs(record, model, bundle, device, y_true, y_pred, probs) -> None:
    dataset = record["dataset"]
    config_name = record["config"]
    seed = record["seed"]
    stem = f"{dataset}__{config_name}__seed{seed}"
    METRICS.mkdir(parents=True, exist_ok=True)
    (METRICS / f"{stem}.json").write_text(json.dumps(_public(record), indent=2) + "\n")
    checkpoint = {
        "state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "classes": bundle.classes,
        "model_name": record["model"],
        "dataset": dataset,
        "config": config_name,
        "seed": seed,
        "input_size": bundle.input_size,
        "val_macro_f1": record["val"].get("macro_f1"),
    }
    ckpt_path = CHECKPOINTS / dataset / config_name / f"seed_{seed}.pt"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, ckpt_path)
    title = f"{DATASET_TITLES[dataset]} · {config_name} · seed {seed}"
    save_curves(record["history"], record["best_epoch"], PLOTS / f"{stem}_curves.png", title)
    save_confusion(record["test"]["confusion_matrix"], bundle.classes, PLOTS / f"{stem}_confusion.png", title)
    mistakes = worst_mistakes(y_true, y_pred, probs, k=5)
    save_failure_grid(
        bundle.test_ds,
        bundle.classes,
        mistakes,
        y_true,
        y_pred,
        probs,
        PLOTS / f"{stem}_failures.png",
        f"High-confidence mistakes · {title}",
    )
    shown = mistakes[:3]
    save_gradcam_grid(
        model,
        bundle.test_ds,
        bundle.classes,
        shown,
        y_true,
        device,
        GRADCAM / f"{stem}.png",
        f"Grad-CAM on mistakes · {title}",
        dataset,
    )
    if config_name == "finetune_aug":
        _maybe_promote_demo(checkpoint, record["val"].get("macro_f1") or -1)


def _maybe_promote_demo(checkpoint: dict, val_f1: float) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    dataset = checkpoint["dataset"]
    sidecar = MODELS / f"{dataset}.json"
    previous = -1.0
    if sidecar.exists():
        previous = float(json.loads(sidecar.read_text()).get("val_macro_f1") or -1)
    if val_f1 <= previous:
        return
    torch.save(checkpoint, MODELS / f"{dataset}.pt")
    sidecar.write_text(
        json.dumps(
            {
                "dataset": dataset,
                "config": checkpoint["config"],
                "seed": checkpoint["seed"],
                "val_macro_f1": val_f1,
                "classes": checkpoint["classes"],
            },
            indent=2,
        )
        + "\n"
    )


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Run the CancerAI comparative study.")
    parser.add_argument("--dataset", default="all", choices=("all", *DATASETS))
    parser.add_argument("--config", default="all", choices=("all", *CONFIGS))
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--smoke", action="store_true", help="One tiny brain run, to check that training is wired.")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--max-batches", type=int, default=None)
    args = parser.parse_args(argv)
    if args.smoke:
        started = time.perf_counter()
        run_one("brain", "custom_cnn", 42, smoke=True)
        print(f"Smoke finished in {time.perf_counter() - started:.1f}s", flush=True)
        return
    datasets = DATASETS if args.dataset == "all" else (args.dataset,)
    configs = tuple(CONFIGS) if args.config == "all" else (args.config,)
    seeds = tuple(args.seeds) if args.seeds else (42, 123, 2026)
    for dataset in datasets:
        for config_name in configs:
            for seed in seeds:
                run_one(
                    dataset,
                    config_name,
                    seed,
                    smoke=False,
                    max_batches=args.max_batches,
                    epochs=args.epochs,
                )


if __name__ == "__main__":
    main()
