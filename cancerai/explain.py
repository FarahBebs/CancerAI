"""Grad-CAM and single-image scoring for the demo and the failure figures."""

from __future__ import annotations

import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from cancerai.config import INPUT_SIZE, MEAN, STD
from cancerai.datasets import build_transform, to_pil
from cancerai.models import cam_layer, disable_inplace_relu
from cancerai.training import sync


class GradCAM:
    def __init__(self, model: nn.Module, target: nn.Module):
        self.model = model
        self.activations = None
        self.gradients = None
        self.handles = [
            target.register_forward_hook(self._save_activation),
            target.register_full_backward_hook(self._save_gradient),
        ]

    def _save_activation(self, _module, _inputs, output):
        self.activations = output

    def _save_gradient(self, _module, _grad_in, grad_out):
        self.gradients = grad_out[0]

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()
        self.handles = []

    def __call__(self, batch: torch.Tensor, class_idx: int) -> np.ndarray:
        self.model.eval()
        self.model.zero_grad(set_to_none=True)
        images = batch.detach().requires_grad_(True)
        with torch.enable_grad():
            logits = self.model(images)
            score = logits[0, int(class_idx)]
            score.backward()
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM did not receive activations.")
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        heat = torch.relu((weights * self.activations).sum(dim=1, keepdim=True))
        heat = F.interpolate(heat, size=images.shape[-2:], mode="bilinear", align_corners=False)
        heat = heat[0, 0]
        heat = heat - heat.min()
        heat = heat / (heat.max() + 1e-8)
        result = heat.detach().cpu().numpy()
        self.activations = None
        self.gradients = None
        return result


def prepare_gradcam(model: nn.Module) -> GradCAM:
    model.eval()
    disable_inplace_relu(model)
    return GradCAM(model, cam_layer(model))


def denormalize(tensor: torch.Tensor) -> np.ndarray:
    mean = np.asarray(MEAN, dtype=np.float32).reshape(3, 1, 1)
    std = np.asarray(STD, dtype=np.float32).reshape(3, 1, 1)
    array = tensor.detach().cpu().numpy()
    image = array * std + mean
    return np.clip(image, 0, 1).transpose(1, 2, 0)


def overlay_cam(image_01, heat) -> Image.Image:
    image = np.clip(np.asarray(image_01), 0, 1)
    heat_values = np.asarray(heat, dtype=np.float32)
    if heat_values.shape != image.shape[:2]:
        resized = Image.fromarray((np.clip(heat_values, 0, 1) * 255).astype(np.uint8))
        resized = resized.resize((image.shape[1], image.shape[0]), Image.BILINEAR)
        heat_values = np.asarray(resized).astype(np.float32) / 255.0
    color = cm.jet(heat_values)[..., :3]
    mixed = np.clip(0.58 * image + 0.42 * color, 0, 1)
    return Image.fromarray((mixed * 255).astype(np.uint8))


def predict_pil(model, image, classes, device, gradcam, input_size=INPUT_SIZE, dataset: str = "brain") -> dict:
    picture = to_pil(image)
    batch = build_transform(dataset, train=False, augment=False, input_size=input_size)(picture).unsqueeze(0).to(device)
    model.eval()
    sync(device)
    started = time.perf_counter()
    with torch.no_grad():
        logits = model(batch)
    sync(device)
    elapsed = time.perf_counter() - started
    probs = torch.softmax(logits, dim=1)[0].detach().cpu().numpy()
    pred = int(np.argmax(probs))
    overlay = None
    if gradcam is not None:
        heat = gradcam(batch, pred)
        overlay = overlay_cam(denormalize(batch[0]), heat)
    return {"pred": pred, "probs": probs, "seconds": elapsed, "overlay": overlay, "classes": classes}


def save_failure_grid(dataset, classes, indices, y_true, y_pred, probs, path, title) -> None:
    if not indices:
        return
    fig, axes = plt.subplots(1, len(indices), figsize=(2.8 * len(indices), 3.6))
    if len(indices) == 1:
        axes = [axes]
    for axis, index in zip(axes, indices):
        image = dataset.raw(index) if hasattr(dataset, "raw") else None
        if image is None:
            continue
        axis.imshow(image)
        pred = int(y_pred[index])
        axis.set_title(
            f"True: {classes[int(y_true[index])]}\nPred: {classes[pred]}\n{probs[index, pred] * 100:.0f}%",
            color="#b42318",
            fontsize=8,
        )
        axis.set_xticks([])
        axis.set_yticks([])
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    path = Path_fix(path)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def Path_fix(path):
    from pathlib import Path

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_gradcam_grid(model, dataset, classes, indices, y_true, device, path, title, dataset_name: str) -> None:
    if not indices:
        return
    engine = prepare_gradcam(model)
    transform = build_transform(dataset_name, train=False, augment=False)
    fig, axes = plt.subplots(2, len(indices), figsize=(2.7 * len(indices), 5.6))
    if len(indices) == 1:
        axes = np.array([[axes[0]], [axes[1]]])
    try:
        for col, index in enumerate(indices):
            image = dataset.raw(index)
            batch = transform(image).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(batch)
                pred = int(logits.argmax(dim=1).item())
                confidence = float(torch.softmax(logits, dim=1)[0, pred].item())
            heat = engine(batch, pred)
            shown = denormalize(batch[0])
            true_index = int(y_true[index])
            color = "#1b7f3a" if pred == true_index else "#b42318"
            axes[0, col].imshow(shown)
            axes[0, col].set_title(f"True: {classes[true_index]}", fontsize=8)
            axes[1, col].imshow(np.asarray(overlay_cam(shown, heat)))
            axes[1, col].set_title(f"Pred: {classes[pred]}\n{confidence * 100:.0f}%", color=color, fontsize=8)
            for axis in (axes[0, col], axes[1, col]):
                axis.set_xticks([])
                axis.set_yticks([])
        fig.suptitle(title, fontsize=12)
        fig.tight_layout()
        Path_fix(path)
        fig.savefig(path, dpi=140, bbox_inches="tight")
    finally:
        engine.close()
        plt.close(fig)
