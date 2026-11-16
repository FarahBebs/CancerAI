"""Custom CNN baseline and ResNet18 transfer-learning heads.

Convolution at one spatial position:

    Y(i, j) = sum_u sum_v  X(i+u, j+v) K(u, v)

ReLU is f(x) = max(0, x). A convolutional layer costs about
O(H W C_in C_out K^2) multiply-adds. ResNet18 uses that budget across
18 layers and starts from ImageNet weights. The custom CNN is four
convolutions, so it is cheaper and has no external pretraining.
Freezing the ResNet backbone leaves only the new classification head trainable.
"""

from __future__ import annotations

import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18

from cancerai.config import DROPOUT


class CustomCNN(nn.Module):
    """Four-block CNN trained from scratch. The last convolution is the Grad-CAM layer."""

    def __init__(self, n_classes: int, dropout: float = DROPOUT):
        super().__init__()
        self.block1 = _conv_block(3, 32)
        self.block2 = _conv_block(32, 64)
        self.block3 = _conv_block(64, 128)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.relu4 = nn.ReLU(inplace=False)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.cam_layer = self.conv4
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(p=dropout), nn.Linear(256, n_classes))

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.relu4(self.conv4(x))
        x = self.pool(x)
        return self.head(x)


def _conv_block(in_channels: int, out_channels: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.ReLU(inplace=False),
        nn.MaxPool2d(kernel_size=2),
    )


def build_resnet18(n_classes: int, freeze_backbone: bool = False, pretrained: bool = True) -> nn.Module:
    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = resnet18(weights=weights)
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False
    in_features = model.fc.in_features
    model.fc = nn.Sequential(nn.Dropout(p=DROPOUT), nn.Linear(in_features, n_classes))
    return model


def build_model(name: str, n_classes: int, freeze_backbone: bool = False, pretrained: bool = True) -> nn.Module:
    if name == "custom_cnn":
        return CustomCNN(n_classes)
    if name == "resnet18":
        return build_resnet18(n_classes, freeze_backbone=freeze_backbone, pretrained=pretrained)
    raise ValueError(f"Unknown model: {name}")


def count_params(model: nn.Module) -> tuple[int, int]:
    total = sum(param.numel() for param in model.parameters())
    trainable = sum(param.numel() for param in model.parameters() if param.requires_grad)
    return total, trainable


def cam_layer(model: nn.Module) -> nn.Module:
    if isinstance(model, CustomCNN):
        return model.cam_layer
    if hasattr(model, "layer4"):
        return model.layer4[-1]
    raise TypeError("This model has no Grad-CAM layer.")


def apply_train_mode(model: nn.Module, freeze_backbone: bool) -> None:
    model.train()
    if freeze_backbone:
        for module in model.modules():
            if isinstance(module, nn.BatchNorm2d):
                module.eval()


def disable_inplace_relu(model: nn.Module) -> None:
    for module in model.modules():
        if isinstance(module, nn.ReLU):
            module.inplace = False
