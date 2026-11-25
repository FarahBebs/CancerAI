# CancerAI — presentation script (15 minutes)

Use this as a guide, not something to read word for word. Each slide has **one key sentence**. If you say only that sentence, the slide still makes sense. The same text is in the speaker notes of `BIL458_CancerAI_Slides.pptx`.

| Slide | Topic | Time | Running total |
|---|---|---|---|
| 1 | Title and task distribution | 0:45 | 0:45 |
| 2 | Problem and aim | 1:30 | 2:15 |
| 3 | Data and fair split | 1:30 | 3:45 |
| 4 | Method pipeline | 1:30 | 5:15 |
| 5 | The maths | 1:30 | 6:45 |
| 6 | Experiment design | 1:00 | 7:45 |
| 7 | Results | 1:30 | 9:15 |
| 8 | Ablation | 1:30 | 10:45 |
| 9 | Failure analysis | 1:30 | 12:15 |
| 10 | Demo and conclusion | 2:30 | 14:45 |

**Before the talk:** run `python app.py` and open http://127.0.0.1:7860 in a browser tab, so the demo is ready. Also keep a short screen recording of the demo as a backup, in case the laptop or network fails. A demo that does not work loses points.

---

## 1. Title and task distribution — 0:45
**Key sentence:** "I compare three ways of training a CNN on four kinds of medical images."

Hello, I'm Farah Alhasan. My project is CancerAI. It is an individual project, so I did every part: preparing the data and splits, training the models, the evaluation and ablation, the demo app, and the report.
The question is simple: if we train a CNN in different ways, how much does that change the result on medical images?
I'll cover the problem, the data, the method and the maths, the results, where the model fails, and then a short live demo.

## 2. Problem and aim — 1:30
**Key sentence:** "Each image type is its own task, and I want to know whether the best training recipe is the same for all of them."

These are the four kinds of images: brain MRI, breast tissue under a microscope, skin lesion photos, and lung CT. Each one is a separate task with its own classes. This is not one "cancer detector".
Research question: does the training strategy, and data augmentation, change the score, and is the change the same for every image type?
I wrote four hypotheses before training:
- **H1:** fine-tuning a pretrained network will win.
- **H2:** augmentation will help, especially for rare classes.
- **H3:** how much it helps depends on the image type.
- **H4:** accuracy can hide classes the model gets wrong, so I need macro-F1.

## 3. Data and fair split — 1:30
**Key sentence:** "A fair test needs each patient on one side only; only the breast dataset lets me guarantee that."

The table shows the four datasets, their classes, and how many images went to training, validation and test.
The most important column is how the split was made.
*Data leakage* means the same patient is in training and in test. Then the model can memorise that patient instead of learning the disease, and the test score looks better than it really is.
Only BreakHis has patient IDs, so only there could I keep every patient on one side: 54 patients for training, 14 for validation, 14 for test. That makes breast the most honest result. For skin I used the official split. Brain and lung files have no patient ID, so I say clearly that those scores might be too optimistic.
The split is saved to a file once, and all 48 runs reuse the same file.

## 4. Method pipeline — 1:30
**Key sentence:** "Everything is the same except the model box, where I try three training strategies."

Left to right: an image comes in, it is resized to 224 by 224 and normalised. During training only, I add augmentation: small flips, rotations and brightness changes. Validation and test images are never changed.
Then one of three models:
1. **From scratch:** a small CNN with about 0.39 million weights. It only ever sees the medical images. This is my baseline.
2. **Frozen ResNet18:** I reuse features learned on ImageNet, a big photo dataset, and only train the last layer, a few thousand weights.
3. **Fine-tuned ResNet18:** I reuse those features and adjust every layer, 11.2 million weights, with a small learning rate.

At the end, softmax gives a probability for each class, and Grad-CAM shows which part of the image influenced the decision.

## 5. The maths — 1:30
**Key sentence:** "The loss makes rare classes count, the metric checks every class equally, and the cost tells us how fast it runs."

1. **Loss:** cross-entropy where each class has a weight. The weight is larger when a class has fewer images (w = N / (C · n_c)). A mistake on a rare class costs more, so the model can't just ignore it.
2. **Metric:** macro-F1 computes the F1 score for each class and then takes the plain average. Every class counts the same, so a big class can't hide a weak one. I use it to pick the best epoch and to report results.
3. **Cost:** one convolution layer costs about height × width × kernel² × input channels × output channels operations. My small CNN needs about 0.74 billion multiply-adds per image and ResNet18 about 1.8 billion. In practice that is about 1.5 ms against 3 ms per image, so the bigger model is still fast.

## 6. Experiment design — 1:00
**Key sentence:** "48 runs, and between any two columns only one thing changes."

Four datasets, four setups, three random seeds: 48 runs. Each dot on the slide is one run.
The baseline is the small CNN from scratch. The ablation is the last column: the same fine-tuning with augmentation switched off.
Every run uses the same split, AdamW, a cosine learning-rate schedule and the weighted loss. I keep the epoch with the best validation macro-F1 and stop after three epochs with no gain. The test set is used once, at the end. I report the mean ± standard deviation over seeds 42, 123 and 2026.

## 7. Results — 1:30
**Key sentence:** "Fine-tuning is the best on all four datasets, but by very different margins."

The dark bar, fine-tuning, is the highest everywhere, so H1 is supported. The gap changes a lot between datasets, so H3 is supported too.
One surprise: on skin, the frozen network (0.34) is slightly worse than the small CNN from scratch (0.37). ImageNet features that are never adjusted don't describe skin lesions well. Once every layer is adjusted, skin goes up to 0.72.
Breast is the lowest at about 0.51. Remember that it is the only patient-level split, so it is the most honest number.

