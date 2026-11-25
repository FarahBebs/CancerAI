"""Build the BIL458 report PDF from the saved experiment files."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# reportlab is not in requirements.txt; point CV_PYDEPS at a folder that has it if needed.
sys.path.insert(0, os.environ.get("CV_PYDEPS", "/tmp/cv-pydeps"))

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
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
LOGO = DEMO / "ium_logo.png"
NB_GITHUB = "https://github.com/FarahBebs/CancerAI/blob/main/notebooks/BIL458_CancerAI_Experiments.ipynb"
NB_COLAB = "https://colab.research.google.com/github/FarahBebs/CancerAI/blob/main/notebooks/BIL458_CancerAI_Experiments.ipynb"

# Colours and fonts follow the course report template (navy headings, navy table heads, light rows).
NAVY = colors.HexColor("#1F2A5C")
TEAL = colors.HexColor("#2B3A7A")
ACCENT = colors.HexColor("#C0504D")
RULE = colors.HexColor("#C9CCD8")
ROW = colors.HexColor("#EEF0F7")
MUTED = colors.HexColor("#5A6078")

_FONT_DIR = Path("/System/Library/Fonts/Supplemental")
for _name, _file in (
    ("TNR", "Times New Roman.ttf"),
    ("TNR-Bold", "Times New Roman Bold.ttf"),
    ("TNR-Italic", "Times New Roman Italic.ttf"),
    ("TNR-BoldItalic", "Times New Roman Bold Italic.ttf"),
):
    pdfmetrics.registerFont(TTFont(_name, str(_FONT_DIR / _file)))
pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic")

COURSE = "BİL458 Computer Vision"
FOOTER = "BİL458 Computer Vision · Project Report · Assoc. Prof. Dr. Murat GEZER"


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        "CoverKicker", fontName="TNR-Bold", fontSize=11, textColor=TEAL,
        alignment=TA_CENTER, spaceAfter=8, tracking=1,
    ))
    base.add(ParagraphStyle(
        "CoverTitle", fontName="TNR-Bold", fontSize=18, leading=23,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
    ))
    base.add(ParagraphStyle(
        "CoverMeta", fontName="TNR", fontSize=12, leading=16,
        alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "CoverLink", fontName="TNR", fontSize=9, leading=12,
        alignment=TA_CENTER, textColor=colors.HexColor("#1a4f8b"), spaceAfter=6,
    ))
    base.add(ParagraphStyle(
        "BodyLink", fontName="TNR", fontSize=9, leading=12,
        alignment=TA_CENTER, textColor=colors.HexColor("#1a4f8b"),
        spaceBefore=2, spaceAfter=8,
    ))
    base.add(ParagraphStyle(
        "H1", fontName="TNR-Bold", fontSize=14, leading=18, textColor=NAVY,
        spaceBefore=14, spaceAfter=6,
    ))
    base.add(ParagraphStyle(
        "H2", fontName="TNR-Bold", fontSize=12, leading=15, textColor=TEAL,
        spaceBefore=10, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Body", fontName="TNR", fontSize=11, leading=14.5,
        alignment=TA_JUSTIFY, spaceAfter=8,
    ))
    base.add(ParagraphStyle(
        "Eq", fontName="TNR-Italic", fontSize=11, leading=14,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Caption", fontName="TNR-Italic", fontSize=9, leading=12,
        alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=10,
    ))
    base.add(ParagraphStyle(
        "Cell", fontName="TNR", fontSize=8.5, leading=11,
    ))
    base.add(ParagraphStyle(
        "CellHead", fontName="TNR-Bold", fontSize=8.5, leading=11, textColor=colors.white,
    ))
    base.add(ParagraphStyle(
        "Ref", fontName="TNR", fontSize=10, leading=13, leftIndent=14,
        firstLineIndent=-14, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        "Algo", fontName="TNR", fontSize=10, leading=13, leftIndent=6,
    ))
    return base


S = styles()


def P(text):
    return Paragraph(text, S["Body"])


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(item, S["Body"]), leftIndent=8) for item in items],
        bulletType="bullet", start="-", leftIndent=16, bulletFontName="TNR",
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


def equation(latex: str, name: str, number: int | None = None):
    """Render one formula (same notation as the notebook) with its number on the right."""
    block = _equation_image(latex, name)
    if number is None:
        return block
    img = block._content[0]
    row = Table(
        [[Spacer(1, 1), img, Paragraph(f"({number})", S["Body"])]],
        colWidths=[1.6 * cm, 14.2 * cm, 1.6 * cm],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return KeepTogether([row, Spacer(1, 0.1 * cm)])


def _equation_image(latex: str, name: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folder = ROOT / "deliverables" / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    plt.rcParams["mathtext.fontset"] = "cm"
    fig = plt.figure(figsize=(0.2, 0.2))
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.5, f"${latex}$", fontsize=11, ha="center", va="center", color="black")
    fig.savefig(path, dpi=220, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    from PIL import Image as PILImage
    with PILImage.open(path) as rendered:
        px_w, px_h = rendered.size
    img = Image(str(path), width=px_w / 220 * 72, height=px_h / 220 * 72)
    return KeepTogether([img, Spacer(1, 0.15 * cm)])


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


class NumberedCanvas(rl_canvas.Canvas):
    """Draws the template header and a 'Page X / N' footer once the page count is known."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total):
        width, height = A4
        self.saveState()
        # Header, as in the course template: university at left, faculty block at right, navy rule.
        logo_h = 1.45 * cm
        logo_w = logo_h * 260 / 124
        self.drawImage(str(LOGO), 1.8 * cm, height - 0.55 * cm - logo_h, width=logo_w, height=logo_h, mask="auto")
        self.setFillColor(NAVY)
        self.setFont("TNR-Bold", 8)
        self.drawRightString(width - 1.8 * cm, height - 0.85 * cm, "FACULTY OF ENGINEERING AND NATURAL SCIENCES")
        self.drawRightString(width - 1.8 * cm, height - 1.17 * cm, "DEPARTMENT OF COMPUTER ENGINEERING")
        self.setFont("TNR", 7.5)
        self.setFillColor(MUTED)
        self.drawRightString(width - 1.8 * cm, height - 1.47 * cm, "2026–2027 ACADEMIC YEAR, FALL SEMESTER")
        self.setFillColor(NAVY)
        self.setFont("TNR-Bold", 9.5)
        self.drawRightString(width - 1.8 * cm, height - 1.85 * cm, "BİL458 — Computer Vision")
        self.setStrokeColor(NAVY)
        self.setLineWidth(1.2)
        self.line(1.8 * cm, height - 2.1 * cm, width - 1.8 * cm, height - 2.1 * cm)
        # Footer
        self.setFillColor(MUTED)
        self.setFont("TNR", 8.5)
        self.drawCentredString(width / 2, 1.0 * cm, f"{FOOTER} · Page {self._pageNumber} / {total}")
        self.restoreState()


