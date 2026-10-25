# Cronos — PPT Deck Plan (Slide by Slide)

> Purpose: a presentation-ready map of all project work. Each slide lists what to show,
> suggested visuals, and speaker notes. Use this as the source for PowerPoint, Google
> Slides, or Canva.

**Recommended length:** 18–22 minutes + 3–5 minutes Q&A  
**Audience:** soft-computing evaluators, faculty, and project reviewers  
**Live demo:** https://cronos-sc.vercel.app  
**Primary evidence:** `REPORT.md`, `ALGORITHM_DESIGN.md`, `ARCHITECTURE.md`,
`DATA_MODEL_AND_API.md`, `TEST_PLAN.md`, `evaluation-results.json`, and the test suites.

---

## Deck at a glance

| # | Slide | Work covered | Evidence |
|---:|---|---|---|
| 1 | Title | Project identity | `README.md` |
| 2 | The problem | Manual timetable pain | `PRD.md` |
| 3 | Objectives and scope | Goals, MVP boundary | `PRD.md` |
| 4 | Users and workflow | Admin/faculty/student/evaluator flow | `PRD.md` |
| 5 | Solution overview | End-to-end product | `ARCHITECTURE.md` |
| 6 | System architecture | Next.js + FastAPI + storage | `ARCHITECTURE.md` |
| 7 | Data model | Six academic entities + run records | `DATA_MODEL_AND_API.md` |
| 8 | Hard constraints | Feasibility rules | `ALGORITHM_DESIGN.md` |
| 9 | Soft constraints | Schedule quality rules | `ALGORITHM_DESIGN.md` |
| 10 | GA representation | Chromosome, sessions, fitness | `ALGORITHM_DESIGN.md` |
| 11 | GA lifecycle | Selection, crossover, mutation, repair | `apps/api/scheduler.py` |
| 12 | Optimizer improvements | Greedy seed, early stop, bounded repair | `scheduler.py`, evaluation |
| 13 | API surface | Validation, runs, analytics, CSV | `apps/api/routes.py` |
| 14 | Frontend | Overview, setup, timetable, analytics | `apps/web/app/page.tsx` |
| 15 | Persistence | Saved data, run restore, reset/clear | `DATA_PERSISTENCE_FIX.md` |
| 16 | Deployment | Vercel + Neon PostgreSQL | `vercel.json`, `api/index.py` |
| 17 | Testing | 30 backend + 3 frontend + build | `apps/tests`, `apps/web/test` |
| 18 | Evaluation | Five-seed GA vs baseline | `evaluation-results.json` |
| 19 | Project journey | Commit-to-milestone timeline | `git log` |
| 20 | Challenges and fixes | Persistence, JSONB, quality, UI clarity | `DATA_PERSISTENCE_FIX.md` |
| 21 | Limitations | Honest boundaries | `REPORT.md` |
| 22 | Future work and conclusion | Next phase + close | `ROADMAP.md` |
| 23 | Demo and Q&A | Guided live walkthrough | Deployed app |
| A1 | Appendix: API map | Endpoint reference | `DATA_MODEL_AND_API.md` |
| A2 | Appendix: terminology | GA and scheduling terms | `ALGORITHM_DESIGN.md` |

---

## Slide 1 — Title

**Title:** Cronos — College Timetable Optimization Using a Genetic Algorithm  
**Subtitle:** A local-first, constraint-aware academic scheduling system  
**Footer:** Soft Computing Project · [Your name] · [Date]

**Visual:** Dark neutral background, CRONOS wordmark, subtle timetable-grid motif.
Optional QR code linking to the deployed app.

**Speaker notes:** Cronos turns structured academic data into a weekly timetable while
keeping every hard constraint explicit. The optimizer is a custom genetic algorithm, and
the product is fully usable through a web dashboard.

---

## Slide 2 — The problem

**On-slide bullets:**
- Timetables must coordinate faculty, rooms, sections, courses, and time slots.
- Manual scheduling creates clashes, wasted rooms, uneven workload, and long rework cycles.
- A usable solution must distinguish **invalid** schedules from merely **less-preferred** ones.
- Changes are frequent, so saving, reloading, and re-exporting matter as much as generation.

