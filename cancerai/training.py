"""One training loop for every configuration.

Model selection uses validation macro-F1. The test set is not read here.
"""

from __future__ import annotations

import random
import time

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader

from cancerai.config import BATCH_SIZE, MIN_DELTA, WEIGHT_DECAY
from cancerai.models import apply_train_mode


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps" and hasattr(torch, "mps"):
        torch.mps.synchronize()


def make_loader(dataset, batch_size, shuffle, seed, device) -> DataLoader:
    generator = None
    if shuffle:
        generator = torch.Generator()
        generator.manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=device.type == "cuda",
        generator=generator,
    )


def weighted_cross_entropy(logits, target, weight):
    """Batch mean of L = -sum_c w_c y_c log yhat_c.

    y is one-hot, so only the true class remains. This is the weighted
    cross-entropy written in the report. It is not PyTorch's default
    `CrossEntropyLoss(weight=...)`, which also divides by the sum of the
    weights in the batch.
    """
    log_probs = torch.log_softmax(logits, dim=1)
    picked = log_probs.gather(1, target.view(-1, 1)).squeeze(1)
    return -(weight[target] * picked).mean()


def run_eval(model, loader, device, class_weights=None, max_batches=None):
    model.eval()
    total_loss = 0.0
    seen = 0
    y_true = []
    y_pred = []
    chunks = []
    with torch.no_grad():
        for batch_index, (images, labels) in enumerate(loader):
            if max_batches is not None and batch_index >= max_batches:
                break
            images = images.to(device)
            labels = labels.view(-1).long().to(device)
            logits = model(images)
            if class_weights is None:
                weights = torch.ones(logits.shape[1], device=device)
            else:
                weights = class_weights.to(device)
            loss = weighted_cross_entropy(logits, labels, weights)
            total_loss += float(loss.item()) * labels.size(0)
            seen += labels.size(0)
            y_true.extend(labels.detach().cpu().tolist())
            y_pred.extend(logits.argmax(dim=1).detach().cpu().tolist())
            chunks.append(torch.softmax(logits, dim=1).detach().cpu())
    probs = torch.cat(chunks, dim=0).numpy() if chunks else np.zeros((0, 0), dtype=np.float32)
    return total_loss / max(seen, 1), y_true, y_pred, probs


def train_model(
    model,
    train_loader,
    val_loader,
    class_weights,
    device,
    epochs,
    lr,
    patience,
    freeze_backbone,
    n_classes,
    max_batches=None,
    weight_decay=WEIGHT_DECAY,
    log=print,
):
    model.to(device)
    weights = class_weights.to(device)
    params = [param for param in model.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1), eta_min=1e-6)
    history = {key: [] for key in ("epoch", "lr", "train_loss", "train_acc", "val_loss", "val_acc", "val_macro_f1")}
    best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    best_f1 = -1.0
    best_epoch = 0
    best_val = {}
    patience_left = patience
    started = time.perf_counter()
    labels = list(range(n_classes))

    for epoch in range(1, epochs + 1):
        current_lr = optimizer.param_groups[0]["lr"]
        apply_train_mode(model, freeze_backbone)
        total_loss = 0.0
        correct = 0
        seen = 0
        for batch_index, (images, targets) in enumerate(train_loader):
            if max_batches is not None and batch_index >= max_batches:
                break
            images = images.to(device)
            targets = targets.view(-1).long().to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = weighted_cross_entropy(logits, targets, weights)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * targets.size(0)
            correct += int((logits.argmax(dim=1) == targets).sum().item())
            seen += targets.size(0)
        train_loss = total_loss / max(seen, 1)
        train_acc = correct / max(seen, 1)
        val_loss, y_true, y_pred, _probs = run_eval(
            model, val_loader, device, class_weights, max_batches=max_batches
        )
        val_acc = float(accuracy_score(y_true, y_pred)) if y_true else 0.0
        val_f1 = (
            float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)) if y_true else 0.0
        )
        improved = best_epoch == 0 or val_f1 > best_f1 + MIN_DELTA
        if improved:
            best_f1 = val_f1
            best_epoch = epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            best_val = {
                "loss": float(val_loss),
                "accuracy": val_acc,
                "macro_f1": val_f1,
                "precision_macro": float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
                "recall_macro": float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
            }
            patience_left = patience
        else:
            patience_left -= 1
        history["epoch"].append(epoch)
        history["lr"].append(float(current_lr))
        history["train_loss"].append(float(train_loss))
        history["train_acc"].append(float(train_acc))
        history["val_loss"].append(float(val_loss))
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_f1)
        marker = " saved" if improved else ""
        log(
            f"epoch {epoch}/{epochs}  lr {current_lr:.2e}  "
            f"train loss {train_loss:.4f} acc {train_acc:.3f}  "
            f"val loss {val_loss:.4f} acc {val_acc:.3f} macro-F1 {val_f1:.3f}{marker}"
        )
        scheduler.step()
        if patience_left <= 0:
            log(f"early stop at epoch {epoch}")
            break

    model.load_state_dict(best_state)
    model.to(device)
    return {
        "model": model,
        "history": history,
        "best_epoch": best_epoch,
        "best_val": best_val,
        "training_seconds": time.perf_counter() - started,
        "epochs_ran": len(history["epoch"]),
    }


def inference_milliseconds(model, dataset, device, dataset_name: str, repeats: int = 20) -> float:
    from cancerai.datasets import build_transform

    model.eval()
    image = dataset.raw(0)
    batch = build_transform(dataset_name, train=False, augment=False)(image).unsqueeze(0).to(device)
    with torch.no_grad():
        for _ in range(3):
            model(batch)
        sync(device)
        times = []
        for _ in range(repeats):
            sync(device)
            started = time.perf_counter()
            model(batch)
            sync(device)
            times.append(time.perf_counter() - started)
    times.sort()
    return float(times[len(times) // 2]) * 1000.0


def default_batch_size() -> int:
    return BATCH_SIZE