def header_footer(canvas, doc):
    """Kept for compatibility; decoration is drawn by NumberedCanvas."""
    return None


def box_arrow_flow(steps, width, height=2.6 * cm):
    """A left-to-right flow diagram: one rounded box per step, arrows between them."""
    n = len(steps)
    gap = 0.55 * cm
    box_w = (width - gap * (n - 1)) / n
    d = Drawing(width, height)
    y0 = 0.15 * cm
    box_h = height - 0.3 * cm
    for i, (title, body, fill) in enumerate(steps):
        x = i * (box_w + gap)
        d.add(Rect(x, y0, box_w, box_h, rx=5, ry=5, fillColor=fill, strokeColor=NAVY, strokeWidth=0.8))
        d.add(String(x + box_w / 2, y0 + box_h - 0.5 * cm, title, fontName="TNR-Bold", fontSize=8.5,
                     fillColor=colors.white if fill == NAVY else NAVY, textAnchor="middle"))
        for k, line in enumerate(body):
            d.add(String(x + box_w / 2, y0 + box_h - 0.95 * cm - k * 0.36 * cm, line, fontName="TNR",
                         fontSize=7.2, fillColor=colors.white if fill == NAVY else colors.black, textAnchor="middle"))
        if i < n - 1:
            ax = x + box_w + 0.06 * cm
            ay = y0 + box_h / 2
            d.add(Line(ax, ay, ax + gap - 0.2 * cm, ay, strokeColor=ACCENT, strokeWidth=1.4))
            tip = ax + gap - 0.12 * cm
            d.add(Polygon([tip, ay, tip - 0.16 * cm, ay + 0.1 * cm, tip - 0.16 * cm, ay - 0.1 * cm],
                          fillColor=ACCENT, strokeColor=ACCENT))
    return d


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=2.6 * cm, bottomMargin=1.7 * cm,
        title="CancerAI: A Comparative Study of Deep Learning Strategies for Multi-Modal Medical Image Classification",
        author="Farah Alhasan",
    )
    story = []
    W = 17.4 * cm

    story.append(Spacer(1, 1.6 * cm))
    story.append(Image(str(LOGO), width=5.6 * cm, height=5.6 * cm * 124 / 260))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("BİL458 COMPUTER VISION", S["CoverTitle"]))
    story.append(Paragraph("Term Project Report", S["CoverMeta"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "CancerAI: A Comparative Study of Deep Learning Strategies for Multi-Modal Medical Image Classification",
        S["CoverTitle"],
    ))
    story.append(Spacer(1, 0.6 * cm))
    story.append(table(
        ["Team member", "Student no", "Contribution (task distribution)"],
        [[
            "Farah ALHASAN",
            "21120205709",
            "Individual project (100%): literature review, dataset audit and leak-free splits, "
            "model implementation, 48 training runs, evaluation, ablation and failure analysis, "
            "unit tests, Gradio demo, notebook, report and presentation.",
        ]],
        [3.6 * cm, 3.0 * cm, 10.8 * cm],
        "",
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Instructor: Assoc. Prof. Dr. Murat GEZER", S["CoverMeta"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Notebook: BIL458_CancerAI_Experiments.ipynb (uploaded to Classroom)",
        S["CoverLink"],
    ))
    story.append(Paragraph(
        "Open the notebook in Colab: "
        f'<link href="{NB_COLAB}" color="blue">{NB_COLAB}</link>',
        S["CoverLink"],
    ))
    story.append(Paragraph(
        "Notebook on GitHub: "
        f'<link href="{NB_GITHUB}" color="blue">{NB_GITHUB}</link>',
        S["CoverLink"],
    ))
    story.append(Paragraph(
        "Code repository: "
        '<link href="https://github.com/FarahBebs/CancerAI" color="blue">https://github.com/FarahBebs/CancerAI</link>',
        S["CoverLink"],
    ))
    story.append(PageBreak())

    story.append(Paragraph("Abstract", S["H1"]))
    abstract = (
        "Deep networks for medical image classification are often reported with very high accuracy, "
        "yet the training recipe and the way the data are split can change those numbers more than "
        "the architecture does. This study measures how the training strategy and training-time "
        "augmentation change multi-class classification on four separate medical image tasks. "
        "A four-block convolutional network trained from scratch is used as the baseline and is "
        "compared with an ImageNet-pretrained ResNet18 whose backbone is frozen and with a fully "
        "fine-tuned ResNet18; the fine-tuned model is trained once with and once without "
        "augmentation as an ablation. The data are brain MRI (four tumour categories), BreakHis "
        "breast histopathology (eight subtypes, split by patient), DermaMNIST skin lesions (seven "
        "types, official split) and IQ-OTH/NCCD lung CT (three categories). The split is written "
        "once and never redrawn, test images are never augmented, and every configuration is run "
        "with three seeds, giving 48 runs. The primary metric is macro-F1, reported as mean and "
        "standard deviation. Fine-tuning is best on every dataset, with test macro-F1 of "
        "0.989 ± 0.004 on brain MRI, 0.506 ± 0.031 on breast tissue, 0.719 ± 0.014 on skin and "
        "0.946 ± 0.021 on lung CT, against 0.272 to 0.724 for the baseline. Augmentation improves "
        "the patient-level breast task but lowers the skin and lung scores, so the best recipe "
        "depends on the modality. Accuracy hides a missed phyllodes class and over-called melanoma, "
        "which macro-F1 exposes. Only the breast result is a verified patient-level estimate."
    )
    story.append(P(abstract))
    story.append(Paragraph(
        "<b>Keywords:</b> medical image classification, transfer learning, ResNet18, data augmentation, "
        "macro-F1, data leakage.",
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
        "The existing approaches each have a known strength and a known weakness. Hand-crafted "
        "texture descriptors with classical classifiers were the first BreakHis baseline and reached "
        "about 80 to 85 percent patient-level accuracy on the benign/malignant task [4]; they need "
        "no GPU but do not transfer between modalities. Convolutional networks trained from scratch "
        "learn the features directly, but need far more labelled images than most medical "
        "collections offer. Transfer learning from ImageNet is the dominant remedy: the literature "
        "review of Kim et al. finds that fine-tuning a pretrained CNN is the most common and usually "
        "the strongest choice, while freezing the backbone is cheaper and less prone to overfitting "
        "on very small sets [1]. Benchmarks such as MedMNIST v2 compare architectures on a common "
        "split, but report accuracy and AUC rather than per-class behaviour [5], and many published "
        "results do not state whether the split keeps a patient on one side [3]."
    ))
    story.append(P(
        "This project keeps four collections and treats each as its own classification task. "
        "A brain tumour in the MRI set is not labelled benign or malignant, and several skin "
        "categories are not cancer. ResNet18 was chosen because it is the standard transfer-learning "
        "backbone in this literature, small enough to train 48 times on one laptop GPU, and has a "
        "clear last convolutional layer for Grad-CAM [2], [6]."
    ))
    story.append(P(
        "<b>Research question:</b> How do the CNN training strategy (from scratch, frozen ImageNet "
        "backbone, full fine-tuning) and training-time augmentation change test macro-F1 on four "
        "medical image modalities, and is the effect the same on each? The hypotheses are:"
    ))
    story.append(bullets([
        "H1. A fine-tuned ResNet18 will outscore a custom CNN (baseline) and a frozen ResNet18.",
        "H2. Training augmentation will improve the fine-tuned model, especially where a class is rare.",
        "H3. The size of that gain will depend on the modality.",
        "H4. Accuracy will hide weak minority classes that macro-F1 and per-class recall will show.",
    ]))
    story.append(Paragraph("<b>Contributions:</b>", S["Body"]))
    story.append(bullets([
        "A controlled comparison of three training strategies on four modalities with one fixed, "
        "audited split, one loss and three seeds (48 runs), reported as mean ± standard deviation "
        "with Welch t-tests.",
        "An augmentation ablation showing that the same augmentation helps one modality and hurts two.",
        "A failure analysis (per-class scores, confusion matrices, Grad-CAM on the most confident "
        "mistakes) that exposes classes hidden by accuracy.",
        "A leakage audit of every split, with only the verified patient-level result claimed as such, "
        "and a reproducible notebook, unit tests and a Gradio demonstration.",
    ]))

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
    story.append(Paragraph("2.2 Model, loss and metric", S["H2"]))
    story.append(P(
        "A convolution reads a local patch of the input feature map X with a kernel K of size k, "
        "and is followed by the rectified linear unit:"
    ))
    story.append(equation(
        r"Y(i,j)=\sum_{u=0}^{k-1}\;\sum_{v=0}^{k-1} X(i+u,j+v)\,K(u,v),\qquad f(x)=\max(0,x)",
        "eq_convolution.png", 1,
    ))
    story.append(P(
        "The network f<sub>θ</sub> maps an image to C logits z, and the class probabilities are "
        "p = softmax(z), p<sub>c</sub> = e<super>z<sub>c</sub></super> / Σ<sub>j</sub> e<super>z<sub>j</sub></super>. "
        "Training minimises class-weighted cross-entropy over a mini-batch of B images with true "
        "classes y<sub>b</sub>:"
    ))
    story.append(equation(
        r"\mathcal{L}(\theta)=-\dfrac{1}{B}\sum_{b=1}^{B} w_{y_b}\,\log p_{y_b}(x_b;\theta),"
        r"\qquad w_c=\dfrac{N}{C\,n_c}",
        "eq_loss.png", 2,
    ))
    story.append(P(
        "where N is the number of training images and n<sub>c</sub> the number in class c; the "
        "weights are rescaled to average 1, so a rare class such as phyllodes tumour (60 training "
        "slides) receives w ≈ 4.1 while ductal carcinoma (2,350 slides) receives w ≈ 0.10. This "
        "is the formula above. It is not the default weighted loss in PyTorch, which also divides "
        "by the sum of the weights in the batch; a unit test checks the implementation against a "
        "hand-computed example. The gradient with respect to the logits of one image is"
    ))
    story.append(equation(
        r"\dfrac{\partial \mathcal{L}}{\partial z_{b,j}}=\dfrac{w_{y_b}}{B}\,\left(p_{b,j}-\delta_{j\,y_b}\right)",
        "eq_grad.png", 3,
    ))
    story.append(P(
        "where δ is the Kronecker delta (1 when j is the true class, 0 otherwise). The class weight "
        "therefore simply scales the usual softmax error: a misclassified rare-class "
        "image pushes the parameters about forty times harder than a misclassified ductal image. "
        "The parameters are updated with AdamW [7] (decoupled weight decay λ = 10<super>-4</super>), "
        "whose step on parameter θ with bias-corrected moments m̂ and v̂ is"
    ))
    story.append(equation(
        r"\theta_{t+1}=\theta_t-\eta_t\left(\dfrac{\hat m_t}{\sqrt{\hat v_t}+\epsilon}+\lambda\,\theta_t\right),"
        r"\qquad \eta_t=\eta_{min}+\frac{1}{2}(\eta_0-\eta_{min})\left(1+\cos\frac{\pi t}{T}\right)",
        "eq_adamw.png", 4,
    ))
    story.append(P(
        "with cosine decay from η<sub>0</sub> to η<sub>min</sub> = 10<super>-6</super>. The selection "
        "metric, and the number reported in the tables, is macro-F1, where P<sub>c</sub> and "
        "R<sub>c</sub> are the precision and recall of class c:"
    ))
    story.append(equation(
        r"F1_{macro}=\frac{1}{C}\sum_{c=1}^{C}\frac{2 P_c R_c}{P_c+R_c},\qquad "
        r"P_c=\frac{TP_c}{TP_c+FP_c},\quad R_c=\frac{TP_c}{TP_c+FN_c}",
        "eq_f1.png", 5,
    ))
    story.append(P(
        "Each class contributes the same amount, so a large nevus class cannot hide a weak "
        "melanoma class. Where every class appears in the test predictions, one-versus-rest "
        "ROC-AUC is also computed and averaged with the macro rule. Grad-CAM [6] explains a "
        "prediction of class c from the last convolutional feature maps A<super>k</super> "
        "(Z spatial positions):"
    ))
    story.append(equation(
        r"\alpha_k^c=\dfrac{1}{Z}\sum_{i}\sum_{j}\dfrac{\partial z_c}{\partial A^k_{ij}},\qquad "
        r"L^c_{\mathrm{GradCAM}}=\mathrm{ReLU}\left(\sum_k \alpha_k^c A^k\right)",
        "eq_gradcam.png", 6,
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
    story.append(P(
        "Algorithm 1 is one cell of the study. It is repeated for every dataset, configuration, "
        "and seed, and Figure 1 shows the whole system from data to evaluation."
    ))
    algo = Table([[Paragraph(
        "<b>Algorithm 1: Train and score one configuration</b><br/>"
        "<b>Input:</b> fixed split (D<sub>tr</sub>, D<sub>val</sub>, D<sub>test</sub>) of dataset D, configuration c, seed s, "
        "learning rate η<sub>0</sub>, epoch cap E<br/>"
        "1: load the split file (never redrawn); assert no image or patient is in two splits<br/>"
        "2: build f<sub>θ</sub> for c (random init or ImageNet); set seed s; best ← 0; wait ← 0<br/>"
        "3: <b>for</b> e = 1 … E <b>do</b><br/>"
        "4: &nbsp;&nbsp;&nbsp;<b>for each</b> mini-batch (X, y) from D<sub>tr</sub> (augmented if c uses augmentation) <b>do</b><br/>"
        "5: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;θ ← AdamW step with gradient ∂<i>L</i>/∂θ of <i>L</i>(θ; X, y) and rate η<sub>e</sub> &nbsp;&nbsp;// Eq. (2)–(4)<br/>"
        "6: &nbsp;&nbsp;&nbsp;F ← macro-F1 of f<sub>θ</sub> on D<sub>val</sub> &nbsp;&nbsp;// Eq. (5)<br/>"
        "7: &nbsp;&nbsp;&nbsp;<b>if</b> F &gt; best + 0.001 <b>then</b> best ← F; θ* ← θ; wait ← 0 <b>else</b> wait ← wait + 1<br/>"
        "8: &nbsp;&nbsp;&nbsp;<b>if</b> wait = 3 <b>then break</b><br/>"
        "9: θ ← θ*; score D<sub>test</sub> once; save metrics, curves, confusion matrix, Grad-CAM of the most confident mistakes<br/>"
        "<b>Output:</b> trained model f<sub>θ*</sub> and its test metrics",
        S["Algo"],
    )]], colWidths=[W])
    algo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROW),
        ("LINEBEFORE", (0, 0), (0, -1), 3, NAVY),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether([algo, Spacer(1, 0.3 * cm)]))
    story.append(KeepTogether([
        box_arrow_flow([
            ("1. Data", ["4 collections", "split once to file", "leakage check"], ROW),
            ("2. Pre-processing", ["resize 224×224", "ImageNet normalise", "augment (train only)"], ROW),
            ("3. Model", ["custom CNN /", "frozen ResNet18 /", "fine-tuned ResNet18"], NAVY),
            ("4. Training", ["weighted CE, AdamW", "cosine LR, early stop", "on val. macro-F1"], ROW),
            ("5. Post-processing", ["softmax, argmax", "group = sum of probs", "Grad-CAM"], ROW),
            ("6. Evaluation", ["test set once", "macro-F1, acc., AUC", "3 seeds, mean ± std"], ROW),
        ], W, height=2.5 * cm),
        Paragraph("Figure 1. System flow diagram: data → pre-processing → model → training → post-processing → evaluation.", S["Caption"]),
    ]))
    story.append(Paragraph("2.4 Complexity analysis", S["H2"]))
    story.append(P(
        "The asymptotic (Big-O) cost of one convolutional layer with an H × W output, C<sub>in</sub> input channels, C<sub>out</sub> "
        "output channels and a k × k kernel is"
    ))
    story.append(equation(r"O(H\,W\,k^{2}\,C_{in}\,C_{out})", "eq_cost.png", 7))
    story.append(P(
        "multiply-accumulate operations (MACs), and a forward pass is the sum over layers. In the "
        "custom CNN three stride-2 pools reduce a 224 × 224 input to 28 × 28, so the cost is "
        "dominated by the second and third convolutions. ResNet18 stacks eight residual blocks "
        "(18 weight layers) and stores 11.18 million parameters. Freezing the backbone leaves only "
        "the head trainable, 512C + C weights (2,052 for four brain classes, 4,104 for eight breast "
        "classes), so the backward pass is almost free although the forward pass still runs the "
        "whole backbone. Training costs O(E · N · M) for E epochs, N training images and M MACs per "
        "image (the backward pass is roughly twice the forward pass); Grad-CAM adds one backward "
        "pass to the last convolution per explained image. Table 1 gives the measured values; the "
        "MAC count uses forward hooks on every convolution and linear layer and is reproduced in "
        "the notebook."
    ))
    story.append(table(
        ["Model (4 classes)", "Parameters", "Trainable", "MACs / image", "Inference, MPS (ms)", "Inference, CPU (ms)"],
        [
            ["Custom CNN (baseline)", "0.39 M", "0.39 M", "0.74 G", "1.4 – 1.6", "4.6"],
            ["Frozen ResNet18", "11.18 M", "2,052", "1.81 G", "3.0 – 3.2", "11.7"],
            ["Fine-tuned ResNet18", "11.18 M", "11.18 M", "1.81 G", "3.0 – 3.2", "11.4"],
        ],
        [4.0 * cm, 2.3 * cm, 2.3 * cm, 2.6 * cm, 3.1 * cm, 3.1 * cm],
        "Table 1. Model size and cost for one 3 × 224 × 224 image. MPS: Apple Silicon GPU, mean over the test runs; CPU: batch of one, mean of 20 passes.",
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
    story.append(P(
        "All code, the saved results of the 48 runs, the unit tests and the demonstration are "
        "reproduced in the experiment notebook, which runs from start to finish with Restart &amp; Run All "
        "and does not retrain unless asked to:"
    ))
    story.append(Paragraph(f'<link href="{NB_COLAB}" color="blue">{NB_COLAB}</link>', S["BodyLink"]))
    story.append(Paragraph("3.1 Datasets and splits", S["H2"]))
    story.append(P(
        "Table 2 lists the collections. Membership is written once to results/splits and reloaded "
        "afterwards, so a new seed changes initialisation and shuffle order, not which image is "
        "in the test set. A checker refuses to train if the same path, or the same BreakHis "
        "patient id, appears in two splits."
    ))
    story.append(table(
        ["Dataset", "Task", "Train / val / test", "Grouping"],
        [
            ["Brain MRI [public]", "4 tumour categories", "4855 / 857 / 1311", "Image. No patient id."],
            ["BreakHis [4]", "8 subtypes", "4973 / 1399 / 1537", "Patient. 54 / 14 / 14."],
            ["DermaMNIST [8], [6]", "7 lesion types", "7007 / 1003 / 2005", "Official split."],
            ["IQ-OTH/NCCD [7]", "Normal, benign, malignant", "767 / 165 / 165", "Image. No patient id."],
        ],
        [3.6 * cm, 3.8 * cm, 4.2 * cm, 5.8 * cm],
        "Table 2. Collections, counts, and whether a patient-level split could be verified.",
    ))
    story.append(P(
        "BreakHis is the only collection in which patient independence was verified. Every "
        "magnification of one patient stays in one split [4]. DermaMNIST is not reshuffled, but "
        "the arrays do not contain the HAM10000 lesion id, so two images of one lesion may still "
        "cross the cut [8], [5]. Brain filenames are sequential slice indexes such as Tr-gl_0505. "
        "The official Testing folder is held out and 15 percent of the official Training folder, "
        "stratified, is validation. That does not stop two slices of one scan from landing in "
        "both sets [3]. On IQ-OTH/NCCD the number in a filename such as \"Bengin case (85)\" is "
        "unique inside its class and runs from 1 to the class count. It is an image index. The "
        "public release has no subject id, and slice-level scores on this collection are known "
        "to be optimistic relative to a patient-level protocol [9]."
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
        "4 configurations x 3 seeds x 4 datasets = 48 runs. Table 3 records the settings that "
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
        "Table 3. Settings held fixed inside each configuration. The augmentation switch is the extra factor for the fine-tuned model.",
    ))
    story.append(Paragraph("3.3 The demonstration page", S["H2"]))
    story.append(P(
        "The Gradio page loads one checkpoint per dataset: the fine-tuned, augmented run whose "
        "validation macro-F1 was best among the three seeds. It does not retrain, and it does "
        "not load a second network for the coarser label. After the category softmax, the page "
        "adds the probabilities of the categories that the dataset maps to one group. Table 4 "
        "is that map. A brain tumour is reported as a tumour, not as cancer, because the MRI "
        "folders do not carry a benign or malignant label. Actinic keratosis is precancerous; "
        "it is placed in the cancer-related group only because that is the convention of the "
        "HAM10000 release, and the page says so [8]."
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
        "Table 4. The coarser label is a sum of category probabilities, not a second trained model.",
    ))
    story.append(P(
        "The same page draws Grad-CAM from the last convolutional layer [6]. The map is the "
        "gradient of the winning class with respect to that layer, pooled and drawn over the "
        "input. It shows which features moved the winning logit. It is not a segmentation of "
        "the lesion, and the caption on the page says that a match to a training folder is not "
        "a diagnosis. Figures 2 and 3 are four held-out test images run through that page. "
        "The left half of each panel is the uploaded image. The right half is the Grad-CAM "
        "the page draws for the winning category."
    ))
    story.append(figure_pair(
        DEMO / "demo_brain.png",
        DEMO / "demo_breast.png",
        "Figure 2. Demonstration page. Brain MRI: pituitary tumour, group Tumour, 100%. Breast histopathology: adenosis, group Benign, 65.7% (the benign group sums to 67.7%).",
    ))
    story.append(figure_pair(
        DEMO / "demo_skin.png",
        DEMO / "demo_lung.png",
        "Figure 3. Demonstration page. Skin: the true label is melanoma, and the page returns benign keratosis-like lesions at 82.1%, group Not cancer-related. Lung CT: malignant, group Malignant, 99.5%. One image is not the test average.",
    ))

    story.append(Paragraph("4. Experimental results", S["H1"]))
    story.append(P(
        "Table 5 is the primary result: test macro-F1, mean ± sample standard deviation over the "
        "three seeds, with fine-tuned accuracy and single-image inference time beside it. The "
        "custom CNN is the baseline. Fine-tuning wins on every modality, which supports H1, and a "
        "Welch t-test across seeds gives p &lt; 0.003 for fine-tuning against both the baseline "
        "and the frozen backbone on all four datasets. Figure 4 shows the same comparison. The "
        "margin is not uniform, which supports H3: +0.27 over the baseline on brain MRI but +0.58 "
        "on lung CT. On skin, the frozen ResNet18 (0.344) does not even beat the custom CNN "
        "(0.371). ImageNet features held completely fixed are a weak description of a dermoscopic "
        "lesion; adapting the backbone is what moves the score to 0.719."
    ))
    story.append(table(
        ["Dataset", "Custom CNN (baseline)", "Frozen ResNet18", "Fine-tuned ResNet18 (proposed)", "Accuracy, fine-tuned", "Inference (ms)"],
        [
            ["Brain MRI", "0.724 ± 0.011", "0.837 ± 0.002", "<b>0.989 ± 0.004</b>", "0.990 ± 0.004", "3.2"],
            ["Breast", "0.272 ± 0.016", "0.349 ± 0.024", "<b>0.506 ± 0.031</b>", "0.581 ± 0.020", "3.0"],
            ["Skin", "0.371 ± 0.009", "0.344 ± 0.008", "<b>0.719 ± 0.014</b>", "0.787 ± 0.010", "3.0"],
            ["Lung CT", "0.366 ± 0.044", "0.617 ± 0.034", "<b>0.946 ± 0.021</b>", "0.968 ± 0.013", "3.1"],
        ],
        [2.4 * cm, 3.1 * cm, 2.8 * cm, 3.6 * cm, 3.0 * cm, 2.5 * cm],
        "Table 5. Test macro-F1 (↑), mean ± sample standard deviation over seeds 42, 123 and 2026. Accuracy and MPS inference time are for the fine-tuned model; the custom CNN runs in about 1.5 ms.",
    ))
    story.append(figure(
        PLOTS / "macro_f1_comparison.png",
        "Figure 4. Test macro-F1 by modality and training strategy (seed means). Table 5 gives the standard deviations.",
        height=7.0 * cm,
    ))
    story.append(P(
        "Accuracy, the secondary metric, tells a softer story and supports H4. Skin accuracy "
        "for the fine-tuned model is 0.787 ± 0.010, while macro-F1 is 0.719. Nevi are 1,341 "
        "of 2,005 test images, so a model can be right often and still weak on melanoma "
        "(F1 0.568). Breast accuracy is 0.581 ± 0.020 against macro-F1 0.506, because ductal "
        "carcinoma is common and phyllodes tumour is effectively missed. One-versus-rest macro "
        "AUC for the fine-tuned model is about 1.000 on brain MRI, 0.852 on breast, 0.965 on "
        "skin, and 0.999 on lung CT. AUC stays high when the ranking of a rare class is decent "
        "even if the decision threshold, pushed by class weights, is not."
    ))
    story.append(Paragraph("4.1 Ablation study: training augmentation", S["H2"]))
    story.append(P(
        "Table 6 isolates augmentation. Both columns fine-tune ResNet18 at the same learning "
        "rate, on the same split, with the same seeds and the same early stopping; only the "
        "training transform changes. H2 is supported on breast, where augmentation raises "
        "macro-F1 from 0.462 to 0.506 (+0.045), and it is neutral on brain MRI (+0.004). It is "
        "not supported on skin or lung CT, where the unaugmented fine-tune is higher (0.762 and "
        "0.992, both about −0.045). With only three seeds per arm these differences are "
        "suggestive rather than conclusive: the Welch p-values are 0.12 for breast and about "
        "0.05 for skin and lung CT. The direction, however, is consistent across seeds. Colour "
        "and geometry changes that are harmless on natural photographs can move a stain or a "
        "lesion away from the test distribution, and a tiny, homogeneous CT set gains little "
        "from rotated copies. H3 follows: the useful recipe is not the same recipe on every "
        "modality. The frozen-versus-fine-tuned comparison of Table 5 is a second ablation: "
        "removing backbone adaptation alone costs between 0.15 and 0.38 macro-F1."
    ))
    story.append(table(
        ["Dataset", "With augmentation (full model)", "Without augmentation", "Δ", "Welch p"],
        [
            ["Brain MRI", "0.989 ± 0.004", "0.985 ± 0.006", "+0.004", "0.38"],
            ["Breast", "0.506 ± 0.031", "0.462 ± 0.024", "+0.045", "0.12"],
            ["Skin", "0.719 ± 0.014", "0.762 ± 0.022", "−0.044", "0.053"],
            ["Lung CT", "0.946 ± 0.021", "0.992 ± 0.007", "−0.047", "0.051"],
        ],
        [3.0 * cm, 4.6 * cm, 4.0 * cm, 2.6 * cm, 3.2 * cm],
        "Table 6. Ablation of training augmentation for fine-tuned ResNet18. Test macro-F1, mean ± std over three seeds; Δ = with − without.",
    ))
    story.append(figure(
        DEMO / "learning_curves.png",
        "Figure 5. Learning curves of the fine-tuned ResNet18 with augmentation, seed 42. Top: training and validation loss; bottom: training accuracy and validation macro-F1. The dashed line is the epoch restored for the test score.",
        height=6.4 * cm,
    ))
    story.append(P(
        "Figure 5 shows the learning curves for all four tasks. On brain MRI, skin and lung CT "
        "the validation loss falls with the training loss and validation macro-F1 keeps rising, "
        "so the restored epoch is late (6 to 8). Breast is different: the validation loss rises "
        "from the first epoch while the training loss falls, and the restored epoch is 2. That "
        "is the signature of a patient-level split, where the validation patients look different "
        "from the training patients, and it is discussed in Section 5. Mean training time for a "
        "brain run is 322 s for the custom CNN, 209 s for the frozen head, and 273 s for "
        "fine-tuning; lung runs finish in under a minute because the training set has 767 images. "
        "Figure 6 is the brain confusion matrix for the same run: "
        "almost every test slice sits on the diagonal, and the visible exchanges are glioma with meningioma."
    ))
    story.append(figure(
        PLOTS / "brain__finetune_aug__seed42_confusion.png",
        "Figure 6. Brain MRI confusion matrix, fine-tuned ResNet18 with augmentation, seed 42.",
    ))
    story.append(Paragraph("4.2 Where the errors sit", S["H2"]))
    story.append(P(
        "Tables 7 and 8 break the fine-tuned, augmented model into classes. Support is the "
        "test count, which does not change with the seed. F1 is the mean across the three seeds. "
        "On BreakHis the headline 0.506 is an average of a strong adenosis class and a phyllodes "
        "class that the model does not detect. On DermaMNIST the headline 0.719 is pulled up by "
        "1,341 nevi and pulled down by melanoma, whose precision is 0.484."
    ))
    story.append(table(
        ["BreakHis class", "n", "Precision", "Recall", "F1"],
        [
            ["Adenosis", "132", "0.810", "0.831", "0.820 ± 0.068"],
            ["Fibroadenoma", "247", "0.492", "0.706", "0.579 ± 0.040"],
            ["Phyllodes tumour", "235", "0.021", "0.004", "0.007 ± 0.012"],
            ["Tubular adenoma", "65", "0.750", "0.692", "0.710 ± 0.103"],
            ["Ductal carcinoma", "583", "0.817", "0.718", "0.764 ± 0.008"],
            ["Lobular carcinoma", "123", "0.395", "0.515", "0.445 ± 0.066"],
            ["Mucinous carcinoma", "62", "0.270", "0.527", "0.357 ± 0.030"],
            ["Papillary carcinoma", "90", "0.284", "0.530", "0.369 ± 0.032"],
        ],
        [4.6 * cm, 2.0 * cm, 3.2 * cm, 2.8 * cm, 4.8 * cm],
        "Table 7. BreakHis per-class scores for fine-tuned ResNet18 with augmentation.",
    ))
    story.append(table(
        ["DermaMNIST class", "n", "Precision", "Recall", "F1"],
        [
            ["Actinic keratosis / IEC", "66", "0.775", "0.576", "0.658 ± 0.026"],
            ["Basal cell carcinoma", "103", "0.658", "0.867", "0.747 ± 0.031"],
            ["Benign keratosis", "220", "0.553", "0.833", "0.664 ± 0.009"],
            ["Dermatofibroma", "23", "0.527", "0.855", "0.652 ± 0.033"],
            ["Melanoma", "223", "0.484", "0.691", "0.568 ± 0.002"],
            ["Melanocytic nevi", "1341", "0.973", "0.796", "0.875 ± 0.014"],
            ["Vascular lesions", "29", "0.828", "0.908", "0.865 ± 0.058"],
        ],
        [4.6 * cm, 2.0 * cm, 3.2 * cm, 2.8 * cm, 4.8 * cm],
        "Table 8. DermaMNIST per-class scores for fine-tuned ResNet18 with augmentation.",
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
        "Table 9 is the practical companion to the macro-F1 table. Times are means over the "
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
        "Table 9. Mean training time and test macro one-versus-rest AUC. AUC is omitted from the primary claim because a missing class would leave it undefined; every class was present in these runs.",
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
        "Figure 7. BreakHis confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. Phyllodes tumour is almost absent from the diagonal.",
    ))
    story.append(P(
        "Breast is the honest stress test, because the split is patient-level [4]; Figure 7 is its confusion matrix. Fine-tuned "
        "macro-F1 is only 0.506 ± 0.031. Adenosis F1 is 0.820 and ductal carcinoma F1 is 0.764. "
        "Phyllodes tumour F1 is 0.007 ± 0.012. On average about 143 of 235 phyllodes test "
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
        "Figure 8. DermaMNIST confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. The nevus column and row dominate the counts.",
    ))
    story.append(P(
        "On skin (Figure 8), the largest off-diagonal mass is melanocytic nevi predicted as melanoma, about "
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
        "can sit in training and test [9]. The lung number is therefore an upper bound on what "
        "the same network would score on a new person, not a measurement of that score. "
        "Figure 9 shows how small that off-diagonal is on one seed: the mistakes are a few slices, not a class."
    ))
    story.append(figure(
        PLOTS / "lung__finetune_aug__seed42_confusion.png",
        "Figure 9. Lung CT confusion matrix, fine-tuned ResNet18 with augmentation, seed 42. Benign has 18 test slices.",
    ))
    story.append(figure(
        GRADCAM / "breast__finetune_aug__seed42.png",
        "Figure 10. Grad-CAM on high-confidence BreakHis mistakes for the fine-tuned model, seed 42. The heat map marks features that moved the winning logit. It is not a tumour outline [6].",
    ))
    story.append(P(
        "Figure 10 is the failure view required by the assignment, not a gallery of easy successes. "
        "The saved grids in results/gradcam do the same for the other datasets. Where the heat "
        "sits on the tissue rather than on the slide border, the mistake is a genuine look-alike "
        "class, as with phyllodes and fibroadenoma. Where it sits on background, the prediction "
        "is using a cue that will not survive a new scanner or a new stain. Figures 11 and 12 "
        "are the same view for skin and lung CT."
    ))
    story.append(figure(
        GRADCAM / "skin__finetune_aug__seed42.png",
        "Figure 11. Grad-CAM on high-confidence DermaMNIST mistakes, fine-tuned ResNet18 with augmentation, seed 42.",
        height=7.4 * cm,
    ))
    story.append(figure(
        GRADCAM / "lung__finetune_aug__seed42.png",
        "Figure 12. Grad-CAM on high-confidence lung CT mistakes, fine-tuned ResNet18 with augmentation, seed 42.",
        height=7.4 * cm,
    ))

    story.append(Paragraph("5.1 Expected difference with alternative methods", S["H2"]))
    story.append(P(
        "Several alternatives would be expected to change specific numbers rather than the overall "
        "ranking. Focal loss [10] down-weights easy examples instead of whole classes; it would be "
        "expected to raise melanoma precision and the rare breast carcinomas, but it cannot create "
        "the phyllodes features that 60 training slides do not contain. Stain normalisation of "
        "histopathology [11] removes colour differences between patients and scanners; since the "
        "breast validation curve diverges from the first epoch (Figure 5), it is the change most "
        "likely to help the patient-level task. A self-supervised foundation model such as DINOv2 "
        "[12] used as a frozen backbone with a linear probe would be expected to close much of the "
        "gap between the frozen and the fine-tuned ResNet18, because its features are less tied to "
        "ImageNet object classes; on skin, where frozen ImageNet features were weaker than the "
        "baseline, this is the most informative next comparison. Larger inputs or multi-"
        "magnification fusion on BreakHis and a vision transformer would cost more compute (Table 1) "
        "and are not expected to remove the leakage limitation of the brain and lung results, which "
        "is a property of the data, not of the model."
    ))
    story.append(P(
        "<b>Generalisability.</b> The breast score is the only estimate of performance on new "
        "patients, and it rests on 14 test patients. The brain and lung scores are upper bounds, "
        "and the skin score assumes that two photographs of one lesion did not cross the split. "
        "All four collections come from a small number of sites, so a different scanner, stain "
        "protocol or skin type is untested."
    ))

    story.append(Paragraph("6. Test Procedures and Ethics", S["H1"]))
    story.append(P(
        "The automated checks do not need the image files. They confirm that the custom CNN "
        "maps a 2 x 3 x 224 x 224 batch to 2 x 4 logits, that a frozen ResNet18 trains only the "
        "2,052 head weights of a four-class problem, and that the weighted loss equals the "
        "hand-computed formula. A synthetic nine-patient split is rejected if any patient id "
        "appears twice. MRI and CT training transforms are checked for the absence of a "
        "horizontal flip, and the evaluation transform is checked to be resize, tensor conversion, "
        "and normalisation only. A toy prediction vector checks that macro-F1 does not collapse "
        "to accuracy when one class is easier than the other. The notebook adds three checks of "
        "the formulas: a perfect prediction gives a loss below 10<super>-6</super> "
        "(assert weighted_cross_entropy(z, y, w) &lt; 1e-6), the model output has shape (B, C), "
        "and a perfect prediction gives macro-F1 = 1. All ten checks pass and run from "
        "tests/test_core.py and the notebook without the image files."
    ))
    story.append(P(
        "<b>Preventing data leakage.</b> The split is computed once, written to results/splits, "
        "and reloaded by every run, so a new seed never moves an image between sets. Before "
        "training, a checker raises an error if any image path, or any BreakHis patient id, "
        "appears in two of the three sets; the notebook re-runs that check on all four saved "
        "split files. Augmentation exists only inside the training loader. Class weights and "
        "early stopping use only training and validation data, and the test set is scored once, "
        "after the best validation epoch has been restored. Where the data do not allow a "
        "patient-level split (brain MRI, lung CT), the report says so instead of claiming it."
    ))
    story.append(P(
        "<b>Data licence and privacy.</b> The images are not redistributed. Brain MRI is used under the CC BY 4.0 licence. HAM10000, and "
        "therefore DermaMNIST, is CC BY-NC 4.0 [8]. BreakHis is the UFPR research release [4]. "
        "IQ-OTH/NCCD is a de-identified teaching collection; the public folders still do not "
        "support a patient-level audit [9]. No new patient data were collected. The Gradio page "
        "states that a score is a match to a training folder, not a diagnosis, not a risk, and "
        "not an input to a health decision. All four collections are public and de-identified; no names, dates of birth or other personal data were present or used, images are processed locally, and the demonstration runs on the local machine and its code does not save uploaded images. Actinic keratoses are precancerous; they are grouped "
        "as cancer-related only because that is the dataset convention, and the page says so."
    ))
    story.append(P(
        "<b>Bias.</b> Class weights reduce the chance that the loss is satisfied by the majority class, and "
        "they create the opposite bias: melanoma and the rare breast carcinomas are over-called. "
        "That trade is visible in precision and is preferable to a silent miss, but it must be "
        "described as a threshold choice, not as a calibrated probability. The study also cannot "
        "speak to scanner shift, skin tone, or age, because those attributes are not in the "
        "released labels."
    ))

    story.append(Paragraph("7. Conclusion and Recommendations", S["H1"]))
    story.append(P(
        "Fine-tuning ResNet18 is the best of the three training strategies on all four modalities. "
        "The test macro-F1 values are 0.989 ± 0.004 (brain MRI), 0.506 ± 0.031 (breast), "
        "0.719 ± 0.014 (skin), and 0.946 ± 0.021 (lung CT). A frozen backbone is a useful "
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
    story.append(Paragraph("<b>Future work:</b>", S["Body"]))
    story.append(bullets([
        "Replace brain MRI and lung CT with releases that carry a scan or patient id, and recover "
        "HAM10000 lesion ids for DermaMNIST, so that every score is a patient-level estimate.",
        "Add stain normalisation [11] and focal loss [10] for the rare BreakHis classes, and report "
        "phyllodes recall separately.",
        "Compare against a frozen foundation model (DINOv2 linear probe) [12] and run five or more "
        "seeds so that the augmentation effects can be tested with adequate power.",
        "Make augmentation modality-specific by ablation (no colour jitter on skin, no rotation on CT).",
    ]))

    story.append(Paragraph("References", S["H1"]))
    refs = [
        "[1] H. E. Kim, A. Cosa-Linan, N. Santhanam, M. Jannesari, M. E. Maros, and T. Ganslandt, \"Transfer learning for medical image classification: A literature review,\" BMC Med. Imaging, vol. 22, no. 1, Art. no. 69, Apr. 2022, doi: 10.1186/s12880-022-00793-7.",
        "[2] K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 770-778.",
        "[3] E. Yagis et al., \"Effect of data leakage in brain MRI classification using 2D convolutional neural networks,\" Sci. Rep., vol. 11, Art. no. 22544, Nov. 2021, doi: 10.1038/s41598-021-01681-w.",
        "[4] F. A. Spanhol, L. S. Oliveira, C. Petitjean, and L. Heutte, \"A dataset for breast cancer histopathological image classification,\" IEEE Trans. Biomed. Eng., vol. 63, no. 7, pp. 1455-1462, Jul. 2016.",
        "[5] J. Yang et al., \"MedMNIST v2 - A large-scale lightweight benchmark for 2D and 3D biomedical image classification,\" Sci. Data, vol. 10, Art. no. 41, 2023.",
        "[6] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618-626.",
        "[7] I. Loshchilov and F. Hutter, \"Decoupled weight decay regularization,\" in Proc. Int. Conf. Learn. Represent. (ICLR), 2019.",
        "[8] P. Tschandl, C. Rosendahl, and H. Kittler, \"The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions,\" Sci. Data, vol. 5, Art. no. 180161, 2018.",
        "[9] A. Ahmad et al., \"A leakage-free, patient-level evaluation protocol for multi-class lung CT diagnosis,\" Eng. Rep., 2026, doi: 10.1002/eng2.71054.",
        "[10] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollár, \"Focal loss for dense object detection,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 2980-2988.",
        "[11] M. Macenko et al., \"A method for normalizing histology slides for quantitative analysis,\" in Proc. IEEE Int. Symp. Biomed. Imaging (ISBI), 2009, pp. 1107-1110.",
        "[12] M. Oquab et al., \"DINOv2: Learning robust visual features without supervision,\" Trans. Mach. Learn. Res., 2024.",
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

    doc.build(story, canvasmaker=NumberedCanvas)
    print(OUT)


if __name__ == "__main__":
    build()