**Visual:** Left: messy spreadsheet/conflict collage. Right: clean weekly grid. Use a
single conflict icon (faculty in two rooms at once) as the focal point.

**Speaker notes:** The core problem is combinatorial: each teaching requirement needs a
slot and a room without breaking institutional rules. The project is not only about
search; it is about trustworthy validation, repeatable runs, and a workflow an
administrator can actually use.

---

## Slide 3 — Objectives and scope

**On-slide bullets:**
- Model academic data with validation and reference checks.
- Define hard constraints and soft preferences separately.
- Implement a reproducible Genetic Algorithm with a documented seed.
- Provide timetable views, run metrics, analytics, and CSV export.
- Persist datasets and run snapshots; deploy the MVP.
- Compare the GA with a baseline and report measured limits honestly.

**Out of scope for the MVP:** authentication, multi-tenancy, background jobs, rate limiting,
institutional integrations, paid APIs, GPU workloads, and guaranteed global optimality.

**Visual:** Two columns: "In scope" and "Later phase".

**Speaker notes:** The project deliberately stays small enough to validate end to end.
Every objective maps to a document and a test or measured result.

---

## Slide 4 — Users and end-to-end workflow

**On-slide bullets:**
1. Administrator loads or enters faculty, rooms, sections, courses, slots, and requirements.
2. API validates IDs, capacities, room types, availability, and slot references.
3. Administrator configures GA parameters and starts a run.
4. GA evolves candidates; an independent checker validates the best schedule.
5. Run snapshot and schedule are saved.
6. Administrator reviews overview, filters the timetable, reads analytics, exports CSV.
7. Any visitor can review the generated schedule through the shared workspace.

**Visual:** Horizontal 6-step swimlane with icons. Highlight the feedback loop for
"validate → fix → run".

**Speaker notes:** The shared-workspace model is intentional for the MVP. Per-user
separation is deferred until authentication exists.

---

## Slide 5 — Solution overview

**On-slide bullets:**
- **Guided data setup** for six entity types plus an advanced JSON editor.
- **Smart Scheduling overview** with dataset counts, validation, and generation controls.
- **Custom timetable grid** filtered by section, faculty, room, day, or text.
- **Run diagnostics:** status, hard violations, soft penalty, runtime, generations.
- **Analytics:** fitness history and session distribution by slot, room, and section.
- **CSV export** that respects the active filters.
- **Durable state:** dataset and latest timetable survive refresh; reset and clear are explicit.

**Visual:** Four annotated product screenshots: Overview, Setup, Timetable, Analytics.
If screenshots are not ready, use browser-framed placeholders with labels.

**Speaker notes:** This slide is the product answer to the problem. Keep it high level;
the next slides explain how it works.

---

## Slide 6 — System architecture

**On-slide diagram:**

```text
Browser
  │  HTTP/JSON
  ▼
Next.js App Router + TypeScript
  │  /api/v1
  ▼
FastAPI + Pydantic
  ├── Route handlers
  ├── Scheduling domain
  │     ├── Constraint checker
  │     ├── Fitness / soft penalty
  │     └── Genetic Algorithm
  └── Storage adapter
        ├── PostgreSQL / Neon (Vercel)
        └── SQLite (local development)
```

**On-slide bullets:**
- Domain logic is independent of FastAPI and React.
- API handlers load state from storage rather than process memory.
- Serverless-safe: Vercel instances are stateless.

**Speaker notes:** The separation is deliberate: the GA can be tested without a web server,
and the API can run locally or as a Vercel Python function without changing scheduling code.

---

## Slide 7 — Data model

**On-slide bullets:**
- **Faculty:** id, name, department, unavailable/preferred slots, optional daily load limit.
- **Room:** id, name, capacity, type, unavailable slots.
- **Section:** id, name, size, department, semester, unavailable slots.
- **Course:** id, code, name, required room type, duration, sessions per week, lab-block flag.
- **TeachingRequirement:** course + section + faculty + required sessions + overrides.
- **TimeSlot:** id, day, period, start/end time; day+period pairs must be unique.
- **Run records:** parameters, seed, dataset snapshot, metrics, history, candidate, violations.

**Visual:** Entity-relationship diagram centered on `TeachingRequirement`; show `Run` as
the snapshot boundary.

