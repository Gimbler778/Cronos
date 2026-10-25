# Data Persistence Fix

## The issue

Manually entered data disappears whenever the page is reloaded, and the **Reload sample**
button appears to be the only way to get data into the app. Users lose their dataset on every
refresh (F5, hard refresh, or reopening the tab).

## Root cause

Backend persistence is not the problem. The API already stores the dataset and every
optimization run in SQLite locally (`apps/cronos.db`) or PostgreSQL on Vercel, via
`apps/api/storage.py`.

The cause is the frontend boot sequence:

```ts
// apps/web/app/page.tsx (before the fix)
useEffect(() => {
  void loadSample();   // POST /api/v1/sample-data on every mount
  ...
}, []);
```

`loadSample()` calls `POST /api/v1/sample-data`, which runs
`storage.save_dataset(sample_dataset())` (`apps/api/routes.py`). That call **overwrites the
entire saved dataset** with the demo dataset. So every mount silently replaces whatever the
user saved.

Manual records are written to the database immediately when added through the form
(`POST /api/v1/faculty`, `/rooms`, `/sections`, `/courses`, `/time-slots`,
`/teaching-requirements`), so the data does persist — it is destroyed a moment later by the
sample reload on the next mount.

Three related problems were found while investigating:

1. **Stale counters.** After adding a record, `Setup.addRecord` refreshes only the raw JSON
   editor (`editor`) and not the `data` state, so the Overview counters and panels stay out
   of date until a reload — and the reload then wipes the data.
2. **Lost timetable on refresh.** Generated runs are stored in the database, but `run`,
   `schedule`, `history`, and `analytics` are React-only state. A refresh loses the visible
   timetable even though it is still available from the API.
3. **Unsaved editor changes.** Edits typed into the Advanced JSON editor only exist in the
   textarea until **Save dataset** is pressed. A reload discards them regardless of the
   sample-data overwrite.

## Solution

### 1. Load saved data on mount instead of overwriting it

Replace the unconditional `loadSample()` in the mount effect with a boot sequence:

1. `GET /api/v1/data` — read the persisted dataset.
2. Seed the sample **only on the first run**, then reload it.
3. Restore the latest saved timetable, if one exists.

The result: refresh keeps the user's data and timetable; the sample is created once for a
brand-new workspace. The initial status text is also updated so it no longer claims that the
sample dataset is always being loaded.

### 2. Distinguish "first run" from "deliberately cleared"

`DELETE /api/v1/data` currently calls `storage.clear_all()`, which deletes the `dataset` row
too. That makes an empty dataset indistinguishable from a workspace that has never been
used, so the client cannot decide whether to seed.

Fix: persist a canonical empty dataset after clearing, and expose a status endpoint.

- `apps/api/storage.py`: add `dataset_exists()` (checks whether the `dataset` key is present).
- `apps/api/routes.py`: `clear_data()` calls `clear_all()` and then `save_dataset(Dataset())`.
- `apps/api/routes.py`: add `GET /api/v1/data/status` returning `{"initialized": bool}`.

Behavior:

| State | `initialized` | On mount |
| --- | --- | --- |
| Never saved | `false` | Seed sample once |
| Saved dataset | `true` | Load it |
| Cleared dataset | `true` | Stay empty |

### 3. Make the sample button explicit and destructive

- Rename **Reload sample** to **Reset to sample data**.
- Ask for confirmation with `window.confirm`, warning that the saved dataset will be replaced.
- Update the success message to say the previous dataset was replaced.
- Clear existing optimization runs during the reset so a timetable from the previous dataset
  cannot be restored after the reset.
- Keep it available on the Overview page (and optionally on Data setup next to
  **Clear data & timetable**).

The button is not useless after the fix — it becomes the *only* way to restore the demo data,
which is exactly what an explicit reset should be.

### 4. Keep local state in sync after writes

In `Setup.addRecord`, after the `POST` completes, refresh **both** `data` and `editor` from
`GET /api/v1/data`. `saveData` already updates both.

### 5. Restore the latest run on load

After the dataset loads:

1. `GET /api/v1/optimization-runs` (already sorted newest first by `storage.list_runs`).
2. For the newest run, fetch in parallel:
   - `GET /api/v1/optimization-runs/{id}/schedule`
   - `GET /api/v1/optimization-runs/{id}/metrics`
   - `GET /api/v1/optimization-runs/{id}/analytics`
3. Populate `run`, `schedule`, `history`, and `analytics` and show a
   "latest timetable restored" message.

If restoring the run fails, the dataset must still load; the timetable panel shows its normal
empty state and the error is reported to the user.

### 6. Documentation

Update the README "Run the web app" section: the dashboard loads the saved dataset, the sample
is seeded only on first use, and the confirmed reset replaces the saved dataset.

## Files to change

| File | Change |
| --- | --- |
| `apps/web/app/page.tsx` | Boot sequence, sample reset confirmation + label, refresh `data` after adding records, restore latest run |
| `apps/api/storage.py` | Add `dataset_exists()` |
| `apps/api/routes.py` | Save an empty dataset on clear; add `GET /api/v1/data/status`; clear runs on sample reset |
| `apps/tests/test_api.py` | Regression tests for persistence and clear semantics |
| `README.md` | Describe the new load/reset behavior |

No change is needed in the storage adapter's write path: it already persists correctly.

## Acceptance criteria

1. Refreshing the page keeps manually entered records; the Overview counters match the saved
   dataset.
2. A brand-new workspace (no dataset row) receives the sample dataset exactly once.
3. **Clear data & timetable** leaves the app empty after a refresh; the sample does not
   reappear on its own.
4. **Reset to sample data** asks for confirmation and clearly reports that saved data was
   replaced.
5. Adding a record updates the counters without a manual reload.
6. Refreshing the page restores the latest generated timetable, metrics, and analytics.
7. If the API is unavailable, the app shows an error instead of silently presenting an empty
   dataset.

## Notes and limits

- The dataset is a **single shared workspace**, not per-browser or per-user. Multi-user
  separation is out of scope until authentication is added.
- On Vercel, persistence requires `DATABASE_URL`; serverless filesystems are not durable and
  SQLite is local-development only (already documented in the README).
- Each optimization run stores a dataset snapshot, so a timetable remains coherent if the
  current dataset is edited afterwards.
- **Reset to sample data** clears existing optimization runs as well as replacing the dataset,
  so refresh cannot restore a timetable generated from the previous dataset.
