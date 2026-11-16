"""Shared constants for the BIL458 comparative study."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_SIZE = 224
SPLIT_SEED = 42
SEEDS = (42, 123, 2026)
BATCH_SIZE = 32
WEIGHT_DECAY = 1e-4
DROPOUT = 0.3
MIN_DELTA = 0.001
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".heif"}

DATASETS = ("brain", "breast", "skin", "lung")

DATASET_TITLES = {
    "brain": "Brain MRI",
    "breast": "Breast histopathology",
    "skin": "Skin lesion",
    "lung": "Lung CT",
}

DATASET_INFO = {
    "brain": {
        "name": "Brain Tumor MRI (Nickparvar; figshare, SARTAJ, Br35H)",
        "url": "https://doi.org/10.5281/zenodo.12735702",
        "license": "CC BY 4.0",
        "task": "Glioma, meningioma, pituitary tumor, or no tumor",
    },
    "breast": {
        "name": "BreaKHis",
        "url": "https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-breakhis/",
        "license": "UFPR research release",
        "task": "Eight histopathological subtypes",
    },
    "skin": {
        "name": "DermaMNIST 224, derived from HAM10000",
        "url": "https://doi.org/10.7910/DVN/DBW86T",
        "license": "CC BY-NC 4.0 (HAM10000)",
        "task": "Seven skin-lesion categories",
    },
    "lung": {
        "name": "IQ-OTH/NCCD lung CT slices",
        "url": "https://www.kaggle.com/datasets/hamdallak/the-iqothnccd-lung-cancer-dataset",
        "license": "Public teaching dataset",
        "task": "Normal, benign, or malignant slice",
    },
}

BRAIN_ORDER = ["glioma", "meningioma", "pituitary", "notumor"]
BRAIN_DISPLAY = {
    "glioma": "Glioma",
    "meningioma": "Meningioma",
    "pituitary": "Pituitary tumor",
    "notumor": "No tumor",
}
BRAIN_ALIASES = {
    "glioma": "glioma",
    "gliomatumor": "glioma",
    "meningioma": "meningioma",
    "meningiomatumor": "meningioma",
    "pituitary": "pituitary",
    "pituitarytumor": "pituitary",
    "pituitarytumour": "pituitary",
    "notumor": "notumor",
    "notumour": "notumor",
    "healthy": "notumor",
    "normal": "notumor",
}

BREAST_CLASS = {
    "adenosis": "Adenosis",
    "fibroadenoma": "Fibroadenoma",
    "phyllodestumor": "Phyllodes tumor",
    "tubularadenoma": "Tubular adenoma",
    "ductalcarcinoma": "Ductal carcinoma",
    "lobularcarcinoma": "Lobular carcinoma",
    "mucinouscarcinoma": "Mucinous carcinoma",
    "papillarycarcinoma": "Papillary carcinoma",
}
BREAST_ORDER = [
    "Adenosis",
    "Fibroadenoma",
    "Phyllodes tumor",
    "Tubular adenoma",
    "Ductal carcinoma",
    "Lobular carcinoma",
    "Mucinous carcinoma",
    "Papillary carcinoma",
]
BREAST_BENIGN = {"Adenosis", "Fibroadenoma", "Phyllodes tumor", "Tubular adenoma"}

LUNG_CLASS = {
    "normal": "Normal",
    "normalcases": "Normal",
    "benign": "Benign",
    "benigncases": "Benign",
    "bengin": "Benign",
    "bengincases": "Benign",
    "malignant": "Malignant",
    "malignantcases": "Malignant",
}
LUNG_ORDER = ["Normal", "Benign", "Malignant"]

# DermaMNIST names vary slightly by release. Matching is done on the folded label.
SKIN_CANCER_RELATED_KEYS = {
    "actinickeratoses",
    "actinickeratosesandintraepithelialcarcinoma",
    "basalcellcarcinoma",
    "melanoma",
    "akiec",
    "bcc",
    "mel",
}


def fold_text(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def group_of(dataset: str, class_name: str) -> str:
    """Collapse a category to the coarser label used only in the demo.

    This is a lookup on the predicted category. It is not a second trained model.
    A tumor label is not reported as cancer.
    """
    if dataset == "brain":
        return "No tumor" if class_name == "No tumor" else "Tumor"
    if dataset == "breast":
        return "Benign" if class_name in BREAST_BENIGN else "Malignant"
    if dataset == "skin":
        if fold_text(class_name) in SKIN_CANCER_RELATED_KEYS:
            return "Cancer-related"
        return "Not cancer-related"
    if dataset == "lung":
        return "Malignant" if class_name == "Malignant" else "Not malignant"
    raise KeyError(dataset)


def torch_home() -> Path:
    env = os.environ.get("TORCH_HOME")
    if env:
        return Path(env).expanduser()
    sibling = ROOT.parent / "Deep Learning" / "Homework 2 - CancerAI" / "data" / "torch"
    if sibling.exists():
        return sibling
    return ROOT / "data" / "torch"


os.environ.setdefault("TORCH_HOME", str(torch_home()))
