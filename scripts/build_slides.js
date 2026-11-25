// Build the ten-slide BIL458 talk from the saved study results.
// Run: node scripts/build_slides.js   ->  deliverables/BIL458_CancerAI_Slides.pptx

const path = require("path");
let pptxgen;
try {
  pptxgen = require("/private/tmp/claude-501/-Users-farahalhasan-Desktop-Projects/23fe7d3d-661f-4b5a-b8fb-a40f0f056694/scratchpad/js/node_modules/pptxgenjs");
} catch (e) {
  pptxgen = require("pptxgenjs");
}
let applyTheme = null;
try {
  const scratchModules = "/private/tmp/claude-501/-Users-farahalhasan-Desktop-Projects/23fe7d3d-661f-4b5a-b8fb-a40f0f056694/scratchpad/js/node_modules";
  process.env.NODE_PATH = [scratchModules, process.env.NODE_PATH || ""].filter(Boolean).join(path.delimiter);
  require("module").Module._initPaths();
  ({ applyTheme } = require("/Users/farahalhasan/.claude/skills/synced/06e5d6b2-a6b6-41a6-9d0b-bb623ceddeaf_fa08ef33-107c-43a0-8b59-9a33c35c5105/pptx/scripts/apply_theme.js"));
} catch (e) {
  console.warn("apply_theme.js not found; scheme colours will use the Office default palette.");
}
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "deliverables", "BIL458_CancerAI_Slides.pptx");
const P = (...p) => path.join(ROOT, ...p);

// Palette: navy echoes the university template, teal is the accent, coral marks warnings.
const NAVY = "1F2A5C";
const TEAL = "0F8B8D";
const CORAL = "D1495B";
const SOFT = "EEF2F8";
const GREY = "9AA3B5";

const THEME = {
  name: "CancerAI BIL458",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F2A", lt1: "FFFFFF", dk2: NAVY, lt2: SOFT,
    accent1: NAVY, accent2: TEAL, accent3: CORAL, accent4: GREY,
    accent5: "5B6B8C", accent6: "C9D3E6", hlink: TEAL, folHlink: "5B6B8C",
  },
};

