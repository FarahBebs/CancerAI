"""Gradio demonstration for the four category models.

The page shows the dataset category, the coarser group that category belongs to,
and a Grad-CAM map. The group is a collapse of the category probabilities.
It is not a second network, and it is not a diagnosis.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
import numpy as np
import torch

from cancerai.config import DATASET_TITLES, DATASETS, ROOT, group_of
from cancerai.explain import predict_pil, prepare_gradcam
from cancerai.models import build_model, disable_inplace_relu
from cancerai.training import get_device

DISCLAIMER = (
    "This is a course project for comparing image classifiers. "
    "A score is how strongly an image matches a training folder. "
    "It is not a diagnosis, not a risk estimate, and not something to use for a health decision. "
    "A tumor is not the same thing as cancer. "
    "Brain labels do not say benign or malignant. "
    "Actinic keratoses are precancerous and are grouped here as cancer-related only because that is the dataset convention. "
    "The models are not validated for clinical use."
)
NOTES = {
    "brain": "Expect a brain MRI slice from the same kind of collection as the training set. A photo of a person is not an MRI. The source filenames have no patient id, so the published score can be optimistic for a new person.",
    "breast": "Expect a microscope image of breast tumor tissue, like BreakHis. The eight subtypes include benign tumors. Benign is not called cancer.",
    "skin": "Expect a dermoscopic lesion image like HAM10000. An ordinary phone photo has different lighting and scale. Nevi dominate the dataset, so accuracy alone is a poor summary.",
    "lung": "Expect a chest CT slice like IQ-OTH/NCCD. Benign and normal are not called cancer. The public filenames do not identify the patient, so slices from one scan may have been seen in training.",
}
CACHE = {}


def model_path(dataset: str) -> Path:
    return ROOT / "models" / f"{dataset}.pt"


def get_model(dataset: str):
    if dataset in CACHE:
        return CACHE[dataset]
    path = model_path(dataset)
    if not path.exists():
        return None
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    device = get_device()
    model = build_model(checkpoint["model_name"], len(checkpoint["classes"]), freeze_backbone=False, pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device)
    model.eval()
    disable_inplace_relu(model)
    gradcam = prepare_gradcam(model)
    CACHE[dataset] = (model, checkpoint, gradcam, device)
    return CACHE[dataset]


def collapsed_group(dataset: str, classes, probs) -> tuple[str, float]:
    totals = {}
    for index, name in enumerate(classes):
        group = group_of(dataset, name)
        totals[group] = totals.get(group, 0.0) + float(probs[index])
    group = max(totals, key=totals.get)
    return group, totals[group]


def analyze(dataset_title, image):
    dataset = next((key for key in DATASETS if DATASET_TITLES[key] == dataset_title), None)
    if dataset is None:
        return "Choose an image type.", None
    if image is None:
        return "Upload an image first.", None
    loaded = get_model(dataset)
    if loaded is None:
        return (
            f"No {dataset_title} checkpoint yet. The demo uses the fine-tuned ResNet18 "
            f"with the best validation macro-F1.\n"
            f"From this folder: python -m experiments.run_experiments --dataset {dataset} --config finetune_aug",
            None,
        )
    model, checkpoint, gradcam, device = loaded
    classes = checkpoint["classes"]
    try:
        result = predict_pil(
            model,
            image,
            classes,
            device,
            gradcam,
            int(checkpoint.get("input_size", 224)),
            dataset=dataset,
        )
    except Exception as exc:
        return f"The model could not read this image ({type(exc).__name__}: {exc}).", None
    pred = result["pred"]
    category = classes[pred]
    group, group_score = collapsed_group(dataset, classes, result["probs"])
    ranked = sorted(
        ((classes[i], float(result["probs"][i])) for i in range(len(classes))),
        key=lambda item: -item[1],
    )
    lines = [
        "1. Category",
        f"{category} ({result['probs'][pred] * 100:.1f}%)",
        "",
        "2. Broader group",
        f"{group} ({group_score * 100:.1f}% of the category scores)",
        "This group is the category scores added together. It is not a separately trained model.",
        "",
        "Category scores:",
    ]
    lines.extend(f"- {name}: {score * 100:.1f}%" for name, score in ranked)
    top = float(result["probs"][pred])
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    if top < 0.70 or top - second < 0.15:
        lines.extend(["", "The top score is modest, or another category is close. Treat this example as uncertain."])
    lines.extend(
        [
            "",
            NOTES[dataset],
            "",
            DISCLAIMER,
            "",
            f"Checkpoint: {checkpoint.get('config', 'finetune_aug')}, seed {checkpoint.get('seed', '—')}.",
            f"Forward pass: {result['seconds'] * 1000:.1f} ms.",
            "Grad-CAM shows which spatial features moved the winning logit. It is not a tumor outline.",
        ]
    )
    return "\n".join(lines), result["overlay"]


def opening_state():
    """Open on a finished example so a new visitor sees the same filled page."""
    name = "breast"
    path = ROOT / "examples" / f"{name}.jpg"
    title = DATASET_TITLES[name]
    if not path.exists():
        return DATASET_TITLES["brain"], None, "", None
    from PIL import Image

    picture = Image.open(path).convert("RGB")
    text, heat = analyze(title, picture)
    return title, picture, text, heat


def build_demo():
    title, picture, result_text, heat_image = opening_state()
    with gr.Blocks(title="CancerAI") as demo:
        gr.Markdown("# CancerAI")
        gr.Markdown(
            "Four separate classifiers for brain MRI, breast histopathology, skin lesions, and lung CT. "
            "Pick the modality that matches the image. The page reports the dataset category and the coarser group that category belongs to."
        )
        gr.Markdown(DISCLAIMER)
        with gr.Row():
            with gr.Column():
                dataset = gr.Radio(
                    [DATASET_TITLES[name] for name in DATASETS],
                    value=title,
                    label="Image type",
                )
                image = gr.Image(type="pil", label="Image", height=320, value=picture)
                button = gr.Button("Run model", variant="primary")
            with gr.Column():
                text = gr.Textbox(label="Result", lines=34, value=result_text)
                heat = gr.Image(label="Grad-CAM for the predicted category", height=320, value=heat_image)
        example_rows = []
        for name in DATASETS:
            example_path = ROOT / "examples" / f"{name}.jpg"
            if example_path.exists():
                example_rows.append([DATASET_TITLES[name], str(example_path)])
        if example_rows:
            gr.Examples(examples=example_rows, inputs=[dataset, image], label="Try an example")
        button.click(analyze, inputs=[dataset, image], outputs=[text, heat])
    return demo


if __name__ == "__main__":
    missing = [DATASET_TITLES[name] for name in DATASETS if not model_path(name).exists()]
    if missing:
        print("Still missing checkpoints:", ", ".join(missing))
        print("Train the demo models with: python -m experiments.run_experiments --config finetune_aug")
    public = os.environ.get("CANCERAI_SHARE", "1") != "0"
    build_demo().launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=public,
        allowed_paths=[str(ROOT), str(ROOT / "examples")],
    )
