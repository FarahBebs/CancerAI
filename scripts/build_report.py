"""Build the BIL458 report PDF from the saved experiment files."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/tmp/cv-pydeps")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "BIL458_CancerAI_Report.pdf"
PLOTS = ROOT / "results" / "plots"
GRADCAM = ROOT / "results" / "gradcam"
DEMO = ROOT / "deliverables" / "figures"

NAVY = colors.HexColor("#12312A")
TEAL = colors.HexColor("#1F6F6A")
RULE = colors.HexColor("#D7D1C7")
ROW = colors.HexColor("#F6F3EE")


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        "CoverKicker", fontName="Times-Bold", fontSize=11, textColor=TEAL,
        alignment=TA_CENTER, spaceAfter=8, tracking=1,
    ))
    base.add(ParagraphStyle(
        "CoverTitle", fontName="Times-Bold", fontSize=18, leading=23,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
    ))
    base.add(ParagraphStyle(
        "CoverMeta", fontName="Times-Roman", fontSize=12, leading=16,
        alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "H1", fontName="Times-Bold", fontSize=14, leading=18, textColor=NAVY,
        spaceBefore=14, spaceAfter=6,
    ))
    base.add(ParagraphStyle(
        "H2", fontName="Times-Bold", fontSize=12, leading=15, textColor=TEAL,
        spaceBefore=10, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Body", fontName="Times-Roman", fontSize=11, leading=14.5,
        alignment=TA_JUSTIFY, spaceAfter=8,
    ))
    base.add(ParagraphStyle(
        "Eq", fontName="Times-Italic", fontSize=11, leading=14,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Caption", fontName="Times-Italic", fontSize=9, leading=12,
        alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=10,
    ))
    base.add(ParagraphStyle(
        "Cell", fontName="Times-Roman", fontSize=8.5, leading=11,
    ))
    base.add(ParagraphStyle(
        "CellHead", fontName="Times-Bold", fontSize=8.5, leading=11, textColor=colors.white,
    ))
    base.add(ParagraphStyle(
        "Ref", fontName="Times-Roman", fontSize=10, leading=13, leftIndent=14,
        firstLineIndent=-14, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Algo", fontName="Times-Roman", fontSize=10, leading=13, leftIndent=6,
    ))
    return base


S = styles()


def P(text):
    return Paragraph(text, S["Body"])


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(item, S["Body"]), leftIndent=8) for item in items],
        bulletType="bullet", start="-", leftIndent=16, bulletFontName="Times-Roman",
        spaceBefore=2, spaceAfter=6,
    )


def table(headers, rows, col_widths, caption):
    head = [Paragraph(h, S["CellHead"]) for h in headers]
    body = [[Paragraph(str(cell), S["Cell"]) for cell in row] for row in rows]
    data = [head] + body
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW]),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return KeepTogether([tbl, Paragraph(caption, S["Caption"])])


def figure(path: Path, caption: str, width=15.5 * cm, height=8.2 * cm):
    img = Image(str(path), width=width, height=height, kind="proportional")
    return KeepTogether([img, Paragraph(caption, S["Caption"])])


def figure_pair(left: Path, right: Path, caption: str, width=15.5 * cm, height=6.2 * cm):
    gap = 0.4 * cm
    each = (width - gap) / 2
    row = Table(
        [[
            Image(str(left), width=each, height=height, kind="proportional"),
            Image(str(right), width=each, height=height, kind="proportional"),
        ]],
        colWidths=[each, each],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return KeepTogether([row, Paragraph(caption, S["Caption"])])


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 1.15 * cm, A4[0], 1.15 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Roman", 9)
    canvas.drawString(1.8 * cm, A4[1] - 0.75 * cm, "BIL458 Computer Vision")
    canvas.drawRightString(A4[0] - 1.8 * cm, A4[1] - 0.75 * cm, "CancerAI")
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.setFont("Times-Roman", 9)
    canvas.drawCentredString(A4[0] / 2, 1.0 * cm, str(doc.page))
    canvas.restoreState()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.7 * cm, bottomMargin=1.6 * cm,
        title="CancerAI: A Comparative Study of Deep Learning Strategies for Multi-Modal Medical Image Classification",
        author="Farah Alhasan",
    )
    story = []
    W = 17.4 * cm

    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph("BIL458 COMPUTER VISION", S["CoverKicker"]))
    story.append(Paragraph(
        "CancerAI: A Comparative Study of Deep Learning Strategies for Multi-Modal Medical Image Classification",
        S["CoverTitle"],
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Farah Alhasan", S["CoverMeta"]))
    story.append(Paragraph("Student number 21120205709", S["CoverMeta"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Instructor: Assoc. Prof. Murat Gezer", S["CoverMeta"]))
    story.append(Paragraph("Faculty of Engineering and Natural Sciences", S["CoverMeta"]))
    story.append(Paragraph("Department of Computer Engineering", S["CoverMeta"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Term project report", S["CoverMeta"]))
    story.append(Paragraph("18 November 2026", S["CoverMeta"]))
    story.append(Paragraph(
        "Notebook and code: https://github.com/FarahBebs/CancerAI",
        S["CoverMeta"],
    ))
    story.append(PageBreak())

    story.append(Paragraph("Abstract", S["H1"]))
    abstract = (
        "This study asks how the training strategy and data augmentation change multi-class "
        "classification across four medical image types that must stay separate: brain MRI, "
        "breast histopathology, dermoscopy, and lung CT. The labels are tumour and lesion "
        "categories, not one cancer decision. A four-block convolutional network trained from "
        "scratch is compared with an ImageNet ResNet18 whose backbone is frozen and with a "
        "fully fine-tuned ResNet18. The fine-tuned model is trained once with augmentation and "
        "once without it. Validation and test images are never augmented. The split is written "
        "once. BreakHis is divided by patient. DermaMNIST keeps its published split. Brain MRI "
        "and lung CT filenames do not identify the patient, so those scores are not patient-level "
        "results. The primary metric is macro-F1, reported as the mean and the sample standard "
        "deviation over seeds 42, 123, and 2026. Fine-tuning leads on every dataset, with test "
        "macro-F1 of 0.989 on brain MRI, 0.506 on breast tissue, 0.719 on skin, and 0.946 on "
        "lung CT. The from-scratch network is far behind where the classes are many or rare. "
        "Augmentation raises the breast score and changes the others by only a few points. "
        "Missing patient identifiers, and a near-zero phyllodes score on BreakHis, are the main "
        "limits. The system is a course demonstration, not a diagnostic device."
    )
    story.append(P(abstract))
    story.append(Paragraph(
        "Keywords: medical image classification, ResNet, transfer learning, macro-F1, data leakage.",
        S["Body"],
    ))

    story.append(Paragraph("1. Introduction", S["H1"]))
    story.append(P(
        "Public medical image collections are large enough to train a convolutional network, "
        "and small enough that the training recipe matters. A model started from random weights "
        "has to discover edges, texture, and colour from the medical set alone. A network that "
        "already learned those patterns on ImageNet can either keep them fixed and train a new "
        "head, or adapt every layer with a small learning rate [1], [2]. Which of those choices "
        "is better is not obvious, because a microscope slide, a dermoscopic photograph, an MRI "
        "slice, and a CT slice do not share the same visual statistics."
    ))
    story.append(P(
        "The practical risk is larger than the choice of architecture. Reported accuracies near "
        "99 percent on 2D slices are often produced by a split that puts two slices of the same "
        "person on both sides of the test cut. Yagis et al. showed that a slice-level split of "
        "brain MRI can raise accuracy by tens of points, and that a model can still score about "
        "96 percent after the diagnosis labels have been replaced by noise [3]. A high score is "
        "therefore not, by itself, evidence that the network has learned the disease."
    ))
    story.append(P(
        "This project keeps four collections and treats each as its own classification task. "
        "A brain tumour in the MRI set is not labelled benign or malignant. Several skin "
        "categories are not cancer. The research question is how CNN training strategy and "
        "data augmentation change macro-F1 across these four tasks. The hypotheses are:"
    ))
    story.append(bullets([
        "H1. A fine-tuned ResNet18 will outscore a custom CNN and a frozen ResNet18.",
        "H2. Training augmentation will improve the fine-tuned model, especially where a class is rare.",
        "H3. The size of that gain will depend on the modality.",
        "H4. Accuracy will hide weak minority classes that macro-F1 and per-class recall will show.",
    ]))
    story.append(P(
        "The contribution is the controlled comparison itself: the same split, the same loss, "
        "three seeds, and one augmentation switch. It is not a claim that one network detects "
        "every cancer."
    ))

    story.append(Paragraph("2. Method", S["H1"]))
    story.append(Paragraph("2.1 Problem definition", S["H2"]))
    story.append(P(
        "Each dataset is a separate supervised classification problem. An image X is mapped to "
        "a class index in {1, ..., C}, where C is 4 for brain MRI, 8 for BreakHis, 7 for "
        "DermaMNIST, and 3 for lung CT. The network returns logits. The predicted class is the "
        "argmax. A coarser group, such as benign or malignant on BreakHis, is obtained by adding "
        "the category probabilities that belong to that group. That sum is a lookup, not a second "
        "trained model, and a tumour group is not reported as cancer."
    ))
    story.append(Paragraph("2.2 Loss and macro-F1", S["H2"]))
    story.append(P(
        "A convolution reads a local patch of the input feature map X with a kernel K of size k:"
    ))
    story.append(Paragraph(
        "Y(i, j) = sum_u sum_v  X(i+u, j+v) K(u, v).",
        S["Eq"],
    ))
    story.append(P("The nonlinearity used throughout both networks is the rectified linear unit,"))
    story.append(Paragraph("f(x) = max(0, x).", S["Eq"]))
    story.append(P(
        "Training minimises class-weighted cross-entropy. For a one-hot label y the loss on one "
        "image is"
    ))
    story.append(Paragraph(
        "L = - sum_c  w_c y_c log yhat_c,",
        S["Eq"],
    ))
    story.append(P(
        "where yhat is the softmax of the logits and the class weight is w_c = N / (C n_c), "
        "rescaled so that the weights average to 1. The quantity actually optimised is the mean "
        "of L over the batch. This is the formula above. It is not the default weighted loss in "
        "PyTorch, which also divides by the sum of the weights in the batch. The unit test checks "
        "that the implemented loss matches the formula on a hand-computed example."
    ))
    story.append(P("The selection metric, and the number reported in the tables, is macro-F1:"))
    story.append(Paragraph(
        "F1_macro = (1/C) sum_c  2 P_c R_c / (P_c + R_c).",
        S["Eq"],
    ))
    story.append(P(
        "Each class contributes the same amount, so a large nevus class cannot hide a weak "
        "melanoma class. Where every class appears in the test predictions, one-versus-rest "
        "ROC-AUC is also computed and averaged with the macro rule. If a class is missing, "
        "the AUC is left blank rather than forced."
    ))
    story.append(Paragraph("2.3 Architectures and the training algorithm", S["H2"]))
    story.append(P(
        "The baseline is a four-block CNN. Each of the first three blocks is a 3 x 3 convolution, "
        "a ReLU, and a 2 x 2 max pool, with 32, 64, and 128 channels. A fourth 3 x 3 convolution "
        "produces 256 channels, followed by global average pooling, dropout 0.3, and a linear "
        "layer. It has about 0.39 million parameters and no external pretraining."
    ))
    story.append(P(
        "The comparison model is ResNet18 [2]. ImageNet weights initialise the residual backbone. "
        "The original 1000-way layer is replaced by dropout 0.3 and a linear layer of width C. "
        "In the frozen configuration every backbone weight is held fixed, including the batch-norm "
        "buffers, and only the new head is trained. In the fine-tuned configuration every weight "
        "is updated at a learning rate ten times smaller than the head-only run. Residual "
        "connections let the deeper network train without the degradation that a plain stack of "
        "the same depth would show [2]."
    ))
    story.append(P("Algorithm 1 is one cell of the study. It is repeated for every dataset, configuration, and seed."))
    story.append(Paragraph(
        "Algorithm 1. Train and score one configuration.<br/>"
        "Input: fixed split of dataset D, configuration C, seed s.<br/>"
        "1. Load the split file. Do not draw a new split.<br/>"
        "2. Build the model for C and set the random seed to s.<br/>"
        "3. Optimise AdamW (weight decay 10<sup>-4</sup>) with cosine decay of the learning rate to 10<sup>-6</sup>.<br/>"
        "4. After each epoch, compute validation macro-F1. Keep the weights if the gain exceeds 0.001.<br/>"
        "5. Stop after three epochs without that gain, or at the epoch cap (10 for the custom CNN, 8 for ResNet18).<br/>"
        "6. Restore the best epoch. Score the untouched test set once. Save metrics, curves, the confusion matrix, and Grad-CAM on the most confident mistakes.",
        S["Algo"],
    ))
    story.append(Paragraph("2.4 Complexity", S["H2"]))
    story.append(P(
        "One convolutional layer with spatial size H x W, C_in input channels, C_out output "
        "channels, and a k x k kernel costs about O(H W C_in C_out k<sup>2</sup>) multiply-adds. "
        "The custom CNN applies this four times and then pools. After three stride-2 pools a "
        "224 x 224 input is 28 x 28, so the last convolution dominates that network. ResNet18 "
        "repeats residual blocks through 18 layers and stores 11.18 million parameters. Freezing "
        "the backbone leaves only the classification head trainable: 512 C + C weights, which is "
        "2,052 weights for four brain classes and 4,104 weights for eight breast classes. That is "
        "why the frozen run is cheaper to train even though a forward pass still executes the "
        "whole backbone. Measured single-image inference on the test set is about 1.4-1.6 ms for "
        "the custom CNN and about 3.0-4.2 ms for ResNet18."
    ))
    story.append(Paragraph("2.5 Early stopping and what is held fixed", S["H2"]))
    story.append(P(
        "The epoch that is scored is the one with the highest validation macro-F1, not the last "
        "epoch and not the epoch with the highest accuracy. A later epoch is kept only when "
        "macro-F1 rises by more than 0.001. Three epochs without that rise end the run. The "
        "custom CNN may train for 10 epochs and ResNet18 for 8. Restoring the best epoch, "
        "rather than the last one, is what stops a late drop in the rare classes from becoming "
        "the reported model."
    ))
    story.append(P(
        "Three things stay fixed while the strategy changes. The split file is loaded, never "
        "redrawn, so seed 123 and seed 2026 see the same test images as seed 42. The class "
        "weights are computed on the training counts of that file. The evaluation transform is "
        "resize, conversion to a tensor, and ImageNet normalisation. Random flips, rotations, "
        "and colour jitter exist only inside the training loader of the configurations that "
        "turn augmentation on. The unaugmented fine-tune is the cell in which every training "
        "image is a deterministic resize."
    ))

    story.append(Paragraph("3. Implementation", S["H1"]))
    story.append(Paragraph("3.1 Datasets and splits", S["H2"]))
    story.append(P(
        "Table 1 lists the collections. Membership is written once to results/splits and reloaded "
        "afterwards, so a new seed changes initialisation and shuffle order, not which image is "
        "in the test set. A checker refuses to train if the same path, or the same BreakHis "
        "patient id, appears in two splits."
    ))
    story.append(table(
        ["Dataset", "Task", "Train / val / test", "Grouping"],
        [
            ["Brain MRI [public]", "4 tumour categories", "4855 / 857 / 1311", "Image. No patient id."],
            ["BreakHis [4]", "8 subtypes", "4973 / 1399 / 1537", "Patient. 54 / 14 / 14."],
            ["DermaMNIST [5], [6]", "7 lesion types", "7007 / 1003 / 2005", "Official split."],
            ["IQ-OTH/NCCD [7]", "Normal, benign, malignant", "767 / 165 / 165", "Image. No patient id."],
        ],
        [3.6 * cm, 3.8 * cm, 4.2 * cm, 5.8 * cm],
        "Table 1. Collections, counts, and whether a patient-level split could be verified.",
    ))
    story.append(P(
        "BreakHis is the only collection in which patient independence was verified. Every "
        "magnification of one patient stays in one split [4]. DermaMNIST is not reshuffled, but "
        "the arrays do not contain the HAM10000 lesion id, so two images of one lesion may still "
        "cross the cut [5], [6]. Brain filenames are sequential slice indexes such as Tr-gl_0505. "
        "The official Testing folder is held out and 15 percent of the official Training folder, "
        "stratified, is validation. That does not stop two slices of one scan from landing in "
        "both sets [3]. On IQ-OTH/NCCD the number in a filename such as \"Bengin case (85)\" is "
        "unique inside its class and runs from 1 to the class count. It is an image index. The "
        "public release has no subject id, and slice-level scores on this collection are known "
        "to be optimistic relative to a patient-level protocol [7]."
    ))
    story.append(Paragraph("3.2 Preprocessing, augmentation, and the machine", S["H2"]))
    story.append(P(
        "Every model sees a 224 x 224 RGB image normalised with the ImageNet mean "
        "(0.485, 0.456, 0.406) and standard deviation (0.229, 0.224, 0.225). Using one pipeline "
        "keeps the comparison on the training strategy. Augmentation is applied to training "
        "images only, and it is not the same for every modality. Histopathology may be flipped "
        "horizontally and vertically, rotated by up to 20 degrees, and jittered in brightness "
        "and contrast. Dermoscopy may be flipped horizontally, rotated by up to 15 degrees, and "
        "jittered in brightness, contrast, and saturation. Hue is not changed, because stain and "
        "lesion colour carry category information. MRI is rotated by up to 10 degrees and CT by "
        "up to 8 degrees. Neither is flipped, because left and right are anatomical."
    ))
    story.append(P(
        "The runs used Python 3.13 and PyTorch 2.15 on Apple Silicon (MPS), batch size 32, and "
        "AdamW. The custom CNN learning rate is 10<sup>-3</sup>. The frozen head uses 10<sup>-3</sup>. "
        "Fine-tuning uses 10<sup>-4</sup>. Seeds are 42, 123, and 2026. The full grid is "
        "4 configurations x 3 seeds x 4 datasets = 48 runs. Table 2 records the settings that "
        "were not allowed to vary inside a cell."
    ))
    story.append(table(
        ["Setting", "Custom CNN", "Frozen ResNet18", "Fine-tuned ResNet18"],
        [
            ["Initialisation", "Random", "ImageNet", "ImageNet"],
            ["Trainable weights", "All, about 0.39M", "Head only", "All, 11.18M"],
            ["Learning rate", "0.001", "0.001", "0.0001"],
            ["Epoch cap", "10", "8", "8"],
            ["Optimiser", "AdamW, decay 0.0001", "AdamW, decay 0.0001", "AdamW, decay 0.0001"],
            ["Schedule", "Cosine to 0.000001", "Cosine to 0.000001", "Cosine to 0.000001"],
            ["Batch / input", "32 / 224", "32 / 224", "32 / 224"],
            ["Selection", "Val. macro-F1", "Val. macro-F1", "Val. macro-F1"],
        ],
        [3.4 * cm, 4.6 * cm, 4.6 * cm, 4.8 * cm],
        "Table 2. Settings held fixed inside each configuration. The augmentation switch is the extra factor for the fine-tuned model.",
    ))
    story.append(Paragraph("3.3 The demonstration page", S["H2"]))
    story.append(P(
        "The Gradio page loads one checkpoint per dataset: the fine-tuned, augmented run whose "
        "validation macro-F1 was best among the three seeds. It does not retrain, and it does "
        "not load a second network for the coarser label. After the category softmax, the page "
        "adds the probabilities of the categories that the dataset maps to one group. Table 3 "
        "is that map. A brain tumour is reported as a tumour, not as cancer, because the MRI "
        "folders do not carry a benign or malignant label. Actinic keratosis is precancerous; "
        "it is placed in the cancer-related group only because that is the convention of the "
        "HAM10000 release, and the page says so [5]. "
        "Anyone can open the page at "
        '<link href="https://1a13cc7bc797761295.gradio.live" color="blue">'
        "https://1a13cc7bc797761295.gradio.live</link>. "
        "The same page runs on this machine at http://127.0.0.1:7860."
    ))
    story.append(table(
        ["Dataset", "Group shown beside the category", "How it is obtained"],
        [
            ["Brain MRI", "Tumour or no tumour", "Sum of the three tumour probabilities"],
            ["BreakHis", "Benign or malignant", "Sum of the four subtype probabilities"],
            ["DermaMNIST", "Cancer-related or not", "Sum of akiec, bcc, and melanoma"],
            ["Lung CT", "Malignant or not", "The malignant probability alone"],
        ],
        [3.2 * cm, 5.4 * cm, 8.8 * cm],
        "Table 3. The coarser label is a sum of category probabilities, not a second trained model.",
    ))
    story.append(P(
        "The same page draws Grad-CAM from the last convolutional layer [8]. The map is the "
        "gradient of the winning class with respect to that layer, pooled and drawn over the "
        "input. It shows which features moved the winning logit. It is not a segmentation of "
        "the lesion, and the caption on the page says that a match to a training folder is not "
        "a diagnosis. Figures 1 and 2 are four held-out test images run through that page. "
        "The left half of each panel is the uploaded image. The right half is the Grad-CAM "
        "the page draws for the winning category."
    ))
    story.append(figure_pair(
        DEMO / "demo_brain.png",
        DEMO / "demo_breast.png",
        "Figure 1. Demonstration page. Brain MRI: pituitary tumour, group Tumour, 100%. Breast histopathology: adenosis, group Benign, 65.7% (the benign group sums to 67.7%).",
    ))
    story.append(figure_pair(
        DEMO / "demo_skin.png",
        DEMO / "demo_lung.png",
        "Figure 2. Demonstration page. Skin: the true label is melanoma, and the page returns benign keratosis-like lesions at 82.1%, group Not cancer-related. Lung CT: malignant, group Malignant, 99.5%. One image is not the test average.",
    ))

    story.append(Paragraph("4. Experimental results", S["H1"]))
    story.append(P(
        "Table 4 is the primary result. Each cell is the test macro-F1 mean +/- the sample "
        "standard deviation across the three seeds. "
        "Fine-tuning wins on every modality, which supports H1. Figure 3 shows the same comparison. The margin is not uniform, "
        "which supports H3. On skin, the frozen ResNet18 (0.344) does not beat the custom CNN "
        "(0.371). ImageNet features held completely fixed are a weak description of a dermoscopic "
        "lesion; adapting the backbone is what moves the score to 0.719."
    ))
    story.append(table(
        ["Dataset", "Custom CNN", "Frozen ResNet18", "Fine-tuned ResNet18"],
        [
            ["Brain MRI", "0.724 +/- 0.011", "0.837 +/- 0.002", "0.989 +/- 0.004"],
            ["Breast", "0.272 +/- 0.016", "0.349 +/- 0.024", "0.506 +/- 0.031"],
            ["Skin", "0.371 +/- 0.009", "0.344 +/- 0.008", "0.719 +/- 0.014"],
            ["Lung CT", "0.366 +/- 0.044", "0.617 +/- 0.034", "0.946 +/- 0.021"],
        ],
        [3.6 * cm, 4.6 * cm, 4.6 * cm, 4.6 * cm],
        "Table 4. Test macro-F1, mean +/- sample standard deviation, three seeds.",
    ))
    story.append(figure(
        PLOTS / "macro_f1_comparison.png",
        "Figure 3. Test macro-F1 by modality and training strategy. Error is not drawn on the bars; Table 4 gives the standard deviation.",
    ))
    story.append(P(
        "Accuracy, the secondary metric, tells a softer story and supports H4. Skin accuracy "
        "for the fine-tuned model is 0.787 +/- 0.010, while macro-F1 is 0.719. Nevi are 1,341 "
        "of 2,005 test images, so a model can be right often and still weak on melanoma "
        "(F1 0.568). Breast accuracy is 0.581 +/- 0.020 against macro-F1 0.506, because ductal "
        "carcinoma is common and phyllodes tumour is effectively missed. One-versus-rest macro "
        "AUC for the fine-tuned model is about 1.000 on brain MRI, 0.852 on breast, 0.965 on "
        "skin, and 0.999 on lung CT. AUC stays high when the ranking of a rare class is decent "
        "even if the decision threshold, pushed by class weights, is not."
    ))
    story.append(Paragraph("4.1 Augmentation ablation", S["H2"]))
    story.append(P(
        "Table 5 isolates augmentation. Both columns fine-tune ResNet18 at the same learning "
        "rate, on the same split, with the same seeds. Only the training transform changes. "
        "H2 is supported on breast, where augmentation raises macro-F1 from 0.462 to 0.506, "
        "and it is weakly supported on brain MRI (0.985 to 0.989). It is not supported on skin "
        "or lung CT, where the unaugmented fine-tune is higher (0.762 and 0.992). Those two "
        "gaps are larger than the seed standard deviations, so they are not noise. Colour and "
        "geometry changes that are harmless on natural photographs can move a stain or a lesion "
        "away from the test distribution. H3 follows: the useful recipe is not the same recipe "
        "on every modality."
    ))
    story.append(table(
        ["Dataset", "With augmentation", "Without augmentation"],
        [
            ["Brain MRI", "0.989 +/- 0.004", "0.985 +/- 0.006"],
            ["Breast", "0.506 +/- 0.031", "0.462 +/- 0.024"],
            ["Skin", "0.719 +/- 0.014", "0.762 +/- 0.022"],
            ["Lung CT", "0.946 +/- 0.021", "0.992 +/- 0.007"],
        ],
        [4.4 * cm, 6.5 * cm, 6.5 * cm],
        "Table 5. Ablation of training augmentation for fine-tuned ResNet18. Test macro-F1.",
    ))
    story.append(figure(
        PLOTS / "brain__finetune_aug__seed42_curves.png",
        "Figure 4. Brain MRI, fine-tuned ResNet18 with augmentation, seed 42. The dashed line is the epoch restored for the test score. Training loss keeps falling after validation macro-F1 has flattened.",
    ))
    story.append(P(
        "Figure 4 is representative of the fine-tuned brain runs. Validation macro-F1 is already "
        "0.971 after one epoch and 0.992 at the restored epoch. The custom CNN on the same split "
        "needs the full ten epochs to reach a test macro-F1 near 0.72. Mean training time for a "
        "brain run is 322 s for the custom CNN, 209 s for the frozen head, and 273 s for "
        "fine-tuning. Lung runs finish in under a minute because the training set has 767 images. "
        "Breast runs take 378-468 s. Figure 5 is the brain confusion matrix for the same run: "
        "almost every test slice sits on the diagonal, and the visible exchanges are glioma with meningioma."
    ))
    story.append(figure(
        PLOTS / "brain__finetune_aug__seed42_confusion.png",
        "Figure 5. Brain MRI confusion matrix, fine-tuned ResNet18 with augmentation, seed 42.",
    ))
    story.append(Paragraph("4.2 Where the errors sit", S["H2"]))
    story.append(P(
        "Tables 6 and 7 break the fine-tuned, augmented model into classes. Support is the "
        "test count, which does not change with the seed. F1 is the mean across the three seeds. "
        "On BreakHis the headline 0.506 is an average of a strong adenosis class and a phyllodes "
        "class that the model does not detect. On DermaMNIST the headline 0.719 is pulled up by "
        "1,341 nevi and pulled down by melanoma, whose precision is 0.484."
    ))
    story.append(table(
        ["BreakHis class", "n", "Precision", "Recall", "F1"],
        [
            ["Adenosis", "132", "0.810", "0.831", "0.820 +/- 0.068"],
            ["Fibroadenoma", "247", "0.492", "0.706", "0.579 +/- 0.040"],
            ["Phyllodes tumour", "235", "0.021", "0.004", "0.007 +/- 0.012"],
            ["Tubular adenoma", "65", "0.750", "0.692", "0.710 +/- 0.103"],
            ["Ductal carcinoma", "583", "0.817", "0.718", "0.764 +/- 0.008"],
            ["Lobular carcinoma", "123", "0.395", "0.515", "0.445 +/- 0.066"],
            ["Mucinous carcinoma", "62", "0.270", "0.527", "0.357 +/- 0.030"],
            ["Papillary carcinoma", "90", "0.284", "0.530", "0.369 +/- 0.032"],
        ],
        [4.6 * cm, 2.0 * cm, 3.2 * cm, 2.8 * cm, 4.8 * cm],
        "Table 6. BreakHis per-class scores for fine-tuned ResNet18 with augmentation.",
    ))
    story.append(table(
        ["DermaMNIST class", "n", "Precision", "Recall", "F1"],
        [
            ["Actinic keratosis / IEC", "66", "0.775", "0.576", "0.658 +/- 0.026"],
            ["Basal cell carcinoma", "103", "0.658", "0.867", "0.747 +/- 0.031"],
            ["Benign keratosis", "220", "0.553", "0.833", "0.664 +/- 0.009"],
            ["Dermatofibroma", "23", "0.527", "0.855", "0.652 +/- 0.033"],
            ["Melanoma", "223", "0.484", "0.691", "0.568 +/- 0.002"],
            ["Melanocytic nevi", "1341", "0.973", "0.796", "0.875 +/- 0.014"],
            ["Vascular lesions", "29", "0.828", "0.908", "0.865 +/- 0.058"],
        ],
        [4.6 * cm, 2.0 * cm, 3.2 * cm, 2.8 * cm, 4.8 * cm],
        "Table 7. DermaMNIST per-class scores for fine-tuned ResNet18 with augmentation.",
    ))
    story.append(P(
        "Brain MRI and lung CT look even in the same breakdown, which is why H4 is quiet there. "
        "Glioma, meningioma, pituitary tumour, and no tumour have F1 0.986, 0.979, 0.994, and "
        "0.997. Lung normal, benign, and malignant have F1 0.962, 0.882, and 0.992. The benign "
        "lung number rests on 18 test slices. A change of one or two slices moves it by more "
        "than the gap between the other two classes."
    ))
    story.append(Paragraph("4.3 Cost of the three strategies", S["H2"]))
    story.append(P(
        "Table 8 is the practical companion to the macro-F1 table. Times are means over the "
        "three seeds on the same Apple Silicon machine. The frozen head is the shortest brain "
        "and skin run because the backward pass does not touch 11 million weights. It is not "
        "the shortest breast run: that set is large, the head has eight outputs, and early "
        "stopping lets the fine-tuned model leave after about two epochs while the frozen head "
        "keeps going. Inference stays near 3 ms for every ResNet18 and near 1.5 ms for the "
        "custom CNN, so the accuracy gap is not bought with a slower demo."
    ))
    story.append(table(
        ["Dataset", "Custom CNN", "Frozen head", "Fine-tune + aug."],
        [
            ["Brain MRI", "322 s, AUC 0.911", "209 s, AUC 0.958", "273 s, AUC 1.000"],
            ["Breast", "445 s, AUC 0.766", "468 s, AUC 0.818", "378 s, AUC 0.852"],
            ["Skin", "394 s, AUC 0.856", "212 s, AUC 0.857", "406 s, AUC 0.965"],
            ["Lung CT", "39 s, AUC 0.662", "36 s, AUC 0.905", "56 s, AUC 0.999"],
        ],
        [3.4 * cm, 4.6 * cm, 4.6 * cm, 4.8 * cm],
        "Table 8. Mean training time and test macro one-versus-rest AUC. AUC is omitted from the primary claim because a missing class would leave it undefined; every class was present in these runs.",
    ))

    story.append(Paragraph("5. Discussion", S["H1"]))
    story.append(P(
        "H1 holds. H3 holds. H2 holds only for breast, and mildly for brain MRI. H4 holds on "
        "skin and breast, where accuracy and macro-F1 separate, and it is less informative on "
        "brain MRI, where the four classes are close in size and both scores sit near 0.99."
    ))
    story.append(P(
        "The brain result should not be read as a solved clinical problem. The most common "
        "confusion for the fine-tuned model is glioma predicted as meningioma, about five test "
        "images on average. Per-class F1 is 0.986 for glioma, 0.979 for meningioma, 0.994 for "
        "pituitary tumour, and 0.997 for no tumour. Those numbers are stable across seeds "
        "(standard deviations at most 0.007). Yagis et al. showed that this pattern, a 2D CNN "
        "near ceiling on MRI slices, is exactly what slice leakage produces [3]. The filenames "
        "do not let this project rule that explanation out."
    ))
    story.append(figure(
        PLOTS / "breast__finetune_aug__seed42_confusion.png",
        "Figure 6. BreakHis confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. Phyllodes tumour is almost absent from the diagonal.",
    ))
    story.append(P(
        "Breast is the honest stress test, because the split is patient-level [4]. Fine-tuned "
        "macro-F1 is only 0.506 +/- 0.031. Adenosis F1 is 0.820 and ductal carcinoma F1 is 0.764. "
        "Phyllodes tumour F1 is 0.007 +/- 0.012. On average about 143 of 235 phyllodes test "
        "slides are called fibroadenoma. The two benign fibroepithelial patterns are visually "
        "close. Phyllodes has the highest class weight, about 4.1, because the training split "
        "contains only 60 slides, and the model still does not detect the class. A larger weight "
        "cannot invent the pattern when no slide from a test patient was seen in training. Lobular, mucinous, and "
        "papillary carcinomas also sit below 0.45 F1. A report that quoted only the 0.581 accuracy "
        "would hide this. The next largest exchange is ductal carcinoma called lobular, about "
        "86 test slides, and the reverse, about 51. Those two malignant patterns share a "
        "staining appearance that a patient-held-out test does not let the model memorise."
    ))
    story.append(P(
        "The breast validation score explains the early stop. Mean validation macro-F1 for the "
        "augmented fine-tune is 0.259, while the test score is 0.506, and the best epoch is "
        "usually the first or the second. Training accuracy at the last epoch is still about "
        "0.88. The 14 validation patients are a harder draw than the 14 test patients. Early "
        "stopping is doing what it was asked to do on the validation file. It is also evidence "
        "that 14 patients is a thin estimate of a new hospital, which is the point of refusing "
        "an image-level split on this collection [4]."
    ))
    story.append(figure(
        PLOTS / "skin__finetune_aug__seed42_confusion.png",
        "Figure 7. DermaMNIST confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. The nevus column and row dominate the counts.",
    ))
    story.append(P(
        "On skin, the largest off-diagonal mass is melanocytic nevi predicted as melanoma, about "
        "140 test images on average, against 1,341 nevi. Melanoma recall is 0.691 but precision "
        "is only 0.484, so the class-weighted loss is buying recall by over-calling melanoma. "
        "Dermatofibroma has 23 test images; its F1 of 0.652 moves if a handful of cases flip. "
        "This is the setting H4 was written for. It is also the setting where augmentation hurt: "
        "the unaugmented fine-tune reaches macro-F1 0.762. A horizontal flip is reasonable for a "
        "lesion, but saturation jitter may be enough to blur the colour cues that separate "
        "keratosis, nevus, and melanoma."
    ))
    story.append(P(
        "Lung CT fine-tuning reaches macro-F1 0.946 with augmentation and 0.992 without it. "
        "Malignant F1 is 0.992. Benign F1 is 0.882, estimated on 18 test slices, and the main "
        "confusion is normal called benign (about three images). Eighteen slices cannot support "
        "a stable benign claim, and the missing patient id means neighbouring slices of one scan "
        "can sit in training and test [7]. The lung number is therefore an upper bound on what "
        "the same network would score on a new person, not a measurement of that score. "
        "Figure 8 shows how small that off-diagonal is on one seed: the mistakes are a few slices, not a class."
    ))
    story.append(figure(
        PLOTS / "lung__finetune_aug__seed42_confusion.png",
        "Figure 8. Lung CT confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. Benign has 18 test slices.",
    ))
    story.append(figure(
        GRADCAM / "breast__finetune_aug__seed42.png",
        "Figure 9. Grad-CAM on high-confidence BreakHis mistakes for the fine-tuned model, seed 42. The heat map marks features that moved the winning logit. It is not a tumour outline [8].",
    ))
    story.append(P(
        "Figure 9 is the failure view required by the assignment, not a gallery of easy successes. "
        "The saved grids in results/gradcam do the same for the other datasets. Where the heat "
        "sits on the tissue rather than on the slide border, the mistake is a genuine look-alike "
        "class, as with phyllodes and fibroadenoma. Where it sits on background, the prediction "
        "is using a cue that will not survive a new scanner or a new stain. Figures 10 and 11 "
        "are the same view for skin and lung CT."
    ))
    story.append(figure(
        GRADCAM / "skin__finetune_aug__seed42.png",
        "Figure 10. Grad-CAM on high-confidence DermaMNIST mistakes, fine-tuned ResNet18 with augmentation, seed 42.",
        height=7.4 * cm,
    ))
    story.append(figure(
        GRADCAM / "lung__finetune_aug__seed42.png",
        "Figure 11. Grad-CAM on high-confidence lung CT mistakes, fine-tuned ResNet18 with augmentation, seed 42.",
        height=7.4 * cm,
    ))

    story.append(Paragraph("6. Tests and ethics", S["H1"]))
    story.append(P(
        "The automated checks do not need the image files. They confirm that the custom CNN "
        "maps a 2 x 3 x 224 x 224 batch to 2 x 4 logits, that a frozen ResNet18 trains only the "
        "2,052 head weights of a four-class problem, and that the weighted loss equals the "
        "hand-computed formula. A synthetic nine-patient split is rejected if any patient id "
        "appears twice. MRI and CT training transforms are checked for the absence of a "
        "horizontal flip, and the evaluation transform is checked to be resize, tensor conversion, "
        "and normalisation only. A toy prediction vector checks that macro-F1 does not collapse "
        "to accuracy when one class is easier than the other. These tests live in tests/test_core.py "
        "and are executed from the notebook."
    ))
    story.append(P(
        "The images are not redistributed. Brain MRI is used under CC BY 4.0. HAM10000, and "
        "therefore DermaMNIST, is CC BY-NC 4.0 [5]. BreakHis is the UFPR research release [4]. "
        "IQ-OTH/NCCD is a de-identified teaching collection; the public folders still do not "
        "support a patient-level audit [7]. No new patient data were collected. The Gradio page "
        "states that a score is a match to a training folder, not a diagnosis, not a risk, and "
        "not an input to a health decision. Actinic keratoses are precancerous; they are grouped "
        "as cancer-related only because that is the dataset convention, and the page says so."
    ))
    story.append(P(
        "Class weights reduce the chance that the loss is satisfied by the majority class, and "
        "they create the opposite bias: melanoma and the rare breast carcinomas are over-called. "
        "That trade is visible in precision and is preferable to a silent miss, but it must be "
        "described as a threshold choice, not as a calibrated probability. The study also cannot "
        "speak to scanner shift, skin tone, or age, because those attributes are not in the "
        "released labels."
    ))

    story.append(Paragraph("7. Conclusion", S["H1"]))
    story.append(P(
        "Fine-tuning ResNet18 is the best of the three training strategies on all four modalities. "
        "The test macro-F1 values are 0.989 +/- 0.004 (brain MRI), 0.506 +/- 0.031 (breast), "
        "0.719 +/- 0.014 (skin), and 0.946 +/- 0.021 (lung CT). A frozen backbone is a useful "
        "middle point on brain MRI and lung CT and is not useful on skin. Training augmentation "
        "helps the patient-level breast task and is neutral or harmful on skin and lung CT. "
        "Accuracy alone would have overstated the skin and breast models."
    ))
    story.append(P(
        "The limit that matters more than another point of macro-F1 is the split. Only BreakHis "
        "supports a patient-level claim, and on that set the headline score is about 0.51, with "
        "phyllodes tumour effectively unrecognised. Brain MRI and lung CT remain in the study "
        "with that limitation written down. A next experiment should replace those two "
        "collections with a release that carries a scan id, or should join HAM10000 lesion ids "
        "back to DermaMNIST before claiming that a test lesion is unseen. Until then the page "
        "that shows a prediction is a teaching demo."
    ))

    story.append(Paragraph("References", S["H1"]))
    refs = [
        "[1] H. E. Kim, A. Cosa-Linan, N. Santhanam, M. Jannesari, M. E. Maros, and T. Ganslandt, \"Transfer learning for medical image classification: A literature review,\" BMC Med. Imaging, vol. 22, no. 1, Art. no. 69, Apr. 2022, doi: 10.1186/s12880-022-00793-7.",
        "[2] K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 770-778.",
        "[3] E. Yagis et al., \"Effect of data leakage in brain MRI classification using 2D convolutional neural networks,\" Sci. Rep., vol. 11, Art. no. 22544, Nov. 2021, doi: 10.1038/s41598-021-01681-w.",
        "[4] F. A. Spanhol, L. S. Oliveira, C. Petitjean, and L. Heutte, \"A dataset for breast cancer histopathological image classification,\" IEEE Trans. Biomed. Eng., vol. 63, no. 7, pp. 1455-1462, Jul. 2016.",
        "[5] P. Tschandl, C. Rosendahl, and H. Kittler, \"The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions,\" Sci. Data, vol. 5, Art. no. 180161, 2018.",
        "[6] J. Yang et al., \"MedMNIST v2 - A large-scale lightweight benchmark for 2D and 3D biomedical image classification,\" Sci. Data, vol. 10, Art. no. 41, 2023.",
        "[7] A. Ahmad, M. U. Hashmi, M. Azam, R. Sarwar, and M. Ali, \"A leakage-free, patient-level evaluation protocol for multi-class lung CT diagnosis,\" Eng. Rep., 2026, doi: 10.1002/eng2.71054.",
        "[8] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618-626.",
    ]
    for ref in refs:
        story.append(Paragraph(ref, S["Ref"]))

    story.append(Paragraph("Appendix A. Critical code", S["H1"]))
    story.append(P(
        "The loss used in training is the batch mean of the weighted negative log-probability "
        "of the true class. The notebook and tests/test_core.py call this function directly."
    ))
    story.append(Paragraph(
        "def weighted_cross_entropy(logits, target, weight):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;log_probs = log_softmax(logits, dim=1)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;picked = log_probs.gather(1, target.view(-1, 1)).squeeze(1)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;return -(weight[target] * picked).mean()",
        S["Algo"],
    ))
    story.append(P(
        "The experiment grid is experiments/run_experiments.py. A finished metrics file is "
        "skipped unless --force is set, so an interrupted study resumes instead of repeating "
        "a seed. The test loader is opened only after the best validation epoch has been restored."
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUT)


if __name__ == "__main__":
    build()
