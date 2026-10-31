# GeoSafe models

Status of the bundled models, and what the code needs from retrained ones.

**None of these models is ready for real use.** Accuracy on labelled data has not
been measured. The test results below come from local media only.

## How the models fit together

Each video frame is cut into 640×640 tiles, and each tile goes through two stages:

1. The **plant classifier** names the crop. Tiles scoring below 0.7 are marked
   `not detected` and stop here.
2. The **disease classifier** for that crop names the condition. Scores below 0.5
   become `Inconclusive`.

The plant classifier is the gate for everything else. A wrong crop label sends the
tile to the wrong disease model.

## Current status

| Model | Files in `backend/models/new_models/` | Architecture | Input | Recorded accuracy | Status |
|---|---|---|---|---|---|
| Plant classifier | `best.onnx`, `best.pt` | YOLOv8n-cls | 640×640 | None saved | Unreliable, retrain |
| Cassava disease | `cassava_classifier.onnx`, `.pt`, `cassava_meta.json` | EfficientNet-B0 | 380×380 | 0.876 validation, leaf photos | Unproven on drone footage |
| Banana disease | `banana_classifier.onnx`, `.pt`, `banana_meta.json` | EfficientNet-B0 | 380×380 | 1.0 validation, meaningless | Invalid, retrain |

Training notebooks are in `Notebooks/` (currently untracked) and
`backend/Notebooks/`. Their output cells are empty, so training logs and per-class
results were not kept.

## Test results (2026-10-31)

| Test | Result |
|---|---|
| ONNX compared with checkpoints | All three match exactly, 18 of 18 labels |
| Known cassava photo through the pipeline | Reported as plantain, disease Inconclusive |
| Same photo as one whole image | Cassava at 0.88 |
| Tiles from that photo | 5 of 9 labelled plantain |
| Non-crop DJI clip (person, building) | 48 of 48 tiles passed the gate as plantain |
| Corn field clip | 33 of 48 tiles passed the gate |
| 200 synthetic images | 11 passed the gate |
| Flip, ±15% brightness, JPEG, blur, shift | Plant label flips on 12–16% of 25 tiles |
| Cassava disease on the same changes | 0–1 of 25 tiles flip |
| Cassava disease on 100 synthetic images | Healthy all 100 times |

These checks rest on one cassava photo and two short clips. They show behaviour,
not accuracy.

## Problems to fix when retraining

### Plant classifier

- **No negative class.** The notebook planned `cassava`, `plantain` and `other`, but
  the shipped model has only the first two. Everything is forced into one of them,
  so the 0.7 threshold cannot reject non-crop input.
- **Confuses the two crops on tiles.** It got the whole cassava photo right but
  labelled most of its tiles plantain, which suggests a scale mismatch.
- **Fragile.** Small image changes flip labels. Needs stronger augmentation and more
  varied data.

### Cassava disease

- **Trained on a different view.** The notebook uses the Kaggle Cassava Leaf Disease
  dataset, resized from whole images. The pipeline sends it zoomed-in drone tiles.
- **Healthy is the default for unfamiliar input.** A gate-passing tile that the model
  has never seen the like of may be called Healthy.
- **Per-class results are missing.** Overall accuracy can hide weak classes, so save
  a per-class report.

### Banana disease

- **Trained on the wrong labels.** The notebook set `ROOT_DIR` one level too high, so
  `ImageFolder` used `AugmentedSet` and `OriginalSet` as classes. Point it at the
  disease folders so it finds the 4 BananaLSD classes, and train on the original
  images only.
- **Small dataset.** The notebook notes 937 images, so expect it to generalize less
  well than the cassava model.

## What the code expects from retrained models

### File names

Keep the names in `backend/pipeline/config.py`: `best.onnx`,
`<stem>_classifier.onnx` and `<stem>_meta.json`, where plantain uses the stem
`banana`. A missing file now stops the app at startup.

### Plant classifier

- **Update the labels when adding a class.** `class_names` is hardcoded to
  `{0: "cassava", 1: "plantain"}` in `backend/pipeline/onnx_backend.py`. Ultralytics
  sorts classes alphabetically, so with `other` added plantain moves to index 2.
  Leaving the labels unchanged would mislabel tiles.
- **Non-crop labels need no other change.** Any class outside `RECOGNIZED_PLANTS` in
  `backend/pipeline/inference.py` is treated as `not detected`.
- **Input.** The exported model has a fixed batch size of 1 and takes RGB values
  scaled to 0–1.

### Disease classifiers

The metadata file must provide `class_names` and `img_size`:

```json
{
  "model_name": "efficientnet_b0",
  "img_size": 380,
  "num_classes": 5,
  "class_names": { "0": "Cassava Mosaic Disease (CMD)", "1": "Healthy" }
}
```

- **Healthy label.** The healthy class must be named `Healthy`, or the survey counts
  it as a disease.
- **Input.** Preprocessing always converts to RGB and applies ImageNet mean and
  standard deviation, whatever the metadata says. Train with the same values.
- **Output.** The model must return raw logits, because the app applies softmax.

### Removing the banana guard

`_MEANINGLESS_DISEASE_CLASSES` in `backend/pipeline/inference.py` turns `AugmentedSet`
and `OriginalSet` into Inconclusive. Real class names pass through it, so a retrained
model works straight away. Remove the guard and its test once the old model is gone.

### Thresholds

The 0.7 plant and 0.5 disease thresholds were chosen without evaluation data. Tune
them on a validation set after retraining.

## Checking a retrained model

1. Run the backend tests from `backend/`:

   ```bash
   uv run python -m pytest tests -q
   ```

2. Evaluate on a labelled set that was not used for training. The CSV needs `image`
   and `disease` columns, with image paths relative to the CSV:

   ```bash
   uv run python model_evaluation.py path/to/labels.csv --output model-evaluation.json
   ```

3. Check real drone footage. Leaf-photo accuracy says little about aerial tiles.

Before relying on a model, confirm that:

- Each class reports precision and recall on held-out data.
- Non-crop tiles such as soil, sky, buildings and people are rejected.
- Other crops such as corn are rejected.
- Known cassava and plantain footage gets the right crop at tile level.
- Plant labels stay stable under small changes in flip, brightness and compression.
