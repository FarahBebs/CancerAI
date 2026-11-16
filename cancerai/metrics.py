"""Metrics and figures shared by every dataset.

Macro-F1 is the primary score:

    F1_macro = (1 / C) * sum_c  2 P_c R_c / (P_c + R_c)

ROC-AUC, when it can be computed, is one-vs-rest with macro averaging.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)

plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"


def classification_metrics(y_true, y_pred, probs, classes) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    probs = np.asarray(probs)
    labels = list(range(len(classes)))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)) if len(y_true) else 0.0,
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "per_class": {
            classes[i]: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in labels
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "report": classification_report(
            y_true, y_pred, labels=labels, target_names=classes, digits=4, zero_division=0
        ),
    }
    metrics["roc_auc_macro_ovr"] = _roc_auc(y_true, probs)
    return metrics


def _roc_auc(y_true, probs):
    try:
        if probs.ndim != 2 or len(np.unique(y_true)) < 2:
            return None
        if probs.shape[1] == 2:
            return float(roc_auc_score(y_true, probs[:, 1]))
        return float(roc_auc_score(y_true, probs, multi_class="ovr", average="macro"))
    except ValueError:
        return None


def mean_std(values) -> tuple[float, float]:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return float("nan"), float("nan")
    std = float(array.std(ddof=1)) if array.size > 1 else 0.0
    return float(array.mean()), std


def format_mean_std(mean: float, std: float, digits: int = 3) -> str:
    if not np.isfinite(mean):
        return "—"
    return f"{mean:.{digits}f} ± {std:.{digits}f}"


def worst_mistakes(y_true, y_pred, probs, k: int = 5) -> list[int]:
    wrong = [i for i in range(len(y_true)) if int(y_true[i]) != int(y_pred[i])]
    wrong.sort(key=lambda i: -float(probs[i, int(y_pred[i])]))
    return wrong[:k]


def _save(fig, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def save_curves(history, best_epoch, path, title) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4))
    epochs = history["epoch"]
    axes[0].plot(epochs, history["train_loss"], label="Train")
    axes[0].plot(epochs, history["val_loss"], label="Validation")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Weighted cross-entropy")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[1].plot(epochs, history["train_acc"], label="Train accuracy")
    axes[1].plot(epochs, history["val_macro_f1"], label="Validation macro-F1")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Accuracy and macro-F1")
    axes[1].legend()
    for axis in axes:
        if best_epoch:
            axis.axvline(best_epoch, color="gray", ls="--", lw=1)
        axis.grid(True, alpha=0.3)
    fig.suptitle(title)
    fig.tight_layout()
    _save(fig, path)


def save_confusion(matrix, classes, path, title) -> None:
    counts = np.asarray(matrix, dtype=float)
    if counts.size == 0:
        return
    labels = list(classes)
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    image = ax.imshow(counts, cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    thresh = counts.max() * 0.62 if counts.max() > 0 else 0
    for row in range(counts.shape[0]):
        for col in range(counts.shape[1]):
            color = "white" if counts[row, col] > thresh else "black"
            ax.text(col, row, f"{int(counts[row, col])}", ha="center", va="center", color=color, fontsize=8)
    fig.tight_layout()
    _save(fig, path)


def save_comparison(table: dict, path, title) -> None:
    """table[dataset][config] = macro-F1 mean."""
    datasets = list(table)
    if not datasets:
        return
    configs = list(next(iter(table.values())))
    x = np.arange(len(datasets))
    width = 0.8 / max(len(configs), 1)
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    for index, config in enumerate(configs):
        values = [table[name].get(config, np.nan) for name in datasets]
        ax.bar(x + (index - (len(configs) - 1) / 2) * width, values, width, label=config)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Test macro-F1")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    _save(fig, path)
