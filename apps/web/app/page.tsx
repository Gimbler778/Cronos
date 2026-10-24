"use client";

import { useEffect, useMemo, useState } from "react";
import { filterSchedule } from "./schedule";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
type View = "overview" | "setup" | "section" | "faculty" | "room" | "analytics";
type Entity = "faculty" | "rooms" | "sections" | "courses" | "time-slots" | "teaching-requirements";
type Run = { id: string; status: string; hard_violations: number | null; soft_penalty: number | null; runtime_ms: number; generations: number; diagnostics: string[] };
type Data = { faculty: Record<string, unknown>[]; rooms: Record<string, unknown>[]; sections: Record<string, unknown>[]; courses: Record<string, unknown>[]; time_slots: Record<string, unknown>[]; teaching_requirements: Record<string, unknown>[] };
type Session = { session_id: string; slot_id: string; room_id: string; course_id: string; section_id: string; faculty_id: string; slot: { day: string; period: number; start_time: string; end_time: string }; room: { name: string } };
type Point = { generation: number; hard_violations: number; soft_penalty: number };
type Analytics = { sessions_by_slot: Record<string, number>; sessions_by_room: Record<string, number>; sessions_by_section: Record<string, number> };
type Config = { population_size: number; max_generations: number; crossover_probability: number; mutation_probability: number; tournament_size: number; elite_count: number; random_seed: number };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail?.message ?? body.message ?? `Request failed (${response.status})`);
  return body as T;
}

const emptyData: Data = { faculty: [], rooms: [], sections: [], courses: [], time_slots: [], teaching_requirements: [] };
const emptyConfig: Config = { population_size: 40, max_generations: 100, crossover_probability: 0.8, mutation_probability: 0.15, tournament_size: 3, elite_count: 2, random_seed: 42 };

export default function Home() {
  const [data, setData] = useState<Data | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [schedule, setSchedule] = useState<Session[]>([]);
  const [history, setHistory] = useState<Point[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [panel, setPanel] = useState<View>("overview");
  const [filter, setFilter] = useState("");
  const [editor, setEditor] = useState("");
  const [config, setConfig] = useState<Config>(emptyConfig);
  const [message, setMessage] = useState("Loading the sample dataset…");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  async function loadData() {
    const value = await request<Data>("/api/v1/data");
    setData(value);
    setEditor(JSON.stringify(value, null, 2));
  }

  async function loadSample() {
    setBusy(true); setError("");
    try { await request("/api/v1/sample-data", { method: "POST" }); await loadData(); setMessage("Sample data loaded and ready to validate."); }
    catch (value) { const text = value instanceof Error ? value.message : "Could not load sample data."; setError(text); setMessage("The API is unavailable."); }
    finally { setBusy(false); }
  }

  async function validate() {
    setBusy(true); setError("");
    try { const result = await request<{ valid: boolean; errors: Array<{ message: string }> }>("/api/v1/validate", { method: "POST" }); setMessage(result.valid ? "Validation passed. Ready to generate." : result.errors.map(item => item.message).join(" ")); }
    catch (value) { setError(value instanceof Error ? value.message : "Validation request failed."); }
    finally { setBusy(false); }
  }

  async function saveData() {
    setBusy(true); setError("");
    try { const value = JSON.parse(editor) as Data; await request("/api/v1/data", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) }); setData(value); setMessage("Dataset saved and references validated."); }
    catch (value) { const text = value instanceof SyntaxError ? "Dataset editor contains invalid JSON." : value instanceof Error ? value.message : "Dataset could not be saved."; setError(text); }
    finally { setBusy(false); }
  }

  async function generate() {
    setBusy(true); setError("");
    try {
      const result = await request<Run>("/api/v1/optimization-runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(config) });
      const [scheduleResult, metrics, summary] = await Promise.all([
        request<{ sessions: Session[] }>(`/api/v1/optimization-runs/${result.id}/schedule`),
        request<{ history: Point[] }>(`/api/v1/optimization-runs/${result.id}/metrics`),
        request<Analytics>(`/api/v1/optimization-runs/${result.id}/analytics`),
      ]);
      setRun(result); setSchedule(scheduleResult.sessions); setHistory(metrics.history); setAnalytics(summary); setPanel("overview"); setMessage(`Run finished with status: ${result.status}.`);
    } catch (value) { setError(value instanceof Error ? value.message : "Generation failed."); }
    finally { setBusy(false); }
  }

  useEffect(() => { void loadSample(); }, []);
  const counts = data ? [data.sections.length, data.faculty.length, data.rooms.length, data.teaching_requirements.length] : [0, 0, 0, 0];
  const filteredSchedule = useMemo(() => filterSchedule(schedule, filter), [filter, schedule]);
  const nav: Array<[View, string]> = [["overview", "Overview"], ["setup", "Data setup"], ["section", "Timetable"], ["analytics", "Analytics"]];

  return <main className="shell">
    <aside><div className="brand">CRONOS<span>.</span></div><p className="muted">Academic scheduling studio</p><nav aria-label="Primary navigation">{nav.map(([value, label]) => <button className={panel === value ? "active" : ""} key={value} onClick={() => setPanel(value)}>{label}</button>)}</nav><div className="side-note">Local-first<br /><span>Deployment is reserved for a later phase.</span></div></aside>
    <section className="content"><header><div><p className="eyebrow">WORKSPACE / {panel.toUpperCase()}</p><h1>Timetable command center</h1></div><button className="outline" onClick={loadSample} disabled={busy}>Reload sample</button></header>
      {error && <div className="error" role="alert"><strong>Action failed.</strong> {error}</div>}
      {panel === "setup" ? <Setup editor={editor} setEditor={setEditor} saveData={saveData} busy={busy} data={data} /> : panel === "analytics" ? <AnalyticsPanel analytics={analytics} history={history} /> : <><div className="hero"><div><p className="eyebrow">GENETIC OPTIMIZER</p><h2>Build a schedule<br /><em>that works.</em></h2><p className="hero-copy">Coordinate courses, faculty, rooms, and sections with transparent hard-constraint validation.</p><div className="actions"><button onClick={validate} disabled={busy}>Validate data</button><button className="secondary" onClick={generate} disabled={busy}>Generate timetable →</button></div></div><div className="orb" aria-hidden="true"><div className="orb-inner">GA<br /><small>{busy ? "WORKING" : "READY"}</small></div></div></div><p className="notice" aria-live="polite">{busy ? "Working…" : message}</p><div className="stats">{["Sections", "Faculty", "Rooms", "Teaching reqs"].map((label, index) => <div className="card" key={label}><span>{label}</span><strong>{counts[index]}</strong><small>configured</small></div>)}</div><OptimizationControls config={config} setConfig={setConfig} disabled={busy} /><div className="lower"><RunPanel run={run} history={history} /><SchedulePanel schedule={filteredSchedule} run={run} filter={filter} setFilter={setFilter} panel={panel} setPanel={setPanel} /></div></>}
    </section>
  </main>;
}