// ---------------------------------------------------------------- notes
const NOTES = {
  1: `(~45 s) Hello, I'm Farah Alhasan. My project is CancerAI. It is an individual project, so I did every part: preparing the data and the splits, training the models, the evaluation and the ablation, the demo app, and the report.
The question is simple: if we train a CNN in different ways, how much does that change the result on medical images? I test this on four different kinds of medical images.
I will go through: the problem, the data, the method and the maths, the results, where the model fails, and then a short live demo.`,
  2: `(~1.5 min) Here are the four kinds of images. Brain MRI, breast tissue under a microscope, skin lesion photos, and lung CT.
Each one is its own separate task with its own classes. This is not one "cancer detector".
My research question: does the training strategy, and data augmentation, change the score, and is the change the same for every image type?
I wrote four hypotheses before training.
H1: fine-tuning a pretrained network will win.
H2: augmentation will help, especially for rare classes.
H3: how much it helps depends on the image type.
H4: accuracy can hide classes that the model gets wrong, so I need macro-F1.`,
  3: `(~1.5 min) These are the four datasets. You can see the number of classes and how many images went to training, validation and test.
The most important column is the last one: how the split was made.
Data leakage means: if the same patient is in training and in test, the model can memorise that patient instead of learning the disease. Then the test score looks better than it really is.
Only BreakHis has patient IDs, so only there I could keep every patient on one side. That makes breast the most honest result.
For skin I used the official split. For brain and lung the files have no patient ID, so I say clearly that those scores might be too optimistic.
The split is saved to a file once, and every run reuses the same file.`,
  4: `(~1.5 min) This is the pipeline, left to right.
An image comes in. It is resized to 224 by 224 and normalised. During training only, I add augmentation: small flips, rotations, brightness changes. Validation and test images are never changed.
Then one of three models. One: a small CNN trained from scratch, about 0.39 million weights, it only sees medical images. Two: a frozen ResNet18 — I reuse features learned on ImageNet and only train the last layer, a few thousand weights. Three: a fine-tuned ResNet18 — I reuse those features and adjust every layer, 11.2 million weights, with a small learning rate.
At the end, softmax gives a probability for each class, and Grad-CAM shows which part of the image influenced the decision.`,
  5: `(~1.5 min) Three formulas carry the method.
First, the loss. It is cross-entropy, but each class has a weight. The weight is bigger when a class has fewer images. So a mistake on a rare class costs more, and the model cannot just ignore it.
Second, the metric. Macro-F1 computes F1 for each class and then takes the plain average. Every class counts the same, so a big class cannot hide a weak one. This is the metric I use to pick the best epoch and to report results.
Third, the cost. A convolution layer costs height times width times kernel size squared times input channels times output channels. My small CNN needs about 0.74 billion multiply-adds per image, ResNet18 about 1.8 billion. In practice that is about 1.5 ms versus about 3 ms per image, so the bigger model is still fast.`,
  6: `(~1 min) This is the experiment plan. Four datasets, four training setups, three random seeds: 48 runs. Each dot is one run.
The baseline is the small CNN from scratch. The ablation is the last column: the same fine-tuning, but with augmentation switched off. Only that one thing changes.
Every run uses AdamW and a cosine learning-rate schedule. After each epoch I check validation macro-F1, keep the best epoch, and stop after three epochs with no improvement.
The test set is used once, at the end. Results are the mean plus or minus the standard deviation over the three seeds 42, 123 and 2026.`,
  7: `(~1.5 min) Here are the main results: test macro-F1, averaged over three seeds.
The dark bar, fine-tuning, is the highest on all four datasets. So H1 is supported.
The gap is very different per dataset, so H3 is supported too.
One surprise: on skin, the frozen network is a bit worse than the small CNN from scratch. ImageNet features that are not adjusted don't describe skin lesions well. Once we adjust every layer, skin goes up to 0.72.
Breast is the lowest at about 0.51 — but remember, it is the only patient-level split, so it is the most honest number.`,
  8: `(~1.5 min) This is the ablation: the same fine-tuned model, with and without augmentation.
On breast, augmentation helped by about 4 points. On brain it made almost no difference.
But on skin and lung it hurt, by about 4 to 5 points. All three seeds point the same way, but with only three seeds the t-test gives p of about 0.05, so I call it a clear trend, not a proven effect.
Why? For skin, colour is a key clue, and changing brightness and saturation can blur the colour difference between a mole and a melanoma. For lung, the dataset is small and clean, and extra rotation moves training images away from what the test images look like.
So H2 is only partly true, and the lesson is: choose augmentation per image type.`,
  9: `(~1.5 min) Now where the model fails — the average hides some of this.
On breast, the phyllodes tumour class has F1 of almost zero. About 143 of 235 test images of it are called fibroadenoma. These two benign tissue types look very similar under the microscope. The pictures show Grad-CAM on those mistakes: the model looks at the tissue, so it is a real look-alike problem, not a background trick.
On skin, accuracy is 0.79 but macro-F1 is 0.72. Most test images are normal moles, so accuracy looks good, while melanoma precision is only 0.48 — the model over-calls melanoma. That supports H4.
On brain, 0.99 looks great, but without patient IDs, slices from the same scan can be in train and test, so it might be inflated.`,
  10: `(~2.5 min incl. ~1 min demo) Let me show the demo. I run python app.py, open the page, choose the image type and upload an image. The page shows the predicted category, the broader group like benign or malignant — that is just the category probabilities added up, not a second model — and the Grad-CAM map. The page also says clearly that this is not a diagnosis.
To conclude: one, fine-tuning a pretrained ResNet18 was the best strategy on all four image types. Two, augmentation is not automatically good; it helped breast and hurt skin and lung. Three, macro-F1 showed weak classes that accuracy hid.
The main limitation is the split: only breast is patient-level. Next, I would use datasets with patient IDs, and try stain normalisation or focal loss for the rare breast classes.
Thank you. I'm happy to take questions.`,
};

function addFooter(slide, n, dark = false) {
  // Footer text and number are added per slide so the number is always the real page.
  slide.addText("CancerAI  ·  BIL458 Computer Vision", {
    x: 0.6, y: 7.02, w: 6, h: 0.3, fontSize: 10, color: dark ? "C9D3E6" : "6B7489", margin: 0, isTextBox: true,
  });
  slide.addText(`${n} / 10`, {
    x: 11.73, y: 7.02, w: 1.0, h: 0.3, fontSize: 10, color: dark ? "C9D3E6" : "6B7489", align: "right", margin: 0, isTextBox: true,
  });
}