**Speaker notes:** A teaching requirement is the schedulable unit. Each required occurrence
becomes a session such as `tr1:1`, `tr1:2`, `tr1:3`. Run snapshots keep old timetables
coherent even after the dataset changes.

---

## Slide 8 — Hard constraints (must never break)

**On-slide bullets:**
- No faculty double-booking in the same day/period.
- No room double-booking.
- No section double-booking.
- Room capacity must fit the section; room type must match the course.
- Faculty, room, and section unavailable slots must be respected.
- Every required session appears exactly once; no missing or duplicate sessions.
- Every assignment uses a valid slot and room.
- Multi-period sessions must occupy consecutive periods.

**Visual:** Constraint cards with green check / red violation. Show one concrete clash example.

**Speaker notes:** The independent checker re-validates the final best candidate. A schedule
is only labeled `feasible` when the hard-violation count is zero; otherwise it is
`best_effort` with diagnostics.

---

## Slide 9 — Soft constraints (quality, not validity)

**On-slide bullets:**
- Reward faculty preferred slots.
- Reduce gaps in a section's day.
- Balance faculty workload across days and respect daily limits.
- Avoid more than three consecutive teaching periods.
- Distribute repeated sessions of the same requirement across days.
- Weights are configurable; soft penalties never override hard feasibility.

**Visual:** Before/after weekly grids showing fewer gaps and better spread. Add a small
weights panel.

**Speaker notes:** Hard violations are compared first, then weighted soft penalty. This
lexicographic ordering prevents a visually pleasant but invalid schedule from winning.

---

## Slide 10 — GA representation and fitness

**On-slide bullets:**
- Chromosome = list of assignments `(session_id, slot_id, room_id)`.
- Faculty and section come from the teaching requirement, not duplicated in the gene.
- Candidate score = `(hard_violations, soft_penalty)`, compared lexicographically.
- The constraint checker is separate from fitness scoring.
- The best candidate is validated independently before being returned.

**Visual:** One chromosome as a table of 13 sample rows; highlight a gene and its derived
faculty/section.

**Speaker notes:** The representation keeps required-session identity stable, which makes
crossover and repair safer and makes tests meaningful.

---

## Slide 11 — GA lifecycle

**On-slide flow:**

```text
Validate input
  → Build population (random candidates + greedy seed)
  → Evaluate hard + soft
  → Elitism
  → Tournament selection (size 3)
  → Schedule-aware crossover (p = 0.8)
  → Mutation (p = 0.15)
  → Bounded repair (12 attempts per assignment)
  → Re-validate
  → Repeat until feasible / generation limit
  → Independently validate best
  → Return feasible | best_effort | failed
```

**On-slide bullets:**
- Defaults: population 80, generations 250, elite count 2; evaluation/UI defaults 24/60.
- Random seed makes runs reproducible where expected.
- Repair changes placement only, never session identity or count.

**Visual:** Circular GA loop with generation counter and stop conditions.

**Speaker notes:** The run stops as soon as a feasible candidate is found. Early stopping
keeps the request synchronous and fast for college-scale datasets.

---

## Slide 12 — Optimizer quality improvements

**On-slide bullets:**
- Added a **greedy baseline candidate** to the initial population.
- The GA can no longer regress below a constructible feasible seed.
- Added early termination when hard violations reach zero.
- Kept repair bounded and always re-validated after crossover/mutation/repair.
- Persisted final metrics and violations with the run record.
- Result on the documented sample: GA finds a feasible schedule on **5/5 seeds**.

**Visual:** Small arrow chart: "random-only population → greedy-seeded population" and
"5/5 feasible". Use the actual numbers from `evaluation-results.json`.

**Speaker notes:** This was a real correction, not a cosmetic change. The earlier expanded
sample exposed weak search; adding the greedy seed and stopping at feasibility fixed the
regression while keeping the experiment reproducible.

---

## Slide 13 — API surface