## 8. Ablation — 1:30
**Key sentence:** "Augmentation helped breast but hurt skin and lung, so it has to be chosen per image type."

This is the same fine-tuned model with and without augmentation. Breast improved by about 4 points. Brain barely changed. Skin and lung got about 4 to 5 points worse in every seed. With only three seeds the t-test gives p of about 0.05, so I call it a clear trend, not a proven effect.
Why? Breast has few patients, so flipped and rotated views of the tissue are genuinely new examples. For skin, colour is a key clue, and brightness and saturation changes can blur the difference between a mole and a melanoma. For lung, the dataset is small and clean, and rotated images drift away from what the test images look like.
So H2 is only partly true.

## 9. Failure analysis — 1:30
**Key sentence:** "The average score hides a class the model almost never gets right."

- **Breast:** the phyllodes tumour class has an F1 of almost zero. About 143 of its 235 test images are called fibroadenoma, and these two benign tissues look very similar. The Grad-CAM pictures show that the model looks at the tissue, not the background, so this is a real look-alike problem.
- **Skin:** accuracy is 0.79 but macro-F1 is 0.72. Most test images are normal moles, so accuracy looks good, but melanoma precision is only 0.48: the model calls too many things melanoma. That supports H4.
- **Brain:** 0.99 looks great, but without patient IDs, slices from the same scan may sit in both training and test, so the score might be inflated.

## 10. Demo and conclusion — 2:30 (about 1 minute of demo)
**Key sentence:** "Fine-tune, choose augmentation per image type, and always look at macro-F1."

**Demo (switch to the browser):** choose the image type, upload an example image, then point at three things: the predicted category; the broader group, such as benign or malignant, which is just the category probabilities added up and not a second model; and the Grad-CAM map. Point at the disclaimer too: this is not a diagnosis.

**Conclusion:**
1. Fine-tuning a pretrained ResNet18 was the best strategy on all four image types.
2. Augmentation is not automatically good: it helped breast and hurt skin and lung.
3. Macro-F1 showed weak classes that accuracy hid.

The main limitation is the split: only breast is patient-level. Next I would use datasets with patient IDs, and try stain normalisation or focal loss for the rare breast classes.
Thank you. I'm happy to take questions.

---

## Likely questions and simple answers

**1. Why macro-F1 and not accuracy?**
Accuracy is dominated by the biggest class. On skin, 1,341 of the 2,005 test images are normal moles, so a model can have good accuracy and still be weak on melanoma. Macro-F1 averages the F1 of each class equally, so a weak class pulls the score down where we can see it.

**2. What exactly is data leakage, and how did you prevent it?**
Leakage is when information from the test set gets into training, for example the same patient on both sides. I saved the split to a file once and reused it in every run. For BreakHis I split by patient, and a check in the code refuses to train if a patient appears in two splits. Validation and test images are never augmented, and the test set is used only once, after choosing the best epoch on validation.

**3. Why ResNet18 and not a bigger model?**
It is a standard, well-understood network with ImageNet weights, it trains quickly on a laptop GPU, and its residual connections make it stable to fine-tune. The question was about the training strategy, not the biggest model, so a mid-size network keeps 48 runs affordable.

**4. Why is the frozen ResNet18 worse than the small CNN on skin?**
Frozen means the ImageNet features are never changed. ImageNet is everyday photos, and those fixed features don't describe the colour and texture of skin lesions well. The small CNN at least learns its features from skin images. Once ResNet18 is allowed to adjust every layer, it beats both by a lot (0.72).

**5. Why did augmentation hurt skin and lung?**
For skin, colour is a key clue, and changing brightness and saturation can make a mole look like a melanoma or the other way round. For lung, the dataset is small and quite uniform, so rotated training images look less like the test images. The gaps (about 0.04–0.05) are bigger than the seed standard deviations, so they are not random noise.

**6. What does Grad-CAM show?**
It takes the gradient of the predicted class with respect to the last convolution layer and uses it to colour the image. Warm colours are the regions that pushed the model towards its answer. It is not a tumour outline or a segmentation; it is a way to check whether the model looks at the tissue or at the background.

**7. Would you use this in a hospital?**
No. Only one dataset has a patient-level split, the brain and lung scores may be inflated by leakage, phyllodes tumour is almost never detected, and the model was never tested on images from a new hospital or scanner. It is a course demonstration, and the demo page says so.

**8. What would you do next?**
Use datasets that include patient IDs for brain and lung, link the HAM10000 lesion IDs back to DermaMNIST, and for breast try stain normalisation, focal loss or higher input resolution to help the rare and look-alike classes.

**9. Why three seeds?**
The seed changes the starting weights and the order of the training images, and the result changes a little each time. Three seeds (42, 123, 2026) let me report the mean ± standard deviation and check whether a difference is bigger than this random variation. The assignment also asks for at least three.

**10. What is the computational cost (Big-O)?**
One convolution layer costs O(H·W·k²·C_in·C_out) multiply-adds. The custom CNN needs about 0.74 billion multiply-adds per 224×224 image and ResNet18 about 1.8 billion. Measured inference is about 1.5 ms and 3 ms per image. The frozen model is cheaper to train because only the last layer (512·C + C weights) gets gradients, but its forward pass costs the same as the fine-tuned model.

**11. How were the class weights chosen?**
w_c = N / (C · n_c): the total number of training images divided by the number of classes times the number of images in class c, rescaled to average 1. A class with few images gets a big weight. They come from the training split only, never from test.

**12. Why do the breast validation and test scores differ so much?**
There are only 14 validation patients and 14 test patients, so each split is a small sample of "new hospitals". The validation patients happened to be harder. This is exactly why a patient-level split gives an honest, and lower, number.
