# OrthoAssist AI — Project Roadmap

Track progress here. Update the checkboxes as phases complete.

---

- [x] **Phase 1 — Backend Core**
  Auth (signup/login/JWT), patient records, PostgreSQL database models.
  *Status: Built & tested (verified via live API tests).*

- [x] **Phase 2 — Functional AI (Gait)**
  MediaPipe pose estimation, gait feature extraction, Functional Recovery Score.
  *Status: Code complete, logic tested with math verification. Not yet run on a real video.*

- [x] **Phase 3 — Structural AI (pipeline code)**
  YOLO detection wrapper, OpenCV segmentation, pre/post measurement comparison,
  Structural Recovery Score, `/xray/analyze` API endpoint.
  *Status: Fully built & tested with synthetic images.*

- [ ] **Phase 3b — Train the YOLO model** ⬅ *(You are here — training tomorrow)*
  Run `ai_training/train_fracture_yolo.ipynb` in Colab on the FracAtlas dataset,
  produce `best.pt`, place it in `backend/app/ai_structural/weights/`.
  *See `docs/training_guide.md` for full steps.*

- [ ] **Phase 4 — CORI Engine**
  Combine Structural Recovery Score + Functional Recovery Score into the final
  Composite Orthopedic Recovery Index. Simple weighted formula — quick once
  Phase 3b is done and both scores exist.

- [ ] **Phase 5 — Explainable AI Report (PDF)**
  ReportLab-generated doctor report: X-ray images with detected regions,
  gait skeleton overlay, all scores, plain-language explanation, recommendation.

- [ ] **Phase 6 — Frontend (React Dashboard)**
  Doctor login, patient management, upload forms (X-rays + walking video),
  results dashboard, PDF download. The largest remaining chunk of work.

- [ ] **Phase 7 — Docker + Deployment**
  Dockerize backend (and frontend) with `docker-compose.yml` so the whole app
  runs with one command on any machine — this alone is a strong thing to show
  in your submission even without public hosting.
  Optional stretch goal: deploy publicly via Hugging Face Spaces (best fit for
  ML workloads on a free tier) if time permits after everything else works.

- [ ] **Phase 8 — Documentation / Report**
  Project report, methodology write-up, screenshots, accuracy metrics from
  training (Phase 3b), final README.

---

## Notes
- Docker (Phase 7) is intentionally placed *after* the app fully works —
  no point containerizing something still under active development.
- Public deployment is optional and lower priority than a working local
  Docker setup + demo video, given free-tier memory limits with
  PyTorch/YOLO/MediaPipe.
