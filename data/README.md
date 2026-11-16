# Datasets

Image files are not part of this repository. Put them under `data/`, or point `CANCERAI_DATA` at a folder that already contains them.

Expected layout (either names work):

```
data/
├── brain/            or brain_mri/          # Training/ and Testing/, four class folders
├── breakhis/         or breast_breakhis/    # BreaKHis_v1 patient folders
├── medmnist/         or skin_dermamnist/    # dermamnist_224.npz
└── iqoth/            or lung_iqoth/         # Normal / Benign / Malignant case folders
```

On this machine the files already exist beside this project. From the repository root:

```bash
export CANCERAI_DATA="../Deep Learning/Homework 2 - CancerAI/data"
```

If `CANCERAI_DATA` is unset and `data/` is empty, the loaders also check that neighbouring folder.

Licences stay with the sources: Brain Tumor MRI is CC BY 4.0, HAM10000 / DermaMNIST is CC BY-NC 4.0, BreakHis is released by UFPR for research, and IQ-OTH/NCCD is a public teaching set. Do not redistribute the images.