**On-slide bullets:**
- `GET /health` and `GET /api/v1/data/status`.
- `GET/PUT/DELETE /api/v1/data` for full dataset read, replace, or clear.
- CRUD for faculty, rooms, sections, courses, time slots, teaching requirements.
- `PUT/DELETE /api/v1/{collection}/{id}` with immutable IDs and reference protection.
- `POST /api/v1/validate`.
- `POST/GET /api/v1/optimization-runs`; schedule, metrics, analytics by run id.
- `POST /api/v1/baseline` and `/baseline/greedy`.
- `GET /api/v1/optimization-runs/{id}/export.csv` with day/room/section/faculty/text filters.
- Pydantic bounds on all GA parameters; consistent structured errors.

**Visual:** Endpoint map grouped into Data, Optimize, Inspect, Export. Show one request and
one error response.

**Speaker notes:** The API is versioned under `/api/v1`. Error responses use a stable
`{error/detail: {code, message, details}}` shape, and the UI surfaces messages next to the
action that failed.

---

## Slide 14 — Frontend experience

**On-slide bullets:**
- **Overview:** Smart Scheduling hero, dataset counts, validate/generate/reset actions,
  live feedback, latest run, timetable summary.
- **Data setup:** guided forms for all six entities, entity-specific constraint fields,
  advanced JSON editor, save, and destructive clear behind confirmation.
- **Timetable:** custom React grid, section/faculty/room views, day/text filters, keyboard
  focus details, filtered CSV export.
- **Analytics:** custom API-backed fitness and distribution visuals with empty states.
- Accessibility: semantic controls, visible focus, responsive sidebar, `prefers-reduced-motion`.

**Visual:** Four screenshots with callouts: counts, filters, violation panel, export.

**Speaker notes:** The UI avoids fabricated chart data. Every visual is backed by the API,
and loading, error, empty, stale-data, and success states are handled explicitly.

---

## Slide 15 — Persistence and refresh behaviour

**On-slide bullets:**
- Durable `cronos_state` key/value table; JSONB values on PostgreSQL, JSON text on SQLite.
- Dataset, run metadata, candidate, history, and violations are stored separately.
- Boot sequence: read dataset → seed sample only on first use → restore latest run.
- `GET /api/v1/data/status` distinguishes "never initialized" from "deliberately cleared".
- **Clear data & timetable** removes dataset and runs, then saves a canonical empty dataset.
- **Reset to sample data** confirms, replaces the dataset, and clears old runs.
- Run snapshots keep schedules valid after dataset edits.

**Visual:** State table:

| Workspace state | `initialized` | On page load |
|---|---|---|
| Never saved | false | Seed sample once |
| Saved | true | Load saved dataset |
| Cleared | true | Stay empty |

**Speaker notes:** The original bug was a frontend boot sequence that re-posted sample data
on every mount. The fix moved persistence semantics into explicit server state and made
both reset and clear intentional user actions. See `DATA_PERSISTENCE_FIX.md`.

---

## Slide 16 — Deployment

**On-slide bullets:**
- One Vercel project with two services:
  - `frontend` → `apps/web` (Next.js)
  - `backend` → repository root, entrypoint `api.index:app` (FastAPI)
- Rewrites send `/api/*` to the backend and everything else to the frontend.
- Production requires `DATABASE_URL` (Neon pooled PostgreSQL).
- SQLite is local-development only; serverless filesystems are not durable.
- CORS origins configured through `CRONOS_WEB_ORIGINS`.
- Live URL: https://cronos-sc.vercel.app

**Visual:** Vercel service diagram with rewrite arrows and environment variables.

**Speaker notes:** The serverless constraint drove the storage design: request handlers
must load state from PostgreSQL every time, because process memory and local files are not
reliable across cold starts or instances.

---

## Slide 17 — Testing and validation

**On-slide bullets:**
- **30 backend tests**: hard constraints, scheduler determinism, session preservation,
  API flow, CRUD, analytics, export filters, invalid references, baseline bounds, CORS,
  snapshot isolation, clear/reset semantics.
- **3 frontend tests**: schedule filtering across visible and nested fields.
- **Production build:** Next.js build succeeds.
- **Evaluator:** reproducible five-seed comparison writes `apps/evaluation-results.json`.
- Commands:
  - `npm run test:api`
  - `npm --prefix apps/web test -- --run`
  - `npm run build:web`
  - `npm run evaluate`

**Visual:** Test pyramid (constraint/unit at base, API integration, build/acceptance at top)
with the actual counts.

