# CancerAI

**BIL458 — Computer Vision.** A comparative study of deep learning strategies for multi-modal medical image classification.

Four image collections stay separate, because the pictures and the labels are different:

| Module | Collection | What the model classifies |
|---|---|---|
| Brain MRI | Brain Tumor MRI | Glioma, meningioma, pituitary tumor, no tumor |
| Breast | BreakHis | Eight histopathological subtypes |
| Skin | DermaMNIST / HAM10000 | Seven lesion categories |
| Lung CT | IQ-OTH/NCCD | Normal, benign, malignant |

These are tumour and lesion categories. They are not one cancer detector. A brain tumor in this collection is not labeled benign or malignant. Several skin categories are not cancer. The Gradio page is a course demonstration, not a clinical device.

## Research question

How do CNN training strategies and data augmentation change classification across these four modalities?

- H1. Fine-tuned ResNet18 beats a custom CNN and a frozen ResNet18 on macro-F1.
- H2. Training augmentation improves the fine-tuned model, especially where a class is rare.
- H3. The size of that gain depends on the modality.
- H4. Accuracy hides weak minority classes. Macro-F1 and per-class recall show them.

Macro-F1 is the score used to keep a checkpoint. Each configuration is repeated with seeds 42, 123, and 2026. The split does not change with the seed. Results are mean ± sample standard deviation.

| Configuration | What is trained | Augmentation | Learning rate |
|---|---|---|---|
| `custom_cnn` | Four-block CNN from scratch | On | 1e-3 |
| `frozen_resnet18` | New head only; ImageNet backbone frozen | On | 1e-3 |
| `finetune_aug` | All ResNet18 weights | On | 1e-4 |
| `finetune_no_aug` | All ResNet18 weights | Off | 1e-4 |

That is 4 configurations × 3 seeds × 4 datasets = 48 runs. Validation and test images are never augmented. The loss is class-weighted cross-entropy. Early stopping watches validation macro-F1 (patience 3).

Augmentation is not the same for every modality. Histopathology and dermoscopy may be flipped. MRI and CT are not flipped, because left and right are anatomical. Hue is not jittered.

## Split rules

Membership is written once to `results/splits/` and reloaded after that.

- **Breast.** Patient-level. Every magnification of one patient stays in one split. The loader checks that no patient id appears twice.
- **Skin.** Official MedMNIST split, not reshuffled. Lesion ids are not in DermaMNIST, so this is not a lesion-level claim.
- **Brain MRI and lung CT.** Filenames do not contain a patient or scan id. The brain test set is the official Testing folder. The lung split is stratified by image. Those two results are not described as patient-level or leakage-free.

`results/audit.md` records the counts and that decision. The draft paragraph for the 25 November proposal is `docs/proposal.md`.

## Layout

```
cancerai/          datasets, models, training, metrics, Grad-CAM
experiments/       the 48-run configuration and the summary tables
notebooks/         BIL458_CancerAI_Experiments.ipynb
deliverables/      the report PDF and the ten-slide talk
app.py             Gradio demo
results/splits/    the fixed split
models/            demo checkpoints (fine-tuned ResNet18, best validation macro-F1)
```

## Run

Python 3.13 is the interpreter this project was checked with. The system `python3` on this Mac is 3.14 and does not have PyTorch.

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export CANCERAI_DATA="../Deep Learning/Homework 2 - CancerAI/data"   # if the images are already there

python -m cancerai.datasets          # write splits and results/audit.md
python -m unittest tests.test_core -v
python -m experiments.run_experiments --smoke
python -m experiments.run_experiments          # 48 runs
python -m experiments.summarize
python app.py                        # http://127.0.0.1:7860
```

Open `notebooks/BIL458_CancerAI_Experiments.ipynb` and use Kernel → Restart & Run All before submission. The 48 runs are already saved, so `RUN_FULL_STUDY` stays off and the notebook loads those scores. The report is `deliverables/BIL458_CancerAI_Report.pdf`. The talk is `deliverables/BIL458_CancerAI_Slides.pptx`.

The demo asks for a modality, then shows the category, the broader group obtained by adding the category scores, and Grad-CAM. The group is not a second model.
