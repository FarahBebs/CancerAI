"""The four configurations crossed with three seeds and four datasets (48 runs)."""

from cancerai.config import SEEDS

CONFIGS = {
    "custom_cnn": {
        "model": "custom_cnn",
        "pretrained": False,
        "freeze_backbone": False,
        "augment": True,
        "lr": 1e-3,
        "epochs": 10,
        "patience": 3,
        "role": "Baseline trained from scratch",
    },
    "frozen_resnet18": {
        "model": "resnet18",
        "pretrained": True,
        "freeze_backbone": True,
        "augment": True,
        "lr": 1e-3,
        "epochs": 8,
        "patience": 3,
        "role": "ImageNet backbone frozen; only the new head is trained",
    },
    "finetune_aug": {
        "model": "resnet18",
        "pretrained": True,
        "freeze_backbone": False,
        "augment": True,
        "lr": 1e-4,
        "epochs": 8,
        "patience": 3,
        "role": "Full fine-tuning with training augmentation",
    },
    "finetune_no_aug": {
        "model": "resnet18",
        "pretrained": True,
        "freeze_backbone": False,
        "augment": False,
        "lr": 1e-4,
        "epochs": 8,
        "patience": 3,
        "role": "Full fine-tuning without training augmentation",
    },
}

# Main comparison in the report. The fourth config is the augmentation ablation.
MAIN_CONFIGS = ("custom_cnn", "frozen_resnet18", "finetune_aug")
ABLATION_CONFIGS = ("finetune_aug", "finetune_no_aug")
ALL_SEEDS = SEEDS