function Setup({ editor, setEditor, saveData, busy, data }: { editor: string; setEditor: (value: string) => void; saveData: () => void; busy: boolean; data: Data | null }) {
  const [entity, setEntity] = useState<Entity>("faculty");
  const [record, setRecord] = useState("{}");
  const [formError, setFormError] = useState("");
  const addRecord = async () => {
    setFormError("");
    try {
      const value = JSON.parse(record);
      if (!value.id) throw new Error("Each record needs an id.");
      await request(`/${entity}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
      setRecord("{}"); await request<Data>("/api/v1/data").then(next => { setEditor(JSON.stringify(next, null, 2)); }); 
    } catch (value) { setFormError(value instanceof Error ? value.message : "Record must be valid JSON."); }
  };
  return <div className="setup-stack"><div className="panel setup"><div className="panel-head"><div><p className="eyebrow">DATA SETUP</p><h2>Academic dataset</h2></div><button onClick={saveData} disabled={busy}>Save dataset</button></div><p className="muted-dark">Use the guided record form for additions, or edit the complete validated JSON snapshot for advanced changes.</p><div className="record-form"><label>Entity<select value={entity} onChange={event => setEntity(event.target.value as Entity)}>{(["faculty", "rooms", "sections", "courses", "time-slots", "teaching-requirements"] as Entity[]).map(item => <option key={item}>{item}</option>)}</select></label><label>New record JSON<textarea aria-label="New record JSON" value={record} onChange={event => setRecord(event.target.value)} /></label><button onClick={addRecord}>Add record</button>{formError && <p className="field-error" role="alert">{formError}</p>}</div><textarea aria-label="Dataset JSON" value={editor} onChange={event => setEditor(event.target.value)} spellCheck={false} />{data && <p className="notice">Current dataset is persisted locally; PostgreSQL is optional and deployment remains deferred.</p>}</div></div>;
}

function OptimizationControls({ config, setConfig, disabled }: { config: Config; setConfig: (value: Config) => void; disabled: boolean }) {
  const update = (key: keyof Config, value: string) => setConfig({ ...config, [key]: Number(value) });
  return <details className="panel controls"><summary>Optimization controls <span>population, generations, probabilities, seed</span></summary><div className="control-grid">{(["population_size", "max_generations", "crossover_probability", "mutation_probability", "tournament_size", "elite_count", "random_seed"] as (keyof Config)[]).map(key => <label key={key}>{key.replaceAll("_", " ")}<input type="number" step={key.includes("probability") ? "0.05" : "1"} min={key.includes("probability") ? "0" : "1"} value={config[key]} disabled={disabled} onChange={event => update(key, event.target.value)} /></label>)}</div></details>;
}

function RunPanel({ run, history }: { run: Run | null; history: Point[] }) {
  return <div className="panel"><div className="panel-head"><h3>Latest run</h3>{run && <span className={`badge ${run.status}`}>{run.status}</span>}</div>{run ? <div className="metrics"><Metric label="Hard violations" value={run.hard_violations ?? "—"} /><Metric label="Soft penalty" value={run.soft_penalty ?? "—"} /><Metric label="Generations" value={run.generations} /><Metric label="Runtime" value={`${run.runtime_ms} ms`} /></div> : <p className="empty">No optimization run yet. Generate a timetable to see metrics.</p>}{run?.diagnostics.length ? <p className="diagnostics">{run.diagnostics.join(" ")}</p> : null}{history.length > 0 && <div className="schedule">{history.slice(-8).map(point => <div className="schedule-row" key={point.generation}><span>Gen {point.generation}</span><span>{point.hard_violations} hard</span><span>{point.soft_penalty.toFixed(2)} soft</span></div>)}</div>}</div>;
}

function SchedulePanel({ schedule, run, filter, setFilter, panel, setPanel }: { schedule: Session[]; run: Run | null; filter: string; setFilter: (value: string) => void; panel: View; setPanel: (value: View) => void }) {
  const field = panel === "section" ? "section_id" : panel === "faculty" ? "faculty_id" : panel === "room" ? "room_id" : null;
  const groups = field ? [...new Set(schedule.map(item => item[field]))] : [];
  return <div className="panel"><div className="panel-head"><h3>{panel === "overview" ? "Schedule preview" : `${panel} timetable`}</h3>{schedule.length > 0 && run && <a href={`${API}/api/v1/optimization-runs/${run.id}/export.csv`}>Export CSV</a>}</div><div className="filters">{(["overview", "section", "faculty", "room"] as View[]).map(value => <button className={panel === value ? "" : "secondary"} key={value} onClick={() => setPanel(value)}>{value}</button>)}</div>{groups.length > 0 && <div className="filters">{groups.map(group => <button className="secondary" key={group} onClick={() => setFilter(group)}>{group}</button>)}</div>}<label className="sr-only" htmlFor="schedule-filter">Filter schedule</label><input id="schedule-filter" placeholder="Filter session, slot, room, section, or faculty" value={filter} onChange={event => setFilter(event.target.value)} />{schedule.length === 0 ? <p className="empty">Generate a timetable to see scheduled sessions.</p> : schedule.length ? <div className="schedule">{schedule.map(item => <div className="schedule-row schedule-detail" key={item.session_id}><b>{item.session_id}</b><span>{item.slot.day} P{item.slot.period}</span><span>{item.room.name}</span><small>{item.section_id} · {item.faculty_id}</small></div>)}</div> : <p className="empty">No sessions match this filter.</p>}</div>;
}

function AnalyticsPanel({ analytics, history }: { analytics: Analytics | null; history: Point[] }) {
  return <div className="analytics-grid"><div className="panel"><h3>Fitness progression</h3>{history.length ? history.map(point => <div className="bar-row" key={point.generation}><span>G{point.generation}</span><div><i style={{ width: `${Math.min(100, point.hard_violations * 20 + point.soft_penalty)}%` }} /></div><b>{point.hard_violations} / {point.soft_penalty.toFixed(1)}</b></div>) : <p className="empty">Generate a timetable to see metrics.</p>}</div><div className="panel"><h3>Resource distribution</h3>{analytics ? <><Distribution title="By slot" values={analytics.sessions_by_slot} /><Distribution title="By room" values={analytics.sessions_by_room} /><Distribution title="By section" values={analytics.sessions_by_section} /></> : <p className="empty">Run analytics will appear here after generation.</p>}</div></div>;
}

function Distribution({ title, values }: { title: string; values: Record<string, number> }) { return <div className="distribution"><strong>{title}</strong>{Object.keys(values).length ? Object.entries(values).map(([key, value]) => <div key={key}><span>{key}</span><b>{value}</b></div>) : <p className="empty">No sessions</p>}</div>; }
function Metric({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