async function main() {
  const pres = new pptxgen();
  pres.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
  pres.layout = "WIDE";
  pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
  pres.author = "Farah Alhasan";
  pres.title = "CancerAI: Training strategies for multi-modal medical image classification";
  pres.subject = "BIL458 Computer Vision term project";
  pres.company = "BIL458 Computer Vision";
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "Title dark",
    background: { color: C.text2 },
    objects: [],
  });
  pres.defineSlideMaster({
    title: "Content",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.13, h: 0.85, fontFace: "Cambria", fontSize: 34, bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
    ],
  });

  const T = (s, txt, n) => { s.addText(txt, { placeholder: "title" }); s.addNotes(NOTES[n]); addFooter(s, n); };
  const card = (s, x, y, w, h, name, fill = C.background2) =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12, objectName: name });
  const txt = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top", ...o });

  // ============================================================ 1 Title
  pres.addSection({ title: "Introduction" });
  {
    const s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Introduction" });
    txt(s, "BIL458  ·  COMPUTER VISION  ·  TERM PROJECT", { x: 0.8, y: 0.9, w: 11, h: 0.4, fontSize: 14, bold: true, color: "7FD1D2", charSpacing: 2 });
    s.addText("CancerAI", { x: 0.8, y: 1.45, w: 11, h: 1.2, fontFace: "Cambria", fontSize: 60, bold: true, color: C.background1, margin: 0, isTextBox: true });
    txt(s, "Does the way we train a CNN change how well it classifies medical images?\nA comparison on brain MRI, breast tissue, skin lesions and lung CT", {
      x: 0.8, y: 2.75, w: 11.2, h: 1.0, fontSize: 20, color: "DDE4F2",
    });
    txt(s, [
      { text: "Farah Alhasan", options: { bold: true, color: "FFFFFF" } },
      { text: "   ·   21120205709   ·   Instructor: Assoc. Prof. Murat Gezer", options: { color: "DDE4F2" } },
    ], { x: 0.8, y: 4.15, w: 11.5, h: 0.4, fontSize: 18 });

    txt(s, "Task distribution — individual project, all parts done by Farah Alhasan", { x: 0.8, y: 5.05, w: 11.5, h: 0.35, fontSize: 14, bold: true, color: "7FD1D2" });
    const tasks = ["Data & splits", "Models & training", "Evaluation & ablation", "Demo app", "Report & slides"];
    tasks.forEach((t, i) => {
      const x = 0.8 + i * 2.38;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.5, w: 2.2, h: 0.62, fill: { color: "2E3B78" }, line: { color: "2E3B78" }, rectRadius: 0.1, objectName: `task ${i + 1}` });
      txt(s, t, { x, y: 5.5, w: 2.2, h: 0.62, fontSize: 14, color: "FFFFFF", align: "center", valign: "middle" });
    });
    txt(s, "Today:  problem  →  data  →  method & maths  →  results  →  where it fails  →  live demo", { x: 0.8, y: 6.4, w: 11.5, h: 0.4, fontSize: 15, color: "DDE4F2" });
    s.addNotes(NOTES[1]);
    addFooter(s, 1, true);
  }

  // ============================================================ 2 Problem & aim
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Introduction" });
    T(s, "Problem and aim", 2);
    const imgs = [["brain.jpg", "Brain MRI"], ["breast.jpg", "Breast tissue"], ["skin.jpg", "Skin lesion"], ["lung.jpg", "Lung CT"]];
    imgs.forEach(([f, label], i) => {
      const x = 0.6 + (i % 2) * 2.75, y = 1.45 + Math.floor(i / 2) * 2.5;
      s.addImage({ path: P("examples", f), x, y, w: 2.5, h: 1.95, sizing: { type: "cover", w: 2.5, h: 1.95 }, altText: `${label} example image`, rounding: false });
      txt(s, label, { x, y: y + 1.98, w: 2.5, h: 0.32, fontSize: 14, bold: true, color: C.text2, align: "center" });
    });
    card(s, 6.35, 1.45, 6.38, 1.55, "question card", C.text2);
    txt(s, "RESEARCH QUESTION", { x: 6.65, y: 1.6, w: 5.8, h: 0.3, fontSize: 12, bold: true, color: "7FD1D2", charSpacing: 1 });
    txt(s, "How do the CNN training strategy and data augmentation change the score — and is the change the same for every image type?", {
      x: 6.65, y: 1.95, w: 5.85, h: 0.95, fontSize: 17, color: "FFFFFF",
    });
    const H = [
      ["H1", "Fine-tuning a pretrained network wins"],
      ["H2", "Augmentation helps, most for rare classes"],
      ["H3", "The gain depends on the image type"],
      ["H4", "Accuracy hides weak classes; macro-F1 shows them"],
    ];
    H.forEach(([h, t], i) => {
      const y = 3.25 + i * 0.85;
      s.addShape(pres.shapes.OVAL, { x: 6.35, y, w: 0.62, h: 0.62, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `${h} badge` });
      txt(s, h, { x: 6.35, y, w: 0.62, h: 0.62, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
      txt(s, t, { x: 7.15, y, w: 5.6, h: 0.62, fontSize: 17, valign: "middle" });
    });
    txt(s, [
      { text: "Each image type is its own task with its own classes — not one “cancer detector”. ", options: { bold: true, color: C.text2 } },
      { text: "The 4 hypotheses were written before training.", options: { color: "4A5266" } },
    ], { x: 0.6, y: 6.45, w: 12.13, h: 0.4, fontSize: 14 });
  }

  // ============================================================ 3 Data
  pres.addSection({ title: "Method" });
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
    T(s, "Data: four datasets, four separate tasks", 3);
    const head = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: C.text2 }, fontSize: 15 } });
    const rows = [
      [head("Dataset"), head("Classes"), head("Train / Val / Test"), head("Split by")],
      ["Brain MRI", "4 tumour types", "4,855 / 857 / 1,311", "Image only"],
      ["BreakHis (breast)", "8 subtypes", "4,973 / 1,399 / 1,537", "Patient ✓"],
      ["DermaMNIST (skin)", "7 lesion types", "7,007 / 1,003 / 2,005", "Official split"],
      ["IQ-OTH/NCCD (lung)", "Normal / benign / malignant", "767 / 165 / 165", "Image only"],
    ].map((r, i) => i === 0 ? r : r.map((c, j) => ({
      text: c,
      options: { fontSize: 15, fill: { color: i % 2 ? C.background1 : C.background2 }, bold: j === 0 || (i === 2 && j === 3), color: i === 2 && j === 3 ? C.accent2 : C.text1 },
    })));
    s.addTable(rows, { x: 0.6, y: 1.5, w: 7.9, colW: [2.25, 2.05, 2.1, 1.5], rowH: 0.72, border: { type: "solid", pt: 0.75, color: "D5DCEA" }, valign: "middle", margin: 0.08, fontFace: "Calibri" });
    const facts = [
      ["Key column", "“Split by” — how the split was made matters most."],
      ["Breast", "54 / 14 / 14 patients — no patient in two splits (checked in code)."],
      ["Skin", "Official MedMNIST split. Brain, lung: no patient ID → scores may be optimistic."],
      ["All runs", "Split saved to a file once and reused by all 48 runs."],
    ];
    facts.forEach(([h, d], i) => {
      txt(s, [{ text: h + ":  ", options: { bold: true, color: C.text2 } }, { text: d, options: {} }], { x: 0.6, y: 5.2 + i * 0.42, w: 7.9, h: 0.4, fontSize: 14, valign: "middle" });
    });

    card(s, 8.9, 1.5, 3.83, 5.25, "leakage card");
    txt(s, "What is data leakage?", { x: 9.15, y: 1.68, w: 3.4, h: 0.45, fontSize: 19, bold: true, color: C.text2, fontFace: "Cambria" });
    txt(s, "Same patient in training and test → the model can memorise the person, not learn the disease.", { x: 9.15, y: 2.18, w: 3.4, h: 1.0, fontSize: 15 });
    const chip = (x, y, letter, col) => {
      s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: col }, line: { color: col }, objectName: `patient ${letter}` });
      txt(s, letter, { x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    };
    const mini = (y, ok) => {
      [["Train", 9.15], ["Test", 10.95]].forEach(([lab, x]) => {
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.55, h: 0.95, fill: { color: "FFFFFF" }, line: { color: GREY, width: 1 }, rectRadius: 0.08, objectName: `${lab} box ${ok}` });
        txt(s, lab, { x, y: y + 0.05, w: 1.55, h: 0.3, fontSize: 13, align: "center", bold: true, color: "4A5266" });
      });
      chip(9.71, y + 0.42, "A", ok ? TEAL : CORAL);
      chip(11.51, y + 0.42, ok ? "B" : "A", ok ? TEAL : CORAL);
      txt(s, ok ? "✓ Good: each patient on one side" : "✗ Bad: patient A on both sides", {
        x: 9.15, y: y + 1.02, w: 3.4, h: 0.35, fontSize: 14, bold: true, color: ok ? C.accent2 : C.accent3,
      });
    };
    mini(3.3, false);
    mini(4.85, true);
    txt(s, "Only BreakHis has patient IDs → most honest score.", { x: 9.15, y: 6.28, w: 3.45, h: 0.35, fontSize: 13, italic: true, color: C.text2 });
  }

  // ============================================================ 4 Pipeline
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
    T(s, "Method: from image to prediction", 4);
    const steps = [
      ["1", "Input image", "MRI, tissue, skin or CT"],
      ["2", "Pre-process", "Resize 224×224, normalise"],
      ["3", "Augment", "Flip / rotate / brightness — training only. Val/test never changed"],
      ["4", "CNN model", "One of the 3 options below"],
      ["5", "Output", "Class probabilities + Grad-CAM map"],
    ];
    const bw = 2.15, gap = 0.345;
    steps.forEach(([n, h, d], i) => {
      const x = 0.6 + i * (bw + gap);
      card(s, x, 1.5, bw, 1.5, `step ${n}`, i === 3 ? C.text2 : C.background2);
      const dark = i === 3;
      txt(s, `${n}  ${h}`, { x: x + 0.15, y: 1.62, w: bw - 0.3, h: 0.45, fontSize: 17, bold: true, color: dark ? "FFFFFF" : C.text2 });
      txt(s, d, { x: x + 0.15, y: 2.05, w: bw - 0.3, h: 0.9, fontSize: 13, color: dark ? "DDE4F2" : C.text1 });
      if (i < steps.length - 1) {
        s.addShape(pres.shapes.LINE, { x: x + bw + 0.04, y: 2.25, w: gap - 0.08, h: 0, line: { color: C.accent2, width: 2.5, endArrowType: "triangle" }, objectName: `arrow ${n}` });
      }
    });
    // connector from model box to the options
    const mx = 0.6 + 3 * (bw + gap) + bw / 2;
    s.addShape(pres.shapes.LINE, { x: mx, y: 3.05, w: 0, h: 0.5, line: { color: C.accent2, width: 2, dashType: "dash" }, objectName: "model link" });
    txt(s, "Everything else stays the same — only the model box changes:", { x: 0.6, y: 3.2, w: 8, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
    const models = [
      ["From scratch", "Custom CNN", "0.39 M", "weights trained", "Small CNN. Sees only the medical images. This is my baseline."],
      ["Frozen ResNet18", "Transfer learning", "2k–4k", "weights trained", "Reuse features learned on ImageNet (a big photo dataset). Train only the last layer."],
      ["Fine-tuned ResNet18", "Transfer learning", "11.2 M", "weights trained", "Reuse the ImageNet features and adjust every layer, with a small learning rate (1e-4)."],
    ];
    models.forEach(([h, sub, big, unit, d], i) => {
      const x = 0.6 + i * 4.13, w = 3.87;
      card(s, x, 3.75, w, 2.35, `model ${i + 1}`);
      txt(s, h, { x: x + 0.25, y: 3.88, w: w - 0.5, h: 0.42, fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria" });
      txt(s, [{ text: big, options: { fontSize: 30, bold: true, color: i === 2 ? C.accent2 : C.text2 } }, { text: "  " + unit, options: { fontSize: 14, color: "4A5266" } }], { x: x + 0.25, y: 4.35, w: w - 0.5, h: 0.6 });
      txt(s, d, { x: x + 0.25, y: 5.02, w: w - 0.5, h: 1.0, fontSize: 15 });
    });
    txt(s, "Softmax turns the model's scores into class probabilities. Grad-CAM colours the image regions that pushed the decision.", { x: 0.6, y: 6.3, w: 12.13, h: 0.45, fontSize: 14, italic: true, color: "4A5266" });
  }

  // ============================================================ 5 Maths
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
    T(s, "The maths behind it", 5);
    const rows = [
      ["Loss", "Weighted cross-entropy", [["eq_loss.png", 4.6, 0.75], ["eq_weight.png", 2.59, 0.62]],
        "Fewer images → bigger weight w. Mistakes on a rare class cost more, so it can’t be ignored."],
      ["Metric", "Macro-F1 (main score)", [["eq_f1.png", 3.04, 0.95]],
        "F1 per class, then a plain average: every class counts the same. Used to pick the best epoch and to report."],
      ["Cost", "Big-O of one conv layer", [["eq_cost.png", 11.07, 0.45]],
        "Small CNN ≈ 0.74 G multiply-adds (~1.5 ms/image). ResNet18 ≈ 1.8 G (~3 ms) → still fast."],
    ];
    const RH = 1.7, EQX = 3.75, EQW = 5.35;
    rows.forEach(([tag, name, eqs, plain], i) => {
      const y = 1.45 + i * (RH + 0.15);
      card(s, 0.6, y, 12.13, RH, `math row ${i + 1}`);
      s.addShape(pres.shapes.OVAL, { x: 0.85, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `math badge ${i + 1}` });
      txt(s, String(i + 1), { x: 0.85, y: y + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
      txt(s, tag, { x: 1.5, y: y + 0.2, w: 2.1, h: 0.45, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria" });
      txt(s, name, { x: 1.5, y: y + 0.7, w: 2.1, h: 0.75, fontSize: 14, color: "4A5266" });
      const gapEq = 0.3;
      const total = eqs.reduce((a, [, ar, h]) => a + ar * h, 0) + gapEq * (eqs.length - 1);
      let ex = EQX + (EQW - total) / 2;
      eqs.forEach(([f, ar, h]) => {
        const w = ar * h;
        s.addImage({ path: P("deliverables", "figures", "slides", f), x: ex, y: y + (RH - h) / 2, w, h, altText: `${name} equation` });
        ex += w + gapEq;
      });
      s.addShape(pres.shapes.LINE, { x: 9.2, y: y + 0.25, w: 0, h: RH - 0.5, line: { color: "C9D3E6", width: 1 }, objectName: `math divider ${i + 1}` });
      txt(s, plain, { x: 9.4, y: y + 0.15, w: 3.15, h: RH - 0.3, fontSize: 14, valign: "middle" });
    });
  }

  // ============================================================ 6 Experiment design
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
    T(s, "Experiment design: 48 runs, one change at a time", 6);
    const cols = ["From scratch\n(baseline)", "Frozen\nResNet18", "Fine-tune\n+ augmentation", "Fine-tune\nno augmentation"];
    const rows = ["Brain MRI", "Breast", "Skin", "Lung CT"];
    const gx = 2.35, gy = 2.4, cw = 1.55, rh = 0.85;
    cols.forEach((c, j) => {
      const fill = j === 3 ? C.accent3 : (j === 0 ? GREY : C.text2);
      txt(s, c, { x: gx + j * cw, y: 1.45, w: cw - 0.1, h: 0.85, fontSize: 14, bold: true, align: "center", valign: "bottom", color: j === 3 ? C.accent3 : C.text2 });
    });
    rows.forEach((r, i) => {
      txt(s, r, { x: 0.6, y: gy + i * rh, w: 1.65, h: rh - 0.12, fontSize: 16, bold: true, valign: "middle", color: C.text2 });
      cols.forEach((_, j) => {
        const x = gx + j * cw, y = gy + i * rh;
        card(s, x, y, cw - 0.1, rh - 0.12, `cell ${i}-${j}`, j === 3 ? "FBE9EC" : C.background2);
        [0, 1, 2].forEach((k) => {
          const color = j === 3 ? CORAL : (j === 0 ? GREY : (j === 1 ? "5B6B8C" : NAVY));
          s.addShape(pres.shapes.OVAL, { x: x + 0.25 + k * 0.38, y: y + (rh - 0.12) / 2 - 0.13, w: 0.26, h: 0.26, fill: { color }, line: { color }, objectName: `run ${i}-${j}-${k}` });
        });
      });
    });
    txt(s, "Each dot = one run (seeds 42, 123, 2026).  4 datasets × 4 setups × 3 seeds = 48.", { x: 0.6, y: 5.85, w: 8.1, h: 0.4, fontSize: 14, italic: true, color: "4A5266" });
    txt(s, [
      { text: "Baseline", options: { bold: true, color: C.text2 } }, { text: " = small CNN from scratch.   ", options: {} },
      { text: "Ablation", options: { bold: true, color: C.accent3 } }, { text: " = last column: same fine-tuning, augmentation off.", options: {} },
    ], { x: 0.6, y: 6.3, w: 8.1, h: 0.45, fontSize: 14 });
    // brace labels for baseline / ablation
    card(s, 8.95, 1.45, 3.78, 5.0, "settings card");
    txt(s, "Held the same in every run", { x: 9.2, y: 1.6, w: 3.4, h: 0.45, fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria" });
    txt(s, [
      { text: "Same split file and test set", options: { bullet: { indent: 16 }, breakLine: true } },
      { text: "AdamW optimiser, cosine learning rate", options: { bullet: { indent: 16 }, breakLine: true } },
      { text: "Class-weighted loss", options: { bullet: { indent: 16 }, breakLine: true } },
      { text: "Keep the epoch with best validation macro-F1; stop after 3 epochs without gain", options: { bullet: { indent: 16 }, breakLine: true } },
      { text: "Test set used once, at the end", options: { bullet: { indent: 16 }, breakLine: true } },
      { text: "Report mean ± std over 3 seeds", options: { bullet: { indent: 16 } } },
    ], { x: 9.2, y: 2.2, w: 3.35, h: 4.0, fontSize: 16, paraSpaceAfter: 10 });
  }

  // ============================================================ 7 Results chart
  pres.addSection({ title: "Results" });
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
    T(s, "Results: fine-tuning wins on all four", 7);
    const labels = ["Brain MRI", "Breast", "Skin", "Lung CT"];
    s.addChart(pres.charts.BAR, [
      { name: "From scratch", labels, values: [0.724, 0.272, 0.371, 0.366] },
      { name: "Frozen ResNet18", labels, values: [0.837, 0.349, 0.344, 0.617] },
      { name: "Fine-tuned ResNet18", labels, values: [0.989, 0.506, 0.719, 0.946] },
    ], {
      x: 0.6, y: 1.4, w: 7.9, h: 4.85, barDir: "col", barGapWidthPct: 60,
      chartColors: [GREY, "5B6B8C", NAVY],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 12, dataLabelColor: "1B1F2A", dataLabelFontFace: "+mn-lt",
      valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0",
      valAxisLabelColor: "6B7489", catAxisLabelColor: "1B1F2A", valAxisLabelFontSize: 12, catAxisLabelFontSize: 15,
      valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "E3E8F1", size: 0.75 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "t", legendFontSize: 14, legendFontFace: "+mn-lt", legendColor: "1B1F2A",
      showTitle: true, title: "Test macro-F1 (mean of 3 seeds)", titleFontSize: 15, titleColor: "1F2A5C", titleFontFace: "+mn-lt",
      altText: "Clustered bar chart of test macro-F1 for three training strategies on four datasets",
    });
    txt(s, "Fine-tuned ± std:  brain 0.989 ± 0.004 · breast 0.506 ± 0.031 · skin 0.719 ± 0.014 · lung 0.946 ± 0.021", { x: 0.6, y: 6.32, w: 7.9, h: 0.4, fontSize: 12, color: "6B7489" });

    const pts = [
      ["H1 ✓", "The dark bar (fine-tuning) is the highest on every dataset."],
      ["H3 ✓", "The gap changes a lot between image types."],
      ["Surprise", "Skin: frozen 0.34 < scratch 0.37. Unadjusted ImageNet features fit lesions badly; fine-tuned → 0.72."],
      ["Honest score", "Breast is lowest (0.51), but it is the only patient-level split — the most honest number."],
    ];
    pts.forEach(([h, d], i) => {
      const y = 1.4 + i * 1.34;
      card(s, 8.9, y, 3.83, 1.24, `result point ${i + 1}`);
      txt(s, h, { x: 9.12, y: y + 0.08, w: 3.4, h: 0.32, fontSize: 16, bold: true, color: i < 2 ? C.accent2 : (i === 2 ? C.accent3 : C.text2) });
      txt(s, d, { x: 9.12, y: y + 0.42, w: 3.45, h: 0.78, fontSize: 13 });
    });
  }

  // ============================================================ 8 Ablation
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
    T(s, "Ablation: augmentation is not always good", 8);
    const rows = [
      ["Brain MRI", "0.989", "0.985", "+0.004", "no real change", GREY],
      ["Breast", "0.506", "0.462", "+0.044", "helped", TEAL],
      ["Skin", "0.719", "0.762", "−0.043", "hurt", CORAL],
      ["Lung CT", "0.946", "0.992", "−0.046", "hurt", CORAL],
    ];
    const hx = [0.6, 2.6, 4.35, 6.1];
    ["Fine-tuned ResNet18", "With aug.", "Without aug.", "Effect of augmentation"].forEach((h, j) =>
      txt(s, h, { x: hx[j], y: 1.5, w: j === 3 ? 2.6 : 1.7, h: 0.4, fontSize: 14, bold: true, color: "6B7489", align: j === 0 ? "left" : "center" }));
    rows.forEach(([d, a, b, delta, word, col], i) => {
      const y = 2.0 + i * 1.0;
      card(s, 0.6, y, 8.1, 0.82, `ablation row ${i + 1}`);
      txt(s, d, { x: 0.8, y, w: 1.8, h: 0.82, fontSize: 18, bold: true, color: C.text2, valign: "middle" });
      txt(s, a, { x: 2.6, y, w: 1.7, h: 0.82, fontSize: 20, align: "center", valign: "middle" });
      txt(s, b, { x: 4.35, y, w: 1.7, h: 0.82, fontSize: 20, align: "center", valign: "middle" });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.25, y: y + 0.14, w: 2.3, h: 0.54, fill: { color: col }, line: { color: col }, rectRadius: 0.1, objectName: `delta ${i + 1}` });
      txt(s, `${delta}  ${word}`, { x: 6.25, y: y + 0.14, w: 2.3, h: 0.54, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    });
    txt(s, "Same model, split, seeds and learning rate — only the training augmentation is switched. Skin and lung drop in every seed (Welch p ≈ 0.05 with 3 seeds: a clear trend, not proof).", {
      x: 0.6, y: 6.05, w: 8.1, h: 0.75, fontSize: 13, color: "6B7489",
    });
    card(s, 9.05, 1.5, 3.68, 5.3, "why card", C.text2);
    txt(s, "Why?", { x: 9.3, y: 1.65, w: 3.2, h: 0.45, fontSize: 20, bold: true, color: "FFFFFF", fontFace: "Cambria" });
    txt(s, [
      { text: "Breast: ", options: { bold: true, color: "7FD1D2" } },
      { text: "few patients, so flipped/rotated views are genuinely new examples.", options: { color: "FFFFFF", breakLine: true } },
      { text: "Skin: ", options: { bold: true, color: "F4A3AE" } },
      { text: "colour is a key clue; brightness/saturation changes blur mole vs melanoma.", options: { color: "FFFFFF", breakLine: true } },
      { text: "Lung: ", options: { bold: true, color: "F4A3AE" } },
      { text: "small, clean set; rotated images drift away from the test images.", options: { color: "FFFFFF" } },
    ], { x: 9.3, y: 2.2, w: 3.2, h: 3.3, fontSize: 15, paraSpaceAfter: 12 });
    txt(s, [
      { text: "H2 only partly ✓   ·   H3 ✓", options: { bold: true, color: "7FD1D2", breakLine: true } },
      { text: "→ choose augmentation per image type", options: { color: "FFFFFF" } },
    ], { x: 9.3, y: 5.6, w: 3.2, h: 0.95, fontSize: 15 });
  }

  // ============================================================ 9 Failure analysis
  pres.addSection({ title: "Discussion" });
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Discussion" });
    T(s, "Failure analysis: what the average hides", 9);
    s.addImage({ path: P("results", "gradcam", "breast__finetune_aug__seed42.png"), x: 0.6, y: 1.45, w: 6.6, h: 6.6 * 775 / 1085, altText: "Grad-CAM on high-confidence BreakHis mistakes: phyllodes tumour predicted as fibroadenoma" });
    txt(s, "Grad-CAM on confident breast mistakes (true phyllodes → predicted fibroadenoma). The model looks at the tissue, not the background → a real look-alike problem.", {
      x: 0.6, y: 6.2, w: 6.6, h: 0.65, fontSize: 12, color: "6B7489",
    });
    const st = [
      ["0.007", "Phyllodes F1 (breast)", "Almost zero: 143 of 235 test images called fibroadenoma — two benign tissues that look very similar.", CORAL],
      ["0.79 vs 0.72", "Skin accuracy vs macro-F1", "Most test images are normal moles, so accuracy looks good. Melanoma precision only 0.48 (over-called) → H4 ✓", NAVY],
      ["0.99", "Brain macro-F1", "Looks great, but no patient ID: slices of one scan may be in train and test → maybe inflated.", "5B6B8C"],
    ];
    st.forEach(([big, h, d, col], i) => {
      const y = 1.45 + i * 1.8;
      card(s, 7.6, y, 5.13, 1.62, `failure ${i + 1}`);
      txt(s, big, { x: 7.82, y: y + 0.12, w: 2.3, h: 0.7, fontSize: i === 1 ? 24 : 32, bold: true, color: col, valign: "middle", fontFace: "Cambria" });
      txt(s, h, { x: 10.1, y: y + 0.18, w: 2.5, h: 0.6, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
      txt(s, d, { x: 7.82, y: y + 0.8, w: 4.75, h: 0.78, fontSize: 13 });
    });
  }

  // ============================================================ 10 Demo + conclusion
  {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Discussion" });
    T(s, "Demo and conclusion", 10);
    s.addImage({ path: P("deliverables", "figures", "demo_breast.png"), x: 0.6, y: 1.45, w: 5.9, h: 5.9 * 498 / 864, altText: "Demo page output: breast tissue image and its Grad-CAM" });
    card(s, 0.6, 5.05, 5.9, 1.55, "demo card", C.text2);
    txt(s, "LIVE DEMO", { x: 0.85, y: 5.17, w: 5.4, h: 0.3, fontSize: 12, bold: true, color: "7FD1D2", charSpacing: 1 });
    txt(s, [
      { text: "python app.py  →  http://127.0.0.1:7860", options: { fontFace: "Courier New", bold: true, breakLine: true } },
      { text: "Choose image type → upload → category, group (category probabilities added up, not a 2nd model) and Grad-CAM. Not a diagnosis.", options: {} },
    ], { x: 0.85, y: 5.47, w: 5.45, h: 1.08, fontSize: 13, color: "FFFFFF", paraSpaceAfter: 3 });

    txt(s, "What I learned", { x: 7.0, y: 1.45, w: 5.7, h: 0.45, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria" });
    const L = [
      "Fine-tuning a pretrained ResNet18 is the best strategy on all four image types.",
      "Augmentation is not automatically good: it helped breast, hurt skin and lung.",
      "Macro-F1 showed weak classes that accuracy hid — always look at it.",
    ];
    L.forEach((t, i) => {
      const y = 2.0 + i * 0.88;
      s.addShape(pres.shapes.OVAL, { x: 7.0, y: y + 0.05, w: 0.48, h: 0.48, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `lesson ${i + 1}` });
      txt(s, String(i + 1), { x: 7.0, y: y + 0.05, w: 0.48, h: 0.48, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
      txt(s, t, { x: 7.65, y, w: 5.05, h: 0.8, fontSize: 15, valign: "middle" });
    });
    card(s, 7.0, 4.75, 5.73, 1.25, "limits card");
    txt(s, [
      { text: "Limitation: ", options: { bold: true, color: C.accent3 } },
      { text: "the split — only breast is patient-level.", options: { breakLine: true } },
      { text: "Next: ", options: { bold: true, color: C.accent2 } },
      { text: "datasets with patient IDs; stain normalisation or focal loss for rare breast classes.", options: {} },
    ], { x: 7.2, y: 4.85, w: 5.35, h: 1.05, fontSize: 14, valign: "middle" });
    txt(s, "Thank you — questions?", { x: 7.0, y: 6.2, w: 5.73, h: 0.55, fontSize: 22, bold: true, color: C.text2, fontFace: "Cambria", align: "right" });
  }

  await pres.writeFile({ fileName: OUT });
  if (applyTheme) await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
