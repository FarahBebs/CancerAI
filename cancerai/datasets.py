"""Dataset discovery, fixed splits, and modality-specific preprocessing.

The train / validation / test membership is written once to results/splits.
Later runs reload that file. Training seeds do not reshuffle the split.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from torchvision import transforms as T

from cancerai.config import (
    BRAIN_ALIASES,
    BRAIN_DISPLAY,
    BRAIN_ORDER,
    BREAST_CLASS,
    BREAST_ORDER,
    DATASETS,
    IMAGE_EXTS,
    INPUT_SIZE,
    LUNG_CLASS,
    LUNG_ORDER,
    MEAN,
    ROOT,
    SPLIT_SEED,
    STD,
    fold_text,
)

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except Exception:
    pass

SPLIT_DIR = ROOT / "results" / "splits"


@dataclass
class Bundle:
    name: str
    classes: list[str]
    train_ds: Dataset
    val_ds: Dataset
    test_ds: Dataset
    class_weights: torch.Tensor
    split_counts: dict
    grouping: str
    patient_independent: bool
    leakage_note: str
    input_size: int = INPUT_SIZE


class ImageListDataset(Dataset):
    def __init__(self, rows, transform, data_root: Path):
        self.rows = list(rows)
        self.transform = transform
        self.data_root = Path(data_root)

    def __len__(self):
        return len(self.rows)

    def raw(self, index: int) -> Image.Image:
        path = resolve_image(self.rows[index]["path"], self.data_root)
        with Image.open(path) as opened:
            return opened.convert("RGB")

    def __getitem__(self, index):
        image = self.raw(index)
        if self.transform is not None:
            image = self.transform(image)
        return image, int(self.rows[index]["label"])


class SkinDataset(Dataset):
    def __init__(self, base, transform):
        self.base = base
        self.transform = transform

    def __len__(self):
        return len(self.base)

    def raw(self, index: int) -> Image.Image:
        image, _label = self.base[index]
        return to_pil(image)

    def __getitem__(self, index):
        image = self.raw(index)
        _image, label = self.base[index]
        label = int(np.asarray(label).reshape(-1)[0])
        if self.transform is not None:
            image = self.transform(image)
        return image, label


def to_pil(image) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    array = np.asarray(image)
    if array.ndim == 3 and array.shape[0] in (1, 3) and array.shape[-1] not in (1, 3):
        array = np.transpose(array, (1, 2, 0))
    if array.dtype != np.uint8:
        scale = 255.0 if array.size and float(np.max(array)) <= 1.0 else 1.0
        array = np.clip(array * scale, 0, 255).astype(np.uint8)
    if array.ndim == 2:
        array = np.stack([array, array, array], axis=-1)
    return Image.fromarray(array).convert("RGB")


def resolve_data_root() -> Path:
    env = os.environ.get("CANCERAI_DATA")
    if env:
        root = Path(env).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"CANCERAI_DATA does not exist: {root}")
        return root
    local = ROOT / "data"
    if _has_any_dataset(local):
        return local
    sibling = ROOT.parent / "Deep Learning" / "Homework 2 - CancerAI" / "data"
    if sibling.exists() and _has_any_dataset(sibling):
        return sibling.resolve()
    return local


def _has_any_dataset(root: Path) -> bool:
    names = (
        "brain",
        "brain_mri",
        "breakhis",
        "breast_breakhis",
        "medmnist",
        "skin_dermamnist",
        "iqoth",
        "lung_iqoth",
    )
    return any((root / name).exists() for name in names)


def _first_existing(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def build_transform(dataset: str, train: bool, augment: bool, input_size: int = INPUT_SIZE):
    """Resize to 224 and apply ImageNet normalization for every model.

    Augmentation is training-only and depends on the modality. Horizontal flip
    is used for histopathology and dermoscopy. It is omitted for MRI and CT
    because left and right are anatomical. Hue shifts are omitted: stain and
    dermoscopic colour carry category information.
    """
    if not train or not augment:
        return T.Compose(
            [
                T.Resize((input_size, input_size)),
                T.ToTensor(),
                T.Normalize(MEAN, STD),
            ]
        )
    ops = [
        T.Resize((input_size + 32, input_size + 32)),
        T.RandomResizedCrop(input_size, scale=(0.85, 1.0)),
    ]
    if dataset == "breast":
        ops.extend(
            [
                T.RandomHorizontalFlip(),
                T.RandomVerticalFlip(),
                T.RandomRotation(20),
                T.ColorJitter(brightness=0.1, contrast=0.1),
            ]
        )
    elif dataset == "skin":
        ops.extend(
            [
                T.RandomHorizontalFlip(),
                T.RandomRotation(15),
                T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
            ]
        )
    elif dataset == "brain":
        ops.append(T.RandomRotation(10))
    elif dataset == "lung":
        ops.append(T.RandomRotation(8))
    else:
        raise KeyError(dataset)
    ops.extend([T.ToTensor(), T.Normalize(MEAN, STD)])
    return T.Compose(ops)


def class_weights(labels, n_classes) -> torch.Tensor:
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=n_classes).astype(np.float64)
    weights = counts.sum() / (n_classes * np.maximum(counts, 1.0))
    weights = weights / max(float(weights.mean()), 1e-8)
    return torch.tensor(weights, dtype=torch.float32)


def _count_rows(rows, classes) -> dict:
    labels = [int(row["label"]) for row in rows]
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=len(classes))
    return {classes[i]: int(counts[i]) for i in range(len(classes))}


def _walk_files(root: Path):
    root = Path(root)
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name != "__MACOSX" and not name.startswith(".")]
        path = Path(dirpath)
        if "__MACOSX" in path.parts:
            continue
        for filename in filenames:
            if filename.startswith("."):
                continue
            if Path(filename).suffix.lower() not in IMAGE_EXTS:
                continue
            yield path / filename


def _relative(path: Path, data_root: Path) -> str:
    try:
        return path.resolve().relative_to(data_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_image(path_str: str, data_root: Path) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return Path(data_root) / path


def _stratified_cut(rows, test_size, seed):
    labels = [int(row["label"]) for row in rows]
    indices = np.arange(len(rows))
    try:
        left, right = train_test_split(
            indices, test_size=test_size, random_state=seed, stratify=labels
        )
    except ValueError:
        left, right = train_test_split(indices, test_size=test_size, random_state=seed)
    return [rows[i] for i in left], [rows[i] for i in right]


def split_patients(records, classes, test_fraction=0.15, val_fraction=0.15, seed=SPLIT_SEED):
    """Keep every image from one patient in one split.

    records are dicts with path, label, group, and the class index already set.
    A class with fewer than three patients stays in training.
    """
    grouped = {}
    for row in records:
        slot = grouped.setdefault(row["group"], {"label": row["label"], "rows": []})
        if slot["label"] != row["label"]:
            raise RuntimeError(f"Patient {row['group']} has more than one class.")
        slot["rows"].append(row)
    by_class = {index: [] for index in range(len(classes))}
    for patient_id in sorted(grouped):
        by_class[grouped[patient_id]["label"]].append(patient_id)
    rng = np.random.RandomState(seed)
    buckets = {"train": [], "val": [], "test": []}
    for label in range(len(classes)):
        members = by_class[label][:]
        rng.shuffle(members)
        count = len(members)
        if count == 0:
            continue
        if count < 3:
            buckets["train"].extend(members)
            continue
        n_test = max(1, int(round(count * test_fraction)))
        n_val = max(1, int(round(count * val_fraction)))
        while n_test + n_val >= count:
            if n_val > 1:
                n_val -= 1
            elif n_test > 1:
                n_test -= 1
            else:
                break
        buckets["test"].extend(members[:n_test])
        buckets["val"].extend(members[n_test : n_test + n_val])
        buckets["train"].extend(members[n_test + n_val :])
    splits = {}
    for name, patient_ids in buckets.items():
        rows = []
        for patient_id in patient_ids:
            rows.extend(grouped[patient_id]["rows"])
        rows.sort(key=lambda row: row["path"])
        splits[name] = rows
    patient_counts = {name: len(ids) for name, ids in buckets.items()}
    return splits, patient_counts


def assert_disjoint(manifest: dict) -> None:
    paths = {}
    groups = {}
    for split in ("train", "val", "test"):
        for row in manifest.get(split) or []:
            path = row["path"]
            if path in paths:
                raise RuntimeError(f"{path} is in both {paths[path]} and {split}.")
            paths[path] = split
            group = row.get("group")
            if not group:
                continue
            if group in groups and groups[group] != split:
                raise RuntimeError(f"Group {group} is in both {groups[group]} and {split}.")
            groups[group] = split


def _split_path(dataset: str) -> Path:
    return SPLIT_DIR / f"{dataset}.json"


def load_manifest(dataset: str) -> dict | None:
    path = _split_path(dataset)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_manifest(manifest: dict) -> Path:
    path = _split_path(manifest["dataset"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def _brain_records(data_root: Path) -> tuple[list[dict], list[str], str]:
    folder = _first_existing(data_root, ("brain", "brain_mri"))
    if folder is None:
        raise FileNotFoundError(
            "Brain MRI images were not found. See data/README.md. "
            "Source: https://doi.org/10.5281/zenodo.12735702"
        )
    found = []
    for path in _walk_files(folder):
        key = fold_text(path.parent.name)
        class_key = BRAIN_ALIASES.get(key)
        if class_key is None:
            continue
        parent = fold_text(path.parent.parent.name)
        if parent in {"training", "train"}:
            hint = "train"
        elif parent in {"testing", "test"}:
            hint = "test"
        elif parent in {"validation", "val"}:
            hint = "val"
        else:
            hint = "all"
        found.append((path, class_key, hint))
    if not found:
        raise RuntimeError(f"No class folders were found under {folder}.")
    present = [name for name in BRAIN_ORDER if any(item[1] == name for item in found)]
    classes = [BRAIN_DISPLAY[name] for name in present]
    name_to_index = {name: index for index, name in enumerate(present)}
    rows = []
    for path, class_key, hint in found:
        rows.append(
            {
                "path": _relative(path, data_root),
                "label": name_to_index[class_key],
                "group": None,
                "hint": hint,
                "stem": path.stem,
            }
        )
    note = (
        "Filenames are sequential slice indexes (for example Tr-gl_0505), not patient or scan ids. "
        "The official Testing folder is held out and 15% of the official Training folder is validation. "
        "Slices from the same scan can still sit in more than one split. "
        "These scores are not a patient-level result."
    )
    return rows, classes, note


def _breast_records(data_root: Path) -> tuple[list[dict], list[str]]:
    folder = _first_existing(data_root, ("breakhis", "breast_breakhis"))
    if folder is None:
        raise FileNotFoundError(
            "BreakHis images were not found. See data/README.md. "
            "Source: https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-breakhis/"
        )
    magnifications = {"40x", "100x", "200x", "400x"}
    found = []
    for path in _walk_files(folder):
        if fold_text(path.parent.name) not in magnifications:
            continue
        patient_dir = path.parent.parent
        class_dir = patient_dir.parent
        class_name = BREAST_CLASS.get(fold_text(class_dir.name))
        if class_name is None:
            continue
        found.append((path, class_name, patient_dir.name))
    if not found:
        raise RuntimeError(f"No BreakHis patient folders were found under {folder}.")
    classes = [name for name in BREAST_ORDER if any(item[1] == name for item in found)]
    name_to_index = {name: index for index, name in enumerate(classes)}
    rows = [
        {
            "path": _relative(path, data_root),
            "label": name_to_index[class_name],
            "group": patient_id,
        }
        for path, class_name, patient_id in found
    ]
    rows.sort(key=lambda row: row["path"])
    return rows, classes


def _lung_records(data_root: Path) -> tuple[list[dict], list[str], str]:
    folder = _first_existing(data_root, ("iqoth", "lung_iqoth"))
    if folder is None:
        raise FileNotFoundError(
            "IQ-OTH/NCCD images were not found. See data/README.md."
        )
    found = []
    for path in _walk_files(folder):
        class_name = LUNG_CLASS.get(fold_text(path.parent.name))
        if class_name is None:
            continue
        found.append((path, class_name))
    if not found:
        raise RuntimeError(f"No lung CT class folders were found under {folder}.")
    classes = [name for name in LUNG_ORDER if any(item[1] == name for item in found)]
    name_to_index = {name: index for index, name in enumerate(classes)}
    rows = [
        {
            "path": _relative(path, data_root),
            "label": name_to_index[class_name],
            "group": None,
        }
        for path, class_name in found
    ]
    rows.sort(key=lambda row: row["path"])
    note = (
        "The number in each filename, such as 'Bengin case (85)', is unique inside its class "
        "and runs from 1 to the class count. It is an image index, not a patient id shared by several slices. "
        "The public folders do not reconstruct the scan. "
        "The split is stratified by image. Patient-independent evaluation could not be verified, "
        "and the scores must not be described as leakage-free."
    )
    return rows, classes, note


def _label_digest(labels) -> str:
    payload = np.asarray(labels, dtype=np.int64).reshape(-1).tobytes()
    return hashlib.sha256(payload).hexdigest()


def _skin_bases(data_root: Path, input_size: int):
    from medmnist import INFO, DermaMNIST

    folder = _first_existing(data_root, ("medmnist", "skin_dermamnist"))
    if folder is None:
        folder = data_root / "medmnist"
        folder.mkdir(parents=True, exist_ok=True)
    info = INFO["dermamnist"]["label"]
    classes = []
    for index in range(len(info)):
        classes.append(str(info[index] if index in info else info[str(index)]))
    download = not any(folder.glob("dermamnist*.npz"))
    bases = {}
    for split in ("train", "val", "test"):
        bases[split] = DermaMNIST(
            split=split,
            download=download,
            size=input_size,
            root=str(folder),
            as_rgb=True,
            mmap_mode="r",
        )
    return classes, bases


def build_manifest(dataset: str, data_root: Path | None = None) -> dict:
    data_root = Path(data_root or resolve_data_root())
    if dataset == "brain":
        rows, classes, note = _brain_records(data_root)
        test_rows = [row for row in rows if row["hint"] == "test"]
        val_rows = [row for row in rows if row["hint"] == "val"]
        train_pool = [row for row in rows if row["hint"] in {"train", "all"}]
        if not test_rows:
            raise RuntimeError("The brain MRI official Testing folder is missing, so the split was not invented.")
        if not val_rows:
            train_rows, val_rows = _stratified_cut(train_pool, 0.15, SPLIT_SEED)
        else:
            train_rows = train_pool
        for row in train_rows + val_rows + test_rows:
            row.pop("hint", None)
            row.pop("stem", None)
        manifest = _manifest("brain", classes, train_rows, val_rows, test_rows, "image", False, note)
    elif dataset == "breast":
        rows, classes = _breast_records(data_root)
        splits, patients = split_patients(rows, classes)
        note = (
            f"Patient-level split, seed {SPLIT_SEED}. "
            f"Patients train {patients['train']}, validation {patients['val']}, test {patients['test']}. "
            "Every slide from one patient stays in one split. Magnifications of the same patient are not separated."
        )
        manifest = _manifest(
            "breast", classes, splits["train"], splits["val"], splits["test"], "patient", True, note
        )
        manifest["patients"] = patients
    elif dataset == "lung":
        rows, classes, note = _lung_records(data_root)
        train_val, test_rows = _stratified_cut(rows, 0.15, SPLIT_SEED)
        train_rows, val_rows = _stratified_cut(train_val, 0.15 / 0.85, SPLIT_SEED)
        manifest = _manifest("lung", classes, train_rows, val_rows, test_rows, "image", False, note)
    elif dataset == "skin":
        classes, bases = _skin_bases(data_root, INPUT_SIZE)
        counts = {}
        digests = {}
        for split, base in bases.items():
            labels = np.asarray(base.labels).reshape(-1).astype(int)
            tallies = np.bincount(labels, minlength=len(classes))
            counts[split] = {classes[i]: int(tallies[i]) for i in range(len(classes))}
            digests[split] = _label_digest(labels)
        manifest = {
            "dataset": "skin",
            "split_seed": None,
            "grouping": "official_medmnist",
            "patient_independent": False,
            "leakage_note": (
                "The official MedMNIST train, validation, and test arrays are kept as published. "
                "They were not reshuffled. DermaMNIST does not ship HAM10000 lesion_id, "
                "so images of the same lesion may cross the split. "
                "Lesion-level independence could not be verified."
            ),
            "classes": classes,
            "counts": counts,
            "label_sha256": digests,
            "train": [],
            "val": [],
            "test": [],
        }
    else:
        raise KeyError(dataset)
    if dataset != "skin":
        assert_disjoint(manifest)
    return manifest


def _manifest(dataset, classes, train_rows, val_rows, test_rows, grouping, patient_independent, note) -> dict:
    if not train_rows or not val_rows or not test_rows:
        raise RuntimeError(
            f"{dataset} split is empty (train {len(train_rows)}, val {len(val_rows)}, test {len(test_rows)})."
        )
    return {
        "dataset": dataset,
        "split_seed": SPLIT_SEED,
        "grouping": grouping,
        "patient_independent": patient_independent,
        "leakage_note": note,
        "classes": classes,
        "counts": {
            "train": _count_rows(train_rows, classes),
            "val": _count_rows(val_rows, classes),
            "test": _count_rows(test_rows, classes),
        },
        "train": train_rows,
        "val": val_rows,
        "test": test_rows,
    }


def ensure_manifest(dataset: str, data_root: Path | None = None) -> dict:
    existing = load_manifest(dataset)
    if existing is not None:
        if dataset != "skin":
            assert_disjoint(existing)
        else:
            _check_skin_digest(existing, data_root)
        return existing
    manifest = build_manifest(dataset, data_root)
    save_manifest(manifest)
    return manifest


def _check_skin_digest(manifest: dict, data_root: Path | None) -> None:
    data_root = Path(data_root or resolve_data_root())
    _classes, bases = _skin_bases(data_root, INPUT_SIZE)
    for split, base in bases.items():
        digest = _label_digest(np.asarray(base.labels).reshape(-1))
        saved = (manifest.get("label_sha256") or {}).get(split)
        if saved and saved != digest:
            raise RuntimeError(
                f"DermaMNIST {split} labels changed since results/splits/skin.json was written. "
                "The official split file was not replaced."
            )


def prepare(dataset: str, augment: bool, input_size: int = INPUT_SIZE, data_root: Path | None = None) -> Bundle:
    data_root = Path(data_root or resolve_data_root())
    manifest = ensure_manifest(dataset, data_root)
    classes = list(manifest["classes"])
    train_tf = build_transform(dataset, train=True, augment=augment, input_size=input_size)
    eval_tf = build_transform(dataset, train=False, augment=False, input_size=input_size)
    if dataset == "skin":
        _classes, bases = _skin_bases(data_root, input_size)
        datasets = {
            "train": SkinDataset(bases["train"], train_tf),
            "val": SkinDataset(bases["val"], eval_tf),
            "test": SkinDataset(bases["test"], eval_tf),
        }
        labels = np.asarray(bases["train"].labels).reshape(-1).astype(int)
        weights = class_weights(labels, len(classes))
    else:
        datasets = {
            "train": ImageListDataset(manifest["train"], train_tf, data_root),
            "val": ImageListDataset(manifest["val"], eval_tf, data_root),
            "test": ImageListDataset(manifest["test"], eval_tf, data_root),
        }
        weights = class_weights([row["label"] for row in manifest["train"]], len(classes))
    return Bundle(
        name=dataset,
        classes=classes,
        train_ds=datasets["train"],
        val_ds=datasets["val"],
        test_ds=datasets["test"],
        class_weights=weights,
        split_counts=manifest["counts"],
        grouping=manifest["grouping"],
        patient_independent=bool(manifest["patient_independent"]),
        leakage_note=manifest["leakage_note"],
        input_size=input_size,
    )


def describe(bundle: Bundle) -> str:
    lines = [
        f"{bundle.name}: grouping={bundle.grouping}, patient_independent={bundle.patient_independent}",
        bundle.leakage_note,
    ]
    for split, counts in bundle.split_counts.items():
        detail = ", ".join(f"{name} {count}" for name, count in counts.items())
        lines.append(f"  {split}: {sum(counts.values())} ({detail})")
    weights = ", ".join(
        f"{name} {weight:.2f}" for name, weight in zip(bundle.classes, bundle.class_weights.tolist())
    )
    lines.append(f"  class weights (mean 1): {weights}")
    return "\n".join(lines)


def audit_datasets(data_root: Path | None = None) -> dict:
    """Write the fixed splits and a short integrity report."""
    data_root = Path(data_root or resolve_data_root())
    report = {"data_root": str(data_root), "datasets": {}}
    for name in DATASETS:
        manifest = ensure_manifest(name, data_root)
        entry = {
            "grouping": manifest["grouping"],
            "patient_independent": manifest["patient_independent"],
            "leakage_note": manifest["leakage_note"],
            "classes": manifest["classes"],
            "counts": manifest["counts"],
            "split_file": str(_split_path(name).relative_to(ROOT)),
        }
        if name == "brain":
            entry["filename_audit"] = _brain_filename_audit(manifest)
        if name == "lung":
            entry["filename_audit"] = _lung_filename_audit(manifest)
        if name == "breast":
            entry["patients"] = manifest.get("patients")
        report["datasets"][name] = entry
    out = ROOT / "results" / "audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "results" / "audit.md").write_text(_audit_markdown(report))
    return report


def _brain_filename_audit(manifest: dict) -> dict:
    """Count numeric suffixes that appear in more than one official pool.

    A repeated number is not proof of the same patient. It is evidence that the
    filename cannot be used as a patient key.
    """
    def suffix(path: str) -> str:
        stem = Path(path).stem
        return stem.split("_")[-1]

    pools = {
        "train": [suffix(row["path"]) for row in manifest["train"]],
        "val": [suffix(row["path"]) for row in manifest["val"]],
        "test": [suffix(row["path"]) for row in manifest["test"]],
    }
    train_set = set(pools["train"]) | set(pools["val"])
    repeated = sorted(train_set & set(pools["test"]))
    return {
        "images": {name: len(values) for name, values in pools.items()},
        "numeric_suffixes_shared_by_train_or_val_and_test": len(repeated),
        "patient_ids_recovered": 0,
    }


def _lung_filename_audit(manifest: dict) -> dict:
    import re

    pattern = re.compile(r"\((\d+)\)")
    per_class = {}
    for split in ("train", "val", "test"):
        for row in manifest[split]:
            per_class.setdefault(row["label"], []).append(Path(row["path"]).stem)
    unique_ok = True
    for stems in per_class.values():
        numbers = []
        for stem in stems:
            match = pattern.search(stem)
            numbers.append(int(match.group(1)) if match else None)
        if len(numbers) != len(set(numbers)) or any(item is None for item in numbers):
            unique_ok = False
    return {
        "images": sum(len(rows) for rows in (manifest["train"], manifest["val"], manifest["test"])),
        "case_numbers_unique_within_class": unique_ok,
        "patient_ids_recovered": 0,
    }


def _audit_markdown(report: dict) -> str:
    lines = [
        "# Dataset audit",
        "",
        f"Data root: `{report['data_root']}`",
        "",
        "Splits are fixed in `results/splits/`. Training seeds do not change membership.",
        "",
    ]
    for name, entry in report["datasets"].items():
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Grouping: {entry['grouping']}")
        lines.append(f"- Patient-independent split verified: {entry['patient_independent']}")
        lines.append(f"- {entry['leakage_note']}")
        lines.append("")
        lines.append("| Split | Images |")
        lines.append("|---|---:|")
        for split, counts in entry["counts"].items():
            lines.append(f"| {split} | {sum(counts.values())} |")
        lines.append("")
        if entry.get("filename_audit"):
            lines.append(f"Filename check: `{json.dumps(entry['filename_audit'])}`")
            lines.append("")
        if entry.get("patients"):
            lines.append(f"Patients: `{json.dumps(entry['patients'])}`")
            lines.append("")
    lines.append(
        "Decision: keep all four datasets. BreakHis is patient-level. "
        "DermaMNIST keeps its official split and does not support a lesion-level claim. "
        "Brain MRI and lung CT stay in the study with an explicit limitation: "
        "patient-independent evaluation could not be verified, and those results are not reported as leakage-free."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(audit_datasets() and (ROOT / "results" / "audit.md").read_text())
