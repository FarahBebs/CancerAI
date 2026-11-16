"""Checks that do not need the image collections or a trained checkpoint."""

from __future__ import annotations

import unittest

import torch
from torchvision import transforms as T

from cancerai.datasets import assert_disjoint, build_transform, split_patients
from cancerai.metrics import classification_metrics
from cancerai.models import build_model, count_params


class ModelTests(unittest.TestCase):
    def test_custom_cnn_output_shape(self):
        model = build_model("custom_cnn", n_classes=4)
        logits = model(torch.zeros(2, 3, 224, 224))
        self.assertEqual(tuple(logits.shape), (2, 4))

    def test_frozen_resnet_trains_only_the_head(self):
        full = build_model("resnet18", n_classes=4, freeze_backbone=False, pretrained=False)
        frozen = build_model("resnet18", n_classes=4, freeze_backbone=True, pretrained=False)
        _full_total, full_trainable = count_params(full)
        _frozen_total, frozen_trainable = count_params(frozen)
        self.assertLess(frozen_trainable, full_trainable)
        self.assertEqual(frozen_trainable, 512 * 4 + 4)

    def test_weighted_cross_entropy_matches_the_formula(self):
        from cancerai.training import weighted_cross_entropy

        logits = torch.tensor([[2.0, 0.5, -1.0], [0.2, 0.2, 3.0]])
        target = torch.tensor([0, 2])
        weight = torch.tensor([1.5, 2.0, 0.5])
        loss = weighted_cross_entropy(logits, target, weight)
        log_probs = torch.log_softmax(logits, dim=1)
        manual = -(weight[target] * log_probs.gather(1, target.view(-1, 1)).squeeze(1)).mean()
        self.assertTrue(torch.allclose(loss, manual))


class DataTests(unittest.TestCase):
    def test_patient_split_has_no_shared_patient(self):
        records = []
        for patient in range(9):
            label = patient % 3
            for image in range(2):
                records.append(
                    {"path": f"p{patient}_{image}.png", "label": label, "group": f"patient-{patient}"}
                )
        splits, _counts = split_patients(records, ["a", "b", "c"], seed=42)
        assert_disjoint(splits)
        for rows in splits.values():
            self.assertTrue(rows)

    def test_mri_and_ct_are_not_flipped(self):
        for dataset in ("brain", "lung"):
            transform = build_transform(dataset, train=True, augment=True)
            kinds = [type(step) for step in transform.transforms]
            self.assertNotIn(T.RandomHorizontalFlip, kinds)
        breast = build_transform("breast", train=True, augment=True)
        kinds = [type(step) for step in breast.transforms]
        self.assertIn(T.RandomHorizontalFlip, kinds)
        self.assertNotIn(T.ColorJitter, [type(step) for step in build_transform("lung", train=True, augment=True).transforms])

    def test_eval_images_are_not_augmented(self):
        transform = build_transform("skin", train=False, augment=False)
        kinds = [type(step) for step in transform.transforms]
        self.assertEqual(kinds, [T.Resize, T.ToTensor, T.Normalize])


class MetricTests(unittest.TestCase):
    def test_macro_f1_weights_classes_equally(self):
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 0, 1]
        probs = [
            [0.9, 0.1],
            [0.8, 0.2],
            [0.7, 0.3],
            [0.2, 0.8],
        ]
        metrics = classification_metrics(y_true, y_pred, probs, ["a", "b"])
        # Class a: P=2/3 R=1 F1=0.8. Class b: P=1 R=0.5 F1=2/3. Macro = average.
        self.assertAlmostEqual(metrics["f1_macro"], (0.8 + (2 / 3)) / 2, places=5)
        self.assertGreater(metrics["accuracy"], metrics["f1_macro"])


if __name__ == "__main__":
    unittest.main()
