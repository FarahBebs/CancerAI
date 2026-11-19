const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/Users/farahalhasan/.claude/skills/synced/06e5d6b2-a6b6-41a6-9d0b-bb623ceddeaf_fa08ef33-107c-43a0-8b59-9a33c35c5105/pptx/scripts/apply_theme.js");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "deliverables", "BIL458_CancerAI_Slides.pptx");
const GRADCAM = path.join(ROOT, "results", "gradcam", "breast__finetune_aug__seed42.png");

const THEME = {
  name: "CancerAI",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "12312A",
    lt1: "FFFFFF",
    dk2: "1F6F6A",
    lt2: "F3F6F5",
    accent1: "1F6F6A",
    accent2: "B85042",
    accent3: "3E6B58",
    accent4: "C4A484",
    accent5: "6E2E2A",
    accent6: "2A4038",
    hlink: "1F6F6A",
    folHlink: "B85042",
  },
};

function card(slide, x, y, w, h, name) {
  slide.addShape("roundRect", {
    x, y, w, h,
    fill: { color: "F3F6F5" },
    rectRadius: 0.08,
    objectName: name,
  });
}

async function main() {
  const pres = new pptxgen();
  pres.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
  pres.layout = "WIDE";
  pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
  pres.author = "Farah Alhasan";
  pres.title = "CancerAI: A Comparative Study of Deep Learning Strategies for Multi-Modal Medical Image Classification";
  pres.subject = "BIL458 Computer Vision term project";
  pres.company = "BIL458 Computer Vision";
  const C = pres.SchemeColor;

  const titlePh = {
    placeholder: {
      text: "",
      options: {
        name: "title",
        type: "title",
        x: 0.55, y: 0.28, w: 12.2, h: 0.72,
        fontFace: "Cambria",
        fontSize: 32,
        bold: true,
        color: C.text1,
        margin: 0,
      },
    },
  };

  pres.defineSlideMaster({
    title: "Dark",
    background: { color: C.text1 },
    slideNumber: { x: 12.35, y: 7.05, w: 0.5, h: 0.28, color: "D5E3DF", fontFace: "Calibri", fontSize: 12, margin: 0 },
    objects: [],
  });

  pres.defineSlideMaster({
    title: "Light",
    background: { color: C.background1 },
    margin: [0.4, 0.5, 0.45, 0.5],
    slideNumber: { x: 12.35, y: 7.05, w: 0.5, h: 0.28, color: "5E6E69", fontFace: "Calibri", fontSize: 12, margin: 0 },
    objects: [titlePh],
  });

  pres.addSection({ title: "Open" });
  pres.addSection({ title: "Study" });
  pres.addSection({ title: "Evidence" });
  pres.addSection({ title: "Close" });

  // 1. Title
  {
    const s = pres.addSlide({ masterName: "Dark", sectionTitle: "Open" });
    s.addText("BIL458  ·  Computer Vision", {
      x: 0.7, y: 1.35, w: 11.5, h: 0.35,
      fontFace: "Calibri", fontSize: 16, color: "C4A484", margin: 0, isTextBox: true,
    });
    s.addText("CancerAI", {
      x: 0.7, y: 1.8, w: 11.5, h: 0.9,
      fontFace: "Cambria", fontSize: 60, bold: true, color: "FFFFFF", margin: 0, isTextBox: true,
    });
    s.addText("How training strategy and augmentation change classification\nacross four medical image types", {
      x: 0.7, y: 2.85, w: 10.5, h: 1.0,
      fontFace: "Calibri", fontSize: 22, color: "D5E3DF", margin: 0, isTextBox: true,
    });
    s.addText("Farah Alhasan   ·   21120205709\nAssoc. Prof. Murat Gezer   ·   Individual project", {
      x: 0.7, y: 5.55, w: 10, h: 0.75,
      fontFace: "Calibri", fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true,
    });
    s.addNotes("Open by naming the course and yourself. One sentence: this is a comparison of training recipes on four separate image tasks, not a cancer detector. Say the talk has three parts: the design, the scores, and the cases the scores hide. You present the whole 15 minutes. Leave the demo for the end.");
  }

  // 2. Question
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Open" });
    s.addText("The question is the training recipe", { placeholder: "title" });
    const items = [
      ["H1", "Fine-tuning wins", "A fine-tuned ResNet18 should beat a network trained from scratch and a frozen ImageNet backbone."],
      ["H2", "Augmentation helps", "Extra training views should help most where a class is small or uneven."],
      ["H3", "The gain depends", "Microscope, dermoscopy, MRI, and CT should not move by the same amount."],
      ["H4", "Accuracy hides it", "Macro-F1 and per-class recall should show the classes accuracy can skip."],
    ];
    items.forEach((item, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.55 + col * 6.26;
      const y = 1.35 + row * 2.7;
      card(s, x, y, 5.98, 2.45, "Hypothesis " + item[0]);
      s.addText(item[0], {
        x: x + 0.28, y: y + 0.22, w: 1.2, h: 0.4,
        fontFace: "Cambria", fontSize: 20, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: x + 1.35, y: y + 0.22, w: 4.35, h: 0.4,
        fontFace: "Cambria", fontSize: 22, bold: true, color: "12312A", margin: 0, isTextBox: true,
      });
      s.addText(item[2], {
        x: x + 0.28, y: y + 0.85, w: 5.45, h: 1.35,
        fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
      });
    });
    s.addNotes("Read the question, then the four hypotheses, without reading every word. Stress that each dataset is its own task. A brain tumour label is not a cancer label. Primary metric is macro-F1, mean and sample standard deviation over seeds 42, 123, and 2026. About 90 seconds.");
  }

  // 3. Datasets
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Study" });
    s.addText("Four collections, kept separate", { placeholder: "title" });
    const sets = [
      ["Brain MRI", "4 categories", "4,855 / 857 / 1,311", "Filenames are slice indexes. Not a patient split."],
      ["BreakHis", "8 subtypes", "54 / 14 / 14 patients", "The only split verified to keep a patient on one side."],
      ["DermaMNIST", "7 lesion types", "7,007 / 1,003 / 2,005", "Official split. Lesion ids are not in the file."],
      ["Lung CT", "3 categories", "767 / 165 / 165", "Case numbers are image indexes, not people."],
    ];
    sets.forEach((item, i) => {
      const y = 1.35 + i * 1.4;
      card(s, 0.55, y, 12.2, 1.25, item[0]);
      s.addText(item[0], {
        x: 0.8, y: y + 0.16, w: 3.3, h: 0.4,
        fontFace: "Cambria", fontSize: 20, bold: true, color: "12312A", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: 4.2, y: y + 0.18, w: 2.6, h: 0.38,
        fontFace: "Calibri", fontSize: 16, color: "1F6F6A", margin: 0, isTextBox: true,
      });
      s.addText(item[2], {
        x: 7.0, y: y + 0.16, w: 5.4, h: 0.38,
        fontFace: "Cambria", fontSize: 18, color: "12312A", margin: 0, isTextBox: true,
      });
      s.addText(item[3], {
        x: 0.8, y: y + 0.66, w: 11.5, h: 0.4,
        fontFace: "Calibri", fontSize: 15, color: "3E534C", margin: 0, isTextBox: true,
      });
    });
    s.addNotes("Spend the time on the last line of each card. Only BreakHis supports a patient-level claim. Brain and lung scores can be inflated by neighbouring slices. DermaMNIST was not reshuffled, but two photos of one lesion can still cross the cut. Do not call any of those three leakage-free. About 90 seconds.");
  }

  // 4. Method
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Study" });
    s.addText("Three ways to train the same task", { placeholder: "title" });
    const models = [
      ["From scratch", "0.39M", "Four convolutions, trained on the medical set only."],
      ["Frozen ResNet18", "2k–4k", "ImageNet backbone held fixed. Only the new head learns."],
      ["Fine-tuned ResNet18", "11.2M", "Every weight moves, at a learning rate of 0.0001."],
    ];
    models.forEach((item, i) => {
      const x = 0.55 + i * 4.15;
      card(s, x, 1.35, 3.95, 2.55, item[0]);
      s.addText(item[0], {
        x: x + 0.22, y: 1.52, w: 3.5, h: 0.7,
        fontFace: "Cambria", fontSize: 20, bold: true, color: "12312A", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: x + 0.22, y: 2.25, w: 3.5, h: 0.55,
        fontFace: "Cambria", fontSize: 28, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[2], {
        x: x + 0.22, y: 2.9, w: 3.5, h: 0.8,
        fontFace: "Calibri", fontSize: 15, color: "12312A", margin: 0, isTextBox: true,
      });
    });
    s.addText("The loss is class-weighted cross-entropy: minus the weight of the true class times the log of its probability, averaged over the batch. The epoch that is kept is the one with the best validation macro-F1. Three epochs without a gain of 0.001 stop the run. Validation and test images are never augmented.", {
      x: 0.55, y: 4.2, w: 12.2, h: 1.15,
      fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
    });
    s.addText("A coarser label, such as benign or malignant, is the sum of category probabilities. It is not a second network.", {
      x: 0.55, y: 5.5, w: 12.2, h: 0.7,
      fontFace: "Calibri", fontSize: 16, color: "1F6F6A", margin: 0, isTextBox: true,
    });
    s.addNotes("Point at the three cards left to right. Mention the learning-rate difference: 0.001 for the small net and the frozen head, 0.0001 when every ResNet weight moves. Say the loss matches the written formula, not PyTorch's default weighted mean, and that a unit test checks it. About 90 seconds.");
  }

  // 5. Design
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Study" });
    s.addText("One grid, written down before training", { placeholder: "title" });
    const facts = [
      ["48", "runs", "4 configurations, 3 seeds, 4 datasets."],
      ["1", "split file", "Seeds change initialisation, not who is in the test set."],
      ["0", "test flips", "Augmentation stays inside the training loader."],
    ];
    facts.forEach((item, i) => {
      const x = 0.55 + i * 4.15;
      card(s, x, 1.4, 3.95, 2.7, "Fact " + item[0]);
      s.addText(item[0], {
        x: x + 0.22, y: 1.58, w: 3.5, h: 0.85,
        fontFace: "Cambria", fontSize: 42, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: x + 0.22, y: 2.45, w: 3.5, h: 0.4,
        fontFace: "Cambria", fontSize: 20, bold: true, color: "12312A", margin: 0, isTextBox: true,
      });
      s.addText(item[2], {
        x: x + 0.22, y: 3.0, w: 3.5, h: 0.8,
        fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
      });
    });
    s.addText("Histopathology may flip both ways. Dermoscopy may flip horizontally. MRI and CT are not flipped, because left and right are anatomical. Hue is not jittered. The fourth configuration is the same fine-tune with that augmentation turned off.", {
      x: 0.55, y: 4.4, w: 12.2, h: 1.3,
      fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
    });
    s.addNotes("This is the methods slide for the examiner who asks about leakage and seeds. The split is written once. A checker refuses a repeated BreakHis patient. Say the ablation is one switch: augmentation on or off, everything else fixed. About 75 seconds.");
  }

  // 6. Results
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Evidence" });
    s.addText("Fine-tuning leads on every modality", { placeholder: "title" });
    s.addChart(pres.charts.BAR, [
      { name: "Custom CNN", labels: ["Brain", "Breast", "Skin", "Lung"], values: [0.724, 0.272, 0.371, 0.366] },
      { name: "Frozen ResNet18", labels: ["Brain", "Breast", "Skin", "Lung"], values: [0.837, 0.349, 0.344, 0.617] },
      { name: "Fine-tuned", labels: ["Brain", "Breast", "Skin", "Lung"], values: [0.989, 0.506, 0.719, 0.946] },
    ], {
      x: 0.5, y: 1.2, w: 8.0, h: 5.45,
      barGrouping: "clustered",
      showLegend: true,
      legendPos: "b",
      legendFontSize: 12,
      legendColor: "12312A",
      legendFontFace: "+mn-lt",
      chartColors: ["1F6F6A", "C4A484", "B85042"],
      showValue: false,
      showTitle: false,
      valAxisMinVal: 0,
      valAxisMaxVal: 1,
      valAxisTitle: "Test macro-F1",
      showValAxisTitle: true,
      valAxisTitleFontSize: 12,
      valAxisTitleColor: "12312A",
      valAxisTitleFontFace: "+mn-lt",
      catAxisLabelColor: "12312A",
      valAxisLabelColor: "12312A",
      catAxisLabelFontSize: 12,
      valAxisLabelFontSize: 11,
      catAxisLabelFontFace: "+mn-lt",
      valAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "D5DEDB", size: 0.5 },
      catGridLine: { style: "none" },
      chartArea: { fill: { color: "FFFFFF" } },
    });
    const notes = [
      ["0.989", "Brain MRI"],
      ["0.506", "Breast, patient-level"],
      ["0.719", "Skin lesions"],
      ["0.946", "Lung CT"],
    ];
    notes.forEach((item, i) => {
      const y = 1.25 + i * 1.3;
      s.addText(item[0], {
        x: 8.75, y: y, w: 4.0, h: 0.5,
        fontFace: "Cambria", fontSize: 26, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: 8.75, y: y + 0.48, w: 4.0, h: 0.35,
        fontFace: "Calibri", fontSize: 14, color: "12312A", margin: 0, isTextBox: true,
      });
    });
    s.addNotes("Walk left to right. Fine-tuning is the tall bar everywhere, so H1 holds and the margin is not the same, so H3 holds. On skin the frozen bar is shorter than the custom CNN: ImageNet features held fixed are a weak description of a lesion. The breast 0.51 is the number to trust, because that split is by patient. Brain and lung are high and not patient-level. About two minutes.");
  }

  // 7. Ablation
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Evidence" });
    s.addText("Augmentation did not travel", { placeholder: "title" });
    s.addTable([
      [
        { text: "Dataset", options: { fill: { color: "12312A" }, color: "FFFFFF", bold: true, align: "left" } },
        { text: "With augmentation", options: { fill: { color: "12312A" }, color: "FFFFFF", bold: true, align: "center" } },
        { text: "Without augmentation", options: { fill: { color: "12312A" }, color: "FFFFFF", bold: true, align: "center" } },
        { text: "What changed", options: { fill: { color: "12312A" }, color: "FFFFFF", bold: true, align: "left" } },
      ],
      ["Brain MRI", "0.989", "0.985", "Almost nothing"],
      ["Breast", "0.506", "0.462", "Augmentation helped"],
      ["Skin", "0.719", "0.762", "Augmentation hurt"],
      ["Lung CT", "0.946", "0.992", "Augmentation hurt"],
    ], {
      x: 0.55, y: 1.45, w: 12.2, h: 3.4,
      colW: [2.4, 2.8, 3.2, 3.8],
      border: [
        { pt: 0, color: "FFFFFF" },
        { pt: 0, color: "FFFFFF" },
        { pt: 0, color: "FFFFFF" },
        { pt: 0, color: "FFFFFF" },
      ],
      fontFace: "Calibri",
      fontSize: 16,
      color: "12312A",
      align: "center",
      valign: "middle",
      fill: { color: "F3F6F5" },
    });
    s.addText("Both columns fine-tune ResNet18 on the same split and the same seeds. Only the training transform changes. H2 holds for breast. It does not hold for skin or lung CT, and those gaps are larger than the seed-to-seed variation.", {
      x: 0.55, y: 5.2, w: 12.2, h: 1.2,
      fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
    });
    s.addNotes("Say H2 was the hypothesis you expected to win everywhere, and it did not. Breast, the patient-level set, is the one that improved. Skin and lung scored higher with a plain resize. Colour jitter that is harmless on photographs can move a stain or a lesion away from the test images. About 90 seconds.");
  }

  // 8. Failures
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Evidence" });
    s.addText("The average hides the miss", { placeholder: "title" });
    s.addImage({
      path: GRADCAM,
      x: 6.85, y: 1.85, w: 5.9, h: 4.21,
      objectName: "BreakHis Grad-CAM mistakes",
    });
    const fails = [
      ["0.007", "Phyllodes F1. About 143 of 235 test slides are called fibroadenoma."],
      ["0.484", "Melanoma precision. The model buys recall by over-calling it."],
      ["0.99", "Brain macro-F1. Slice indexes cannot rule leakage out."],
    ];
    fails.forEach((item, i) => {
      const y = 1.35 + i * 1.75;
      s.addText(item[0], {
        x: 0.55, y: y, w: 5.8, h: 0.55,
        fontFace: "Cambria", fontSize: 28, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: 0.55, y: y + 0.6, w: 5.8, h: 0.85,
        fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, isTextBox: true,
      });
    });
    s.addNotes("This is the slide to slow down on. The picture is Grad-CAM on high-confidence BreakHis mistakes: phyllodes tumour called fibroadenoma. The heat map is not a tumour outline. Breast accuracy is 0.58 and would have hidden a class the model does not detect. On skin, nevi are 1,341 of 2,005 test images, so accuracy looks kinder than macro-F1. Lung benign rests on 18 slices. About two minutes.");
  }

  // 9. Demo
  {
    const s = pres.addSlide({ masterName: "Light", sectionTitle: "Close" });
    s.addText("What the page is allowed to say", { placeholder: "title" });
    const bits = [
      ["1", "Category", "The class folder the image is closest to, from the fine-tuned model."],
      ["2", "Group", "A sum of those probabilities. Tumour is not reported as cancer."],
      ["3", "Grad-CAM", "Which features moved the winning logit. Not a lesion outline."],
      ["4", "Disclaimer", "A match to a training folder is not a diagnosis and not a risk."],
    ];
    bits.forEach((item, i) => {
      const y = 1.35 + i * 1.35;
      card(s, 0.55, y, 12.2, 1.2, "Demo " + item[0]);
      s.addText(item[0], {
        x: 0.8, y: y + 0.32, w: 0.7, h: 0.5,
        fontFace: "Cambria", fontSize: 26, bold: true, color: "B85042", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x: 1.7, y: y + 0.18, w: 3.2, h: 0.85,
        fontFace: "Cambria", fontSize: 22, bold: true, color: "12312A", margin: 0, valign: "middle", isTextBox: true,
      });
      s.addText(item[2], {
        x: 5.1, y: y + 0.22, w: 7.3, h: 0.75,
        fontFace: "Calibri", fontSize: 16, color: "12312A", margin: 0, valign: "middle", isTextBox: true,
      });
    });
    s.addNotes("Tell the room you will open the Gradio page after this slide, on one image from each modality if time allows. Point at the disclaimer before you point at a high score. Actinic keratosis is grouped as cancer-related only because that is the dataset convention, and the page says it is precancerous. About one minute, then switch to the demo.");
  }

  // 10. Close
  {
    const s = pres.addSlide({ masterName: "Dark", sectionTitle: "Close" });
    s.addText("Fine-tuning won. The split still decides what that means.", {
      x: 0.7, y: 0.55, w: 12, h: 1.3,
      fontFace: "Cambria", fontSize: 32, bold: true, color: "FFFFFF", margin: 0, isTextBox: true,
    });
    const closes = [
      ["0.989", "Brain"],
      ["0.506", "Breast"],
      ["0.719", "Skin"],
      ["0.946", "Lung"],
    ];
    closes.forEach((item, i) => {
      const x = 0.7 + i * 3.1;
      s.addText(item[0], {
        x, y: 2.3, w: 2.8, h: 0.7,
        fontFace: "Cambria", fontSize: 32, bold: true, color: "C4A484", margin: 0, isTextBox: true,
      });
      s.addText(item[1], {
        x, y: 3.0, w: 2.8, h: 0.4,
        fontFace: "Calibri", fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true,
      });
    });
    s.addText("A frozen backbone helps on MRI and CT and does not help on skin. Augmentation helps the patient-level breast task and lowers skin and lung. The next experiment needs a scan id. Until then this is a teaching demo, not a device.", {
      x: 0.7, y: 3.8, w: 11.8, h: 1.4,
      fontFace: "Calibri", fontSize: 18, color: "D5E3DF", margin: 0, isTextBox: true,
    });
    s.addText("Farah Alhasan   ·   questions", {
      x: 0.7, y: 5.7, w: 8, h: 0.4,
      fontFace: "Calibri", fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true,
    });
    s.addNotes("Restate the four numbers and the two limits: only breast is patient-level, and phyllodes is effectively missed there. Invite questions. If asked whether you would deploy it, the answer is no. If asked what you would change first, say a dataset with scan identifiers, not a larger network. Stop around 15 minutes so the five-minute questions have room.");
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log(OUT);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
