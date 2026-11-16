# Dataset audit

Data root: `/Users/farahalhasan/Desktop/Projects/Deep Learning/Homework 2 - CancerAI/data`

Splits are fixed in `results/splits/`. Training seeds do not change membership.

## brain

- Grouping: image
- Patient-independent split verified: False
- Filenames are sequential slice indexes (for example Tr-gl_0505), not patient or scan ids. The official Testing folder is held out and 15% of the official Training folder is validation. Slices from the same scan can still sit in more than one split. These scores are not a patient-level result.

| Split | Images |
|---|---:|
| train | 4855 |
| val | 857 |
| test | 1311 |

Filename check: `{"images": {"train": 4855, "val": 857, "test": 1311}, "numeric_suffixes_shared_by_train_or_val_and_test": 405, "patient_ids_recovered": 0}`

## breast

- Grouping: patient
- Patient-independent split verified: True
- Patient-level split, seed 42. Patients train 54, validation 14, test 14. Every slide from one patient stays in one split. Magnifications of the same patient are not separated.

| Split | Images |
|---|---:|
| train | 4973 |
| val | 1399 |
| test | 1537 |

Patients: `{"train": 54, "val": 14, "test": 14}`

## skin

- Grouping: official_medmnist
- Patient-independent split verified: False
- The official MedMNIST train, validation, and test arrays are kept as published. They were not reshuffled. DermaMNIST does not ship HAM10000 lesion_id, so images of the same lesion may cross the split. Lesion-level independence could not be verified.

| Split | Images |
|---|---:|
| train | 7007 |
| val | 1003 |
| test | 2005 |

## lung

- Grouping: image
- Patient-independent split verified: False
- The number in each filename, such as 'Bengin case (85)', is unique inside its class and runs from 1 to the class count. It is an image index, not a patient id shared by several slices. The public folders do not reconstruct the scan. The split is stratified by image. Patient-independent evaluation could not be verified, and the scores must not be described as leakage-free.

| Split | Images |
|---|---:|
| train | 767 |
| val | 165 |
| test | 165 |

Filename check: `{"images": 1097, "case_numbers_unique_within_class": true, "patient_ids_recovered": 0}`

Decision: keep all four datasets. BreakHis is patient-level. DermaMNIST keeps its official split and does not support a lesion-level claim. Brain MRI and lung CT stay in the study with an explicit limitation: patient-independent evaluation could not be verified, and those results are not reported as leakage-free.