**Speaker notes:** Tests focus on correctness that matters: required sessions cannot vanish,
seeded runs reproduce, hard violations are counted, and saved run schedules still work after
the live dataset changes.

---

## Slide 18 — Evaluation results

**On-slide table (documented sample, 5 seeds: 1, 7, 42, 99, 123):**

| Metric | Greedy baseline | GA |
|---|---:|---:|
| Mean hard violations | 0.0 | 0.0 |
| Mean soft penalty | 7.0 | 7.0 |
| Mean runtime | 76.0 ms | 3357.0 ms |
| Feasible runs | 5 / 5 | 5 / 5 |

**Dataset:** 3 faculty, 4 rooms, 3 sections, 4 courses, 15 slots, 6 teaching requirements
(13 sessions). **Parameters:** population 24, generations 60.

**Interpretation:**
- Both approaches are feasible on all five seeds.
- The GA matches the greedy seed on this small sample; it does not prove superiority.
- The honest result is "parity on a small feasible dataset"; on the constrained benchmark,
 constructive greedy is 31.0, GA without local search is 26.2, and GA with local search
 is 22.4, while the GA is substantially slower.

**Visual:** Grouped bar chart for hard violations, soft penalty, and feasibility; annotate
runtime separately because the scale differs.

**Speaker notes:** The committed `evaluation-results.json` is the source of truth. Avoid
claiming the GA beats the baseline. The next step is a larger, harder dataset where search
quality can separate the methods.

---

## Slide 19 — Project journey

**On-slide timeline (all work, grouped by milestone):**

| Milestone | Delivered work |
|---|---|
| Foundation | Domain models, sample dataset, constraint checker, baseline, GA, tests |
| Product shell | Timetable dashboard, root README, MVP documentation, status copy |
| Data and runs | Run violation/final-metric persistence, setup form fields, JSON editor |
| Quality | Greedy seed + early stop, optimizer quality fixes, run snapshot isolation |
| Deployment | Vercel multi-service config, PostgreSQL JSONB persistence, cleared-data flow |
| Reliability | Persistent dataset loading, first-run seeding, latest-run restore, regression tests |

**Visual:** Horizontal commit timeline with 6 grouped eras; keep hashes in appendix only.

**Speaker notes:** The repository history shows an MVP built in layers: algorithm first,
then API/UI, then deployment and persistence hardening. This is useful evidence of
iteration rather than a single untested dump.

---

## Slide 20 — Challenges and fixes

**On-slide bullets:**
- **Stateless deployment:** moved from in-memory assumptions to storage-backed request state.
- **PostgreSQL JSONB:** fixed writes so JSONB values round-trip correctly.
- **Persistence bug:** sample data was re-posted on every mount, wiping user edits; replaced
  with a first-run seed and explicit reset/clear.
- **Weak GA on the expanded sample:** added a greedy seed and early feasibility stop.
- **UI/API drift:** aligned docs, types, labels, and status copy with the implemented behavior.
- **User clarity:** kept GA terminology in advanced controls while using plain-language
  Smart Scheduling copy on the overview.

**Visual:** Bug → cause → fix → proof, four-column table. Highlight the persistence bug.

**Speaker notes:** Each fix has a corresponding regression test or documented acceptance
criterion. The project report records limitations rather than hiding them.

---

## Slide 21 — Limitations

**On-slide bullets:**
- A GA does not prove global optimality; results depend on data, parameters, and weights.
- Evaluation uses a small sample (13 sessions); larger institutional datasets are untested.
- The workspace is shared, not per-user; authentication and multi-tenancy are deferred.
- Optimization runs synchronously; large workloads would need background jobs.
- Soft weights encode design choices and are not objectively "correct".
- Browser-level E2E tests and formal academic references remain follow-up work.
- Some input sets may be infeasible; the UI reports `best_effort` with diagnostics rather
  than pretending the schedule is valid.

**Visual:** "Known boundaries" panel with green (handled), amber (limited), red (deferred).

**Speaker notes:** Honest limitations are part of the evaluation. The MVP is designed to
fail visibly and explain why.

---

## Slide 22 — Future work and conclusion

**Future work:**
- Larger and harder benchmark datasets; tune population, generations, and repair.
- Manual schedule editing with re-validation.
- Spreadsheet/PDF import and export.
- Background optimization jobs, progress streaming, and rate limiting.
- Authentication, per-user workspaces, and normalized migration rollout.
- Optional alternative optimizers for comparison.

