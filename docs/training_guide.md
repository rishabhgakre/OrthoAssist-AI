# Training the Structural AI Model (YOLOv8 Fracture Detection)

This trains YOLO to detect fractures in X-rays using the FracAtlas dataset.
Do this once — the output (`best.pt`) is reused by your backend afterward.

**Time needed:** ~30-40 minutes, mostly hands-off once training starts.
**Cost:** Free (Google Colab free tier + free Kaggle dataset).

---

## Before you start

- [ ] A Google account (for Colab)
- [ ] A Kaggle account — free, sign up at kaggle.com if you don't have one
- [ ] The file `ai_training/train_fracture_yolo.ipynb` from your project

---

## Step-by-step

### 1. Open Colab
Go to **colab.research.google.com**

### 2. Upload the notebook
`File → Upload notebook` → browse to your project folder → select
`ai_training/train_fracture_yolo.ipynb`

### 3. Turn on the free GPU
`Runtime → Change runtime type → Hardware accelerator → T4 GPU → Save`
(Skipping this makes training take hours instead of minutes — don't skip it.)

### 4. Get your Kaggle API key
- Go to **kaggle.com/settings**
- Scroll to the "API" section → click **"Create New Token"**
- This downloads a file called `kaggle.json` to your computer — remember where.

### 5. Run the notebook, cell by cell
Click each code cell, then press **Shift + Enter** (or the ▶ play button) to run it,
and wait for it to finish before moving to the next one.

| Cell | What it does | What to expect |
|---|---|---|
| Step 1 | Installs packages | Quick, no output needed |
| Step 2 | Asks you to upload `kaggle.json` | An upload button appears — click it, select the file from Step 4 |
| (dataset download) | Downloads FracAtlas | Progress bar, ~1-2 min |
| Step 3 | Shows folder structure | Just for you to sanity-check — no action needed |
| Step 4 | Creates config file | Instant |
| **Step 5** | **Actual training** | **This is the long one — ~20-30 min.** You'll see epoch numbers counting up and loss values going down. Let it run, don't close the tab. |
| Step 6 | Evaluation | Prints precision, recall, mAP50, mAP50-95 — **write these numbers down**, you'll need them for your report |
| Step 7 | Visual check | Shows a sample X-ray with the detected fracture box drawn on it |
| **Step 8** | **Downloads `best.pt`** | Triggers a browser download — save it somewhere you'll find again |

### 6. Move the trained model into your project
Copy the downloaded `best.pt` file into:
```
OrthoAssistAI/backend/app/ai_structural/weights/best.pt
```

### 7. Test it
Restart your backend server:
```bash
cd backend
uvicorn app.main:app --reload
```
Then try the `/xray/analyze` endpoint at `http://localhost:8000/docs` with two real
X-ray images — it should now return real detection + measurement results instead
of the "weights not found" error.

---

## If something goes wrong

| Problem | Likely cause | Fix |
|---|---|---|
| Kaggle download fails / "403 Forbidden" | Kaggle account needs to accept dataset rules once | Visit the FracAtlas dataset page on kaggle.com while logged in, click "Download" once manually (accepts terms), then retry the notebook cell |
| Training cell errors with "CUDA out of memory" | Free GPU has limited memory | Lower `batch=16` to `batch=8` in the training cell and re-run |
| Colab disconnects mid-training | Free tier has usage limits | Just re-run from Step 5 — Colab sessions can idle-timeout, but Ultralytics saves checkpoints, so you don't fully lose progress if it's mid-epoch-save |
| mAP scores look "low" (e.g. 0.5-0.7) | This is normal for FracAtlas — it's a genuinely hard dataset, published research reports similar numbers | Not a bug — report it honestly with context in your write-up, this is expected |

---

## For your report

Cite the dataset as:
> Abedeen, I. et al. (2023). *FracAtlas: A Dataset for Fracture Classification,
> Localization and Segmentation of Musculoskeletal Radiographs.*

Report the precision/recall/mAP50/mAP50-95 numbers from Step 6 as your model's
quantitative evaluation — this is the standard way object detection results are
reported in real papers, and it's what makes your project look methodologically
sound rather than just "it worked" hand-waving.
