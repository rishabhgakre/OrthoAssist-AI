# OrthoAssist AI

**An AI-Powered Clinical Decision Support System for Orthopedic Recovery Assessment**

---

## The Problem

When a patient suffers a bone fracture — say, from a road accident — their treatment and recovery is tracked in two separate ways:

1. **Structural Recovery** — assessed by a doctor reviewing X-rays: Has the bone healed? Is the alignment correct? Has the fracture gap closed?
2. **Functional Recovery** — assessed by a physiotherapist observing the patient: Can they walk normally? Is their gait symmetric? Have they regained balance and mobility?

**These two assessments happen independently, by different people, using different methods, at different times.** A doctor reads an X-ray. A physiotherapist watches the patient walk. Nobody combines the two into a single, quantitative, evidence-backed picture of "how recovered is this patient, really?"

There is no widely available, standardized AI framework that fuses structural (imaging-based) and functional (movement-based) recovery data into one unified, explainable score.

**This is the gap OrthoAssist AI addresses.**

---

## The Solution

OrthoAssist AI is a clinical decision support system that:

1. Analyzes **pre-operative and post-operative X-rays** to measure structural healing (fracture gap closure, bone alignment, bone continuity)
2. Analyzes a **walking video** to measure functional recovery (gait speed, symmetry, balance, joint movement)
3. Combines both into a single **Composite Orthopedic Recovery Index (CORI)** — a 0-100% score
4. Generates a **plain-language, explainable report** so a doctor understands *why* the score is what it is, not just the number itself
5. Produces a **downloadable PDF report** the doctor can add to the patient's file

**The core innovation is not the individual AI models — it's the fusion.** YOLO-based fracture detection and MediaPipe-based pose estimation both exist elsewhere. What doesn't commonly exist is a system that combines them into one coherent, quantitative, explainable recovery assessment.

---

## How It's Implemented

### System Architecture

```
Doctor
  │
  ▼
Frontend (React + Tailwind)
  │
  ▼
Backend (FastAPI + PostgreSQL)
  │
  ├──► Structural AI Pipeline (X-ray)
  │       Pre-op X-ray ──┐
  │                      ├─► YOLOv8 Detection ─► OpenCV Segmentation ─► Measurements ─► SRS
  │       Post-op X-ray ─┘
  │
  ├──► Functional AI Pipeline (Gait)
  │       Walking Video ─► MediaPipe Pose ─► Feature Extraction ─► FRS
  │
  ├──► CORI Engine
  │       SRS + FRS ─► Weighted Fusion ─► CORI Score + Explainability
  │
  └──► Explainable AI Report (PDF)
          Full findings, scores, images, recommendation
```

### 1. Structural Recovery Pipeline (X-ray Analysis)

Since public fracture datasets don't provide matched pre/post pairs of the same patient, this pipeline is designed in two phases:

