# Comparison

Primary metric: test macro-F1, mean ± sample standard deviation across seeds.
A cell stays empty until every listed seed for that configuration has a metrics file.

## Models

| Dataset | Custom CNN | Frozen ResNet18 | Fine-tuned ResNet18 |
|---|---:|---:|---:|
| Brain MRI | 0.724 ± 0.011 | 0.837 ± 0.002 | 0.989 ± 0.004 |
| Breast histopathology | 0.272 ± 0.016 | 0.349 ± 0.024 | 0.506 ± 0.031 |
| Skin lesion | 0.371 ± 0.009 | 0.344 ± 0.008 | 0.719 ± 0.014 |
| Lung CT | 0.366 ± 0.044 | 0.617 ± 0.034 | 0.946 ± 0.021 |

## Augmentation ablation (fine-tuned ResNet18)

| Dataset | With augmentation | Without augmentation |
|---|---:|---:|
| Brain MRI | 0.989 ± 0.004 | 0.985 ± 0.006 |
| Breast histopathology | 0.506 ± 0.031 | 0.462 ± 0.024 |
| Skin lesion | 0.719 ± 0.014 | 0.762 ± 0.022 |
| Lung CT | 0.946 ± 0.021 | 0.992 ± 0.007 |

## Accuracy (secondary)

| Dataset | Custom CNN | Frozen ResNet18 | Fine-tuned ResNet18 |
|---|---:|---:|---:|
| Brain MRI | 0.736 ± 0.014 | 0.845 ± 0.004 | 0.990 ± 0.004 |
| Breast histopathology | 0.378 ± 0.054 | 0.406 ± 0.024 | 0.581 ± 0.020 |
| Skin lesion | 0.499 ± 0.008 | 0.538 ± 0.008 | 0.787 ± 0.010 |
| Lung CT | 0.523 ± 0.075 | 0.705 ± 0.036 | 0.968 ± 0.013 |

Finished metric files: 48 / 48.