**Conclusion:**
- Cronos delivers a tested, deployable timetable MVP with explicit hard-constraint
  validation, seeded genetic optimization, persisted run snapshots, analytics, filtering,
  and CSV export.
- Current evidence supports feasibility and workflow completeness on the documented sample,
  not global optimality or production-scale performance.

**Visual:** Three columns: "Shipped", "Measured", "Next". End with the Cronos wordmark.

**Speaker notes:** Close with the distinction between a working MVP and a production
institutional system. Both are valuable; only the first is claimed here.

---

## Slide 23 — Demo and Q&A

**Suggested 3-minute demo path:**
1. Open the deployed app; show the saved dataset and Overview counts.
2. Click **Validate data**; point out the success feedback.
3. Generate a timetable; show status, hard violations, soft penalty, runtime, and history.
4. Open **Timetable**; filter by section and by faculty; hover/focus a session.
5. Export filtered CSV; open it and show readable labels.
6. Open **Analytics**; show fitness history and resource distributions.
7. Refresh the page; show that data and the latest timetable are restored.
8. Show **Reset to sample data** confirmation and explain **Clear data & timetable**.

**Q&A prompts to prepare for:**
- Why a GA instead of an ILP/constraint solver?
- How do you know a schedule is valid?
- Why does the GA only match the baseline?
- What happens on an infeasible dataset?
- How would this scale to a full college?
- What is stored per run, and why snapshot the dataset?

**Visual:** QR code to the app, plus a "Thank you" slide with repository/docs links.

---

## Appendix A1 — API map

| Area | Endpoints |
|---|---|
| Health | `GET /health`, `GET /api/v1/health`, `GET /v1/models` |
| Dataset | `GET /api/v1/data`, `PUT /api/v1/data`, `DELETE /api/v1/data`, `GET /api/v1/data/status` |
| Collections | `GET/POST /api/v1/faculty`, `/rooms`, `/sections`, `/courses`, `/time-slots`, `/teaching-requirements` |
| Collection items | `PUT/DELETE /api/v1/{collection}/{id}` |
| Validation | `POST /api/v1/validate` |
| Optimization | `POST /api/v1/optimization-runs`, `GET /api/v1/optimization-runs` |
| Run inspection | `GET /api/v1/optimization-runs/{id}`, `/schedule`, `/metrics`, `/analytics` |
| Baselines | `POST /api/v1/baseline`, `POST /api/v1/baseline/greedy` |
| Export | `GET /api/v1/optimization-runs/{id}/export.csv?q=&day=&room=&section=&faculty=` |
| Sample | `POST /api/v1/sample-data` |

**Speaker notes:** IDs are immutable on update, duplicate IDs return `409`, referenced
entities cannot be deleted, and invalid references return `422` with details.

---

## Appendix A2 — Terminology

| Term | Meaning |
|---|---|
| Session | One required occurrence of a teaching requirement |
| Chromosome | A complete candidate schedule: list of `(session, slot, room)` assignments |
| Hard violation | A broken mandatory rule; any count above zero means infeasible |
| Soft penalty | Weighted quality cost; only compared when hard violations tie |
| Feasible | Zero hard violations, reported explicitly |
| Best effort | No feasible candidate found within limits; diagnostics included |
| Elitism | Retaining the best candidates into the next generation |
| Repair | Bounded local reassignment after crossover/mutation |
| Snapshot | Dataset and result stored with a run so old schedules stay coherent |

---

## Presentation checklist

- [ ] Replace `[Your name]` and `[Date]` on the title slide.
- [ ] Capture current screenshots of Overview, Setup, Timetable, and Analytics.
- [ ] Paste values from `apps/evaluation-results.json`, not from memory.
- [ ] Re-run `npm run test:api`, frontend tests, `npm run build:web`, and `npm run evaluate`.
- [ ] Verify the deployed URL and a fresh generation before presenting.
- [ ] Keep the GA/baseline comparison honest: parity on the sample, not superiority.
- [ ] Prepare one infeasible-data example if asked about diagnostics.
- [ ] Export a backup CSV and keep it available offline.