- **Training phase**: A YOLOv8 model is fine-tuned on [FracAtlas](https://www.nature.com/articles/s41597-023-02432-4) (Abedeen et al., 2023) — 4,083 X-rays, 717 with fracture annotations — to detect bone/fracture regions.
- **Assessment phase**: For an individual patient, both their pre-op and post-op X-rays are passed through the same pipeline:
  1. **Detection** (YOLOv8) — locates the bone/fracture region
  2. **Segmentation** (classical OpenCV — Otsu thresholding + contour detection within the detected region, since no clean public segmentation-mask dataset exists for this task)
  3. **Measurement** (OpenCV) — extracts fracture gap (mm), alignment (%), and continuity (%) from the segmented bone shape
  4. **Structural Recovery Score (SRS)** — a weighted comparison of pre-op vs post-op measurements:
     ```
     SRS = 0.3 × gap_improvement + 0.3 × alignment_improvement + 0.4 × continuity_improvement
     ```

Image preprocessing (brightness/contrast normalization) runs automatically before detection, so real-world uploads — including dim or unevenly-lit phone photos of X-rays — are handled more reliably than raw images would allow.

### 2. Functional Recovery Pipeline (Gait Analysis)

- **MediaPipe Pose** (pretrained, no training required) extracts 33 body landmarks per frame from a walking video
- Landmark positions across frames are used to compute: walking speed, cadence, stride length, step symmetry, knee flexion, and balance
- These are combined into a **Functional Recovery Score (FRS)**, weighted against normative healthy-gait reference values

### 3. CORI Engine

```
CORI = weight_structural × SRS + weight_functional × FRS
```

Default weighting is 50/50, but is configurable per assessment (e.g., a doctor may weight structural higher immediately post-surgery, and functional higher during later physiotherapy stages).

Beyond the raw score, the CORI engine also:
- Classifies recovery into a stage (Excellent / Good / Moderate / Early)
- **Detects and explains gaps** between structural and functional recovery (e.g., "bone healed well, but walking hasn't caught up — physiotherapy needs more focus")
- Identifies the **specific sub-metric** driving a low score (e.g., "step symmetry is the weakest contributor, not walking speed")
- Generates a plain-language recommendation for the doctor to consider

### 4. Explainable AI Report

A professionally formatted PDF report is generated per assessment, containing:
- Patient details
- Pre/post X-ray images with the full measurement comparison table
- Gait metrics table
- The CORI score, recovery stage, and full explanation
- A clinical recommendation
- A disclaimer clarifying this is decision *support*, not a replacement for clinical judgment

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js + Tailwind CSS | Doctor-facing dashboard *(planned)* |
| Backend | FastAPI | REST API, business logic |
| Database | PostgreSQL + SQLAlchemy | Patient records, assessment history |
| Authentication | JWT (python-jose + bcrypt) | Secure doctor login |
| Bone Detection | YOLOv8 (Ultralytics), fine-tuned | Locates bone/fracture regions in X-rays |
| Bone Segmentation | OpenCV (classical CV) | Isolates bone shape within detected region |
| Pose Estimation | MediaPipe Pose (pretrained) | Extracts body landmarks from gait video |
| Report Generation | ReportLab | Produces the PDF Explainable AI Report |
| Model Training | Google Colab (free tier, T4 GPU) | YOLOv8 fine-tuning on FracAtlas |

---

## Project Structure

```
OrthoAssistAI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── core/
│   │   │   ├── config.py           # Settings (reads from .env)
│   │   │   ├── database.py         # SQLAlchemy engine/session
│   │   │   ├── security.py         # Password hashing, JWT
│   │   │   ├── deps.py             # Auth dependency
│   │   │   ├── cori_engine.py      # CORI scoring + explainability logic
│   │   │   └── report_generator.py # PDF report builder
│   │   ├── models/models.py        # Database tables
│   │   ├── schemas/schemas.py      # Request/response validation
│   │   ├── routers/                # API endpoints (auth, patients, xray, gait, cori, reports)
│   │   ├── ai_structural/          # YOLO detection, segmentation, measurements, SRS scoring
│   │   └── ai_functional/          # MediaPipe gait pipeline, FRS scoring
│   ├── requirements.txt
│   └── .env.example
├── ai_training/
│   └── train_fracture_yolo.ipynb   # Colab notebook: trains YOLOv8 on FracAtlas
├── frontend/                        # React dashboard (planned)
└── docs/
    ├── ROADMAP.md                  # Phase-by-phase project status
    └── training_guide.md           # Step-by-step model training instructions
```

---

## Getting Started

### Prerequisites
- Python 3.11 or 3.12 (not 3.13 — some ML dependencies lack prebuilt packages for it)
- PostgreSQL
- A trained YOLOv8 model (`best.pt`) — see `ai_training/train_fracture_yolo.ipynb`

### Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Create `backend/.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/orthoassist
SECRET_KEY=your-own-long-random-string
```

Create the database, then run:
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

---

## API Overview

| Endpoint | Purpose |
|---|---|
| `POST /auth/signup`, `POST /auth/login` | Doctor authentication |
| `POST /patients/` | Register a new patient |
| `POST /xray/analyze` | Upload pre/post X-rays → Structural Recovery Score |
| `POST /gait/analyze` | Upload walking video → Functional Recovery Score |
| `POST /cori/compute` | Combine SRS + FRS → CORI score with explanation |
| `GET /cori/{id}/explain` | Full explainable breakdown for a past assessment |
| `POST /reports/{cori_id}/generate` | Generate the PDF report |
| `GET /reports/{cori_id}/download` | Download the generated PDF |

---

## Datasets

| Purpose | Dataset | License |
|---|---|---|
| Fracture detection training | [FracAtlas](https://www.nature.com/articles/s41597-023-02432-4) (Abedeen et al., 2023) | CC-BY 4.0 |

Structural recovery *comparison* logic (pre vs post) is demonstrated on individual patient case pairs, since public datasets do not provide matched longitudinal (same-patient, before/after) X-ray pairs.

---

## Current Status

| Component | Status |
|---|---|
| Backend (auth, patients, database) | ✅ Complete |
| Functional AI (gait analysis) | ✅ Complete |
| Structural AI (X-ray analysis) | ✅ Complete |
| YOLOv8 model training | ✅ Complete |
| CORI Engine | ✅ Complete |
| Explainable AI Report (PDF) | ✅ Complete |
| Frontend (React dashboard) | ⬜ In progress |
| Docker / deployment | ⬜ Planned |

See `docs/ROADMAP.md` for the full phase-by-phase breakdown.

---

## Known Limitations

- **Alignment scoring** is most reliable for elongated long-bone shafts (tibia, femur, humerus); complex joint regions (wrist, hand) are automatically less reliable for this specific metric due to their irregular shape, though other metrics remain valid.
- **Detection confidence decreases** on post-operative images containing surgical hardware (plates, screws), since the training dataset (FracAtlas) contains only pre-treatment radiographs.
- **Pixel-to-millimeter conversion** for gap measurement uses a configurable estimate rather than a calibrated reference marker in the image, since X-rays don't inherently encode real-world scale.
- Structural comparison (pre vs post) is demonstrated per-patient rather than validated across a large matched longitudinal dataset, due to the absence of such public datasets.

These are documented transparently rather than hidden, consistent with how published fracture-detection research reports its own limitations.

---

## Disclaimer

This system is a decision **support** tool intended to assist, not replace, clinical judgment. All AI-generated findings should be reviewed and confirmed by a qualified medical professional before informing treatment decisions.
