"use client";

import { type CSSProperties, useEffect, useMemo, useState } from "react";
import { filterSchedule } from "./schedule";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
type View = "overview" | "setup" | "section" | "faculty" | "room" | "analytics";
type Entity = "faculty" | "rooms" | "sections" | "courses" | "time-slots" | "teaching-requirements";
type Violation = { code: string; entity_id?: string; slot?: string };
type Run = { id: string; status: string; hard_violations: number | null; soft_penalty: number | null; runtime_ms: number; generations: number; diagnostics: string[]; violations?: Violation[] };
type Data = { faculty: Record<string, unknown>[]; rooms: Record<string, unknown>[]; sections: Record<string, unknown>[]; courses: Record<string, unknown>[]; time_slots: Record<string, unknown>[]; teaching_requirements: Record<string, unknown>[] };
type Session = { session_id: string; slot_id: string; room_id: string; course_id: string; section_id: string; faculty_id: string; slot: { day: string; period: number; start_time: string; end_time: string }; room: { id: string; name: string }; course?: { id: string; code: string; name: string; duration?: number }; section?: { id: string; name: string }; faculty?: { id: string; name: string } };
type Point = { generation: number; hard_violations: number; soft_penalty: number };
type Analytics = { sessions_by_slot: Record<string, number>; sessions_by_room: Record<string, number>; sessions_by_section: Record<string, number> };
type Config = { population_size: number; max_generations: number; crossover_probability: number; mutation_probability: number; tournament_size: number; elite_count: number; random_seed: number };

const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const sortDays = (days: string[]) => [...days].sort((left, right) => {
  const leftIndex = dayOrder.indexOf(left);
  const rightIndex = dayOrder.indexOf(right);
  return (leftIndex === -1 ? dayOrder.length : leftIndex) - (rightIndex === -1 ? dayOrder.length : rightIndex) || left.localeCompare(right);
});

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
  const [sidebarOpen, setSidebarOpen] = useState(true);
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
      setRun(result); setSchedule(scheduleResult.sessions); setHistory(metrics.history); setAnalytics(summary); setMessage(`Run finished with status: ${result.status}.`);
    } catch (value) { setError(value instanceof Error ? value.message : "Generation failed."); }
    finally { setBusy(false); }
  }

  useEffect(() => {
    void loadSample();
    const mediaQuery = window.matchMedia("(max-width: 800px)");
    const updateSidebar = () => setSidebarOpen(!mediaQuery.matches);
    updateSidebar();
    mediaQuery.addEventListener("change", updateSidebar);
    return () => mediaQuery.removeEventListener("change", updateSidebar);
  }, []);
  const counts = data ? [data.sections.length, data.faculty.length, data.rooms.length, data.teaching_requirements.length] : [0, 0, 0, 0];
  const filteredSchedule = useMemo(() => filterSchedule(schedule, filter), [filter, schedule]);
  const nav: Array<[View, string]> = [["overview", "Overview"], ["setup", "Data setup"], ["section", "Timetable"], ["analytics", "Analytics"]];

  return <main className={`shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
    <aside>
      <div className="brand">CRONOS</div><p className="muted">Academic scheduling studio</p><nav aria-label="Primary navigation">{nav.map(([value, label]) => <button className={panel === value ? "active" : ""} key={value} onClick={() => { setPanel(value); if (window.matchMedia("(max-width: 800px)").matches) setSidebarOpen(false); }}>{label}</button>)}</nav><div className="side-note">Local-first<br /><span>Deployment is reserved for a later phase.</span></div>
    </aside>
    <section className="content"><header><div className="header-title"><button className="mobile-menu" type="button" aria-label={sidebarOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={sidebarOpen} onClick={() => setSidebarOpen(open => !open)}><span aria-hidden="true">☰</span></button><div><p className="eyebrow">WORKSPACE / {panel.toUpperCase()}</p><h1>Timetable command center</h1></div></div><button className="outline" onClick={loadSample} disabled={busy}>Reload sample</button></header>
      {error && <div className="error" role="alert"><strong>Action failed.</strong> {error}</div>}
      {panel === "setup" ? <Setup editor={editor} setEditor={setEditor} saveData={saveData} busy={busy} data={data} /> : panel === "analytics" ? <AnalyticsPanel analytics={analytics} history={history} run={run} /> : ["section", "faculty", "room"].includes(panel) ? <SchedulePanel schedule={filteredSchedule} run={run} filter={filter} setFilter={setFilter} panel={panel} setPanel={setPanel} /> : <><div className="hero"><div className="hero-title"><p className="eyebrow">SMART SCHEDULING</p><h2>Build a schedule<br /><em>that works.</em></h2></div><p className="hero-copy">Coordinate courses, faculty, rooms, and sections with transparent hard-constraint validation.</p><div className="actions"><button onClick={validate} disabled={busy}>Validate data</button><button className="secondary" onClick={generate} disabled={busy}>Generate timetable <span aria-hidden="true">→</span></button></div></div><p className="notice" aria-live="polite">{busy ? "Working…" : message}</p><div className="stats">{["Sections", "Faculty", "Rooms", "Teaching reqs"].map((label, index) => <div className="card" key={label}><span>{label}</span><strong>{counts[index]}</strong><small>configured</small></div>)}</div><OptimizationControls config={config} setConfig={setConfig} disabled={busy} /><div className="lower"><RunPanel run={run} history={history} /><TimetableSummary schedule={schedule} run={run} openTimetable={() => setPanel("section")} /></div></>}
    </section>
  </main>;
}

function Setup({ editor, setEditor, saveData, busy, data }: { editor: string; setEditor: (value: string) => void; saveData: () => void; busy: boolean; data: Data | null }) {
  const [entity, setEntity] = useState<Entity>("faculty");
  const [record, setRecord] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  type Field = { key: string; label: string; type?: "number" | "time" | "checkbox" | "slot-list"; placeholder?: string; required?: boolean; help?: string };
  const fields: Record<Entity, Field[]> = {
    faculty: [
      { key: "id", label: "Short ID", placeholder: "f1", required: true },
      { key: "name", label: "Name", placeholder: "Dr. A. Sharma", required: true },
      { key: "department", label: "Department", placeholder: "Computer Science", required: true },
      { key: "unavailable_slots", label: "Unavailable slots", type: "slot-list", placeholder: "mon-1, wed-3", help: "Comma-separated time-slot IDs." },
      { key: "preferred_slots", label: "Preferred slots", type: "slot-list", placeholder: "tue-2, thu-1", help: "Comma-separated time-slot IDs." },
      { key: "daily_load_limit", label: "Daily teaching limit", type: "number", placeholder: "3", help: "Optional maximum sessions per day." },
    ],
    rooms: [
      { key: "id", label: "Short ID", placeholder: "r1", required: true },
      { key: "name", label: "Room name", placeholder: "Room 101", required: true },
      { key: "capacity", label: "Capacity", type: "number", placeholder: "60", required: true },
      { key: "room_type", label: "Room type", placeholder: "lecture", required: true },
      { key: "unavailable_slots", label: "Unavailable slots", type: "slot-list", placeholder: "mon-1, fri-4", help: "Comma-separated time-slot IDs." },
    ],
    sections: [
      { key: "id", label: "Short ID", placeholder: "s1", required: true },
      { key: "name", label: "Section name", placeholder: "B.Tech CSE A", required: true },
      { key: "size", label: "Student count", type: "number", placeholder: "40", required: true },
      { key: "department", label: "Department", placeholder: "Computer Science", required: true },
      { key: "semester", label: "Semester", placeholder: "3", required: true },
      { key: "unavailable_slots", label: "Unavailable slots", type: "slot-list", placeholder: "mon-1, wed-3", help: "Comma-separated time-slot IDs." },
    ],
    courses: [
      { key: "id", label: "Short ID", placeholder: "c1", required: true },
      { key: "code", label: "Course code", placeholder: "CS301", required: true },
      { key: "name", label: "Course name", placeholder: "Algorithms", required: true },
      { key: "required_room_type", label: "Room type", placeholder: "lecture", required: true },
      { key: "duration", label: "Duration (slots)", type: "number", placeholder: "1", required: true },
      { key: "sessions_per_week", label: "Sessions per week", type: "number", placeholder: "3", required: true },
      { key: "consecutive_slots_required", label: "Require consecutive slots", type: "checkbox", help: "Keep multi-slot sessions together." },
    ],
    "time-slots": [
      { key: "id", label: "Short ID", placeholder: "mon-1", required: true },
      { key: "day", label: "Day", placeholder: "Monday", required: true },
      { key: "period", label: "Period", type: "number", placeholder: "1", required: true },
      { key: "start_time", label: "Starts at", type: "time", required: true },
      { key: "end_time", label: "Ends at", type: "time", required: true },
    ],
    "teaching-requirements": [
      { key: "id", label: "Short ID", placeholder: "tr1", required: true },
      { key: "course_id", label: "Course ID", placeholder: "c1", required: true },
      { key: "section_id", label: "Section ID", placeholder: "s1", required: true },
      { key: "faculty_id", label: "Faculty ID", placeholder: "f1", required: true },
      { key: "required_sessions", label: "Sessions needed", type: "number", placeholder: "3", required: true },
      { key: "duration", label: "Duration (slots)", type: "number", placeholder: "1", required: true },
      { key: "room_type", label: "Room type override", placeholder: "lab", help: "Optional; defaults to the course room type." },
    ],
  };
  const addRecord = async () => {
    setFormError("");
    try {
      const value = Object.fromEntries(fields[entity].map(field => {
        const raw = record[field.key]?.trim() ?? "";
        if (field.required && !raw) throw new Error(`${field.label} is required.`);
        if (field.type === "checkbox") return [field.key, record[field.key] === "true"];
        if (!raw && !field.required) return [field.key, field.type === "slot-list" ? [] : undefined];
        if (field.type === "number") return [field.key, Number(raw)];
        if (field.type === "slot-list") return [field.key, raw.split(",").map(item => item.trim()).filter(Boolean)];
        return [field.key, raw];
      }));
      const payload = Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined));
      await request(`/api/v1/${entity}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      setRecord({}); await request<Data>("/api/v1/data").then(next => { setEditor(JSON.stringify(next, null, 2)); });
    } catch (value) { setFormError(value instanceof Error ? value.message : "Record could not be added."); }
  };
  return <div className="setup-stack"><div className="panel setup"><div className="panel-head"><div><p className="eyebrow">DATA SETUP</p><h2>Academic dataset</h2></div><button onClick={saveData} disabled={busy}>Save dataset</button></div><p className="muted-dark">Add faculty, rooms, sections, courses, time slots, and teaching requirements using simple fields. IDs connect related records.</p><div className="record-form"><label>What do you want to add?<select value={entity} onChange={event => { setEntity(event.target.value as Entity); setRecord({}); setFormError(""); }}>{(["faculty", "rooms", "sections", "courses", "time-slots", "teaching-requirements"] as Entity[]).map(item => <option key={item}>{item}</option>)}</select></label><div className="field-grid">{fields[entity].map(field => <label key={field.key} className={field.type === "checkbox" ? "checkbox-field" : undefined}>{field.type === "checkbox" ? <><input type="checkbox" checked={record[field.key] === "true"} onChange={event => setRecord({ ...record, [field.key]: String(event.target.checked) })} />{field.label}</> : <><span>{field.label}</span><input type={field.type === "slot-list" ? "text" : field.type ?? "text"} placeholder={field.placeholder} value={record[field.key] ?? ""} onChange={event => setRecord({ ...record, [field.key]: event.target.value })} required={field.required} />{field.help && <small>{field.help}</small>}</>}</label>)}</div><button onClick={addRecord}>Add {entity.replaceAll("-", " ")}</button>{formError && <p className="field-error" role="alert">{formError}</p>}</div><details className="advanced-editor"><summary>Advanced: edit the complete dataset snapshot</summary><textarea aria-label="Dataset JSON" value={editor} onChange={event => setEditor(event.target.value)} spellCheck={false} /></details>{data && <p className="notice">Current dataset is persisted locally; PostgreSQL is optional and deployment remains deferred.</p>}</div></div>;
}

function OptimizationControls({ config, setConfig, disabled }: { config: Config; setConfig: (value: Config) => void; disabled: boolean }) {
  const update = (key: keyof Config, value: string) => setConfig({ ...config, [key]: Number(value) });
  return <details className="panel controls"><summary>Optimization controls <span>population, generations, probabilities, seed</span></summary><div className="control-grid">{(["population_size", "max_generations", "crossover_probability", "mutation_probability", "tournament_size", "elite_count", "random_seed"] as (keyof Config)[]).map(key => <label key={key}>{key.replaceAll("_", " ")}<input type="number" step={key.includes("probability") ? "0.05" : "1"} min={key.includes("probability") ? "0" : "1"} value={config[key]} disabled={disabled} onChange={event => update(key, event.target.value)} /></label>)}</div></details>;
}

function RunPanel({ run, history }: { run: Run | null; history: Point[] }) {
  return <div className="panel"><div className="panel-head"><h3>Latest run</h3>{run && <span className={`badge ${run.status}`}>{run.status}</span>}</div>{run ? <div className="metrics"><Metric label="Hard violations" value={run.hard_violations ?? "—"} /><Metric label="Soft penalty" value={run.soft_penalty ?? "—"} /><Metric label="Generations" value={run.generations} /><Metric label="Runtime" value={`${run.runtime_ms} ms`} /></div> : <p className="empty">No optimization run yet. Generate a timetable to see metrics.</p>}{run?.violations?.length ? <ViolationList violations={run.violations} /> : null}{run?.diagnostics.length ? <p className="diagnostics">{run.diagnostics.join(" ")}</p> : null}{history.length > 0 && <div className="schedule">{history.slice(-8).map(point => <div className="schedule-row" key={point.generation}><span>Gen {point.generation}</span><span>{point.hard_violations} hard</span><span>{point.soft_penalty.toFixed(2)} soft</span></div>)}</div>}</div>;
}

function ViolationList({ violations }: { violations: Violation[] }) {
  return <div className="violations"><strong>Where conflicts occur</strong>{violations.slice(0, 12).map((violation, index) => <div className="violation-row" key={`${violation.code}-${violation.entity_id ?? ""}-${violation.slot ?? ""}-${index}`}><b>{violation.code}</b><span>{violation.entity_id ?? "—"}{violation.slot ? ` · ${violation.slot}` : ""}</span></div>)}{violations.length > 12 && <small>Showing 12 of {violations.length} violations.</small>}</div>;
}

function sessionPlacement(item: Session, dayItems: Session[]) {
 const duration = item.course?.duration ?? 1;
 const start = item.slot.period;
 const end = start + duration;
 const cluster = dayItems.filter(other => {
   const otherEnd = other.slot.period + (other.course?.duration ?? 1);
   return other.slot.period < end && start < otherEnd;
 });
 const ordered = [...cluster].sort((left, right) => left.slot.period - right.slot.period || left.session_id.localeCompare(right.session_id));
 const lanes: number[] = [];
 const laneById = new Map<string, number>();
 ordered.forEach(session => {
   const sessionStart = session.slot.period;
   const lane = lanes.findIndex(lastEnd => lastEnd <= sessionStart);
   const laneIndex = lane === -1 ? lanes.length : lane;
   lanes[laneIndex] = sessionStart + (session.course?.duration ?? 1);
   laneById.set(session.session_id, laneIndex);
 });
 return { duration, lane: laneById.get(item.session_id) ?? 0, laneCount: Math.max(lanes.length, 1) };
}

function SchedulePanel({ schedule, run, filter, setFilter, panel, setPanel }: { schedule: Session[]; run: Run | null; filter: string; setFilter: (value: string) => void; panel: View; setPanel: (value: View) => void }) {
 const [dayFilter, setDayFilter] = useState("All days");
 const [roomFilter, setRoomFilter] = useState("All rooms");
 const [sectionFilter, setSectionFilter] = useState("All sections");
 const [facultyFilter, setFacultyFilter] = useState("All faculty");
 const days = sortDays([...new Set(schedule.map(item => item.slot.day))]);
 const periods = [...new Set(schedule.map(item => item.slot.period))].sort((a, b) => a - b);
 const rooms = [...new Set(schedule.map(item => item.room.name))];
 const sections = [...new Map(schedule.map(item => [item.section_id, item.section?.name ?? item.section_id] as [string, string])).entries()];
 const faculty = [...new Map(schedule.map(item => [item.faculty_id, item.faculty?.name ?? item.faculty_id] as [string, string])).entries()];
 const courses = [...new Map(schedule.map(item => [item.course_id, item.course ? `${item.course.code} · ${item.course.name}` : item.course_id] as [string, string])).entries()];
 const roomLabels = [...new Map(schedule.map(item => [item.room.id, item.room.name] as [string, string])).entries()];
 const visibleSchedule = schedule.filter(item =>
   (dayFilter === "All days" || item.slot.day === dayFilter) &&
   (roomFilter === "All rooms" || item.room.name === roomFilter) &&
   (sectionFilter === "All sections" || item.section_id === sectionFilter) &&
   (facultyFilter === "All faculty" || item.faculty_id === facultyFilter)
 );
 const clearFilters = () => { setFilter(""); setDayFilter("All days"); setRoomFilter("All rooms"); setSectionFilter("All sections"); setFacultyFilter("All faculty"); };
 const hasFilters = Boolean(filter.trim()) || dayFilter !== "All days" || roomFilter !== "All rooms" || sectionFilter !== "All sections" || facultyFilter !== "All faculty";
 const exportParams = new URLSearchParams();
 if (filter.trim()) exportParams.set("q", filter.trim());
 if (dayFilter !== "All days") exportParams.set("day", dayFilter);
 if (roomFilter !== "All rooms") exportParams.set("room", roomFilter);
 if (sectionFilter !== "All sections") exportParams.set("section", sectionFilter);
 if (facultyFilter !== "All faculty") exportParams.set("faculty", facultyFilter);
 const exportQuery = exportParams.toString();
 const exportHref = run ? `${API}/api/v1/optimization-runs/${run.id}/export.csv${exportQuery ? `?${exportQuery}` : ""}` : "";
 return <div className="panel timetable-panel">
   <div className="panel-head"><div><p className="eyebrow">WEEK VIEW</p><h3>Timetable</h3></div>{schedule.length > 0 && run && <div className="export-actions"><a href={exportHref} title="Download the sessions currently shown, with readable labels">Export {hasFilters ? "filtered " : ""}CSV</a><small>{visibleSchedule.length} session{visibleSchedule.length === 1 ? "" : "s"} · {hasFilters ? "filtered view" : "full timetable"}</small></div>}</div>
   <div className="timetable-toolbar">
     <label className="search-field"><span>Search</span><input id="schedule-filter" placeholder="Course, room, section, faculty..." value={filter} onChange={event => setFilter(event.target.value)} /></label>
     <label><span>Day</span><select value={dayFilter} onChange={event => setDayFilter(event.target.value)}><option>All days</option>{days.map(day => <option key={day}>{day}</option>)}</select></label>
     <label><span>Room</span><select value={roomFilter} onChange={event => setRoomFilter(event.target.value)}><option>All rooms</option>{rooms.map(room => <option key={room}>{room}</option>)}</select></label>
     <label><span>Section</span><select value={sectionFilter} onChange={event => setSectionFilter(event.target.value)}><option value="All sections">All sections</option>{sections.map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select></label>
     <label><span>Faculty</span><select value={facultyFilter} onChange={event => setFacultyFilter(event.target.value)}><option value="All faculty">All faculty</option>{faculty.map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select></label>
     <button className="secondary clear-button" onClick={clearFilters}>Clear</button>
   </div>
   <div className="timetable-legend" aria-label="Timetable labels">
     <strong>Reference labels</strong>
     <div className="label-group"><b>Courses</b>{courses.map(([id, name]) => <span key={id}><code>{id}</code> {name}</span>)}</div>
     <div className="label-group"><b>Faculty</b>{faculty.map(([id, name]) => <span key={id}><code>{id}</code> {name}</span>)}</div>
     <div className="label-group"><b>Rooms</b>{roomLabels.map(([id, name]) => <span key={id}><code>{id}</code> {name}</span>)}</div>
     <div className="label-group"><b>Sections</b>{sections.map(([id, name]) => <span key={id}><code>{id}</code> {name}</span>)}</div>
   </div>
   {schedule.length === 0 ? <p className="empty">Generate a timetable to see scheduled sessions.</p> : visibleSchedule.length === 0 ? <p className="empty">No sessions match these filters.</p> : <div className="timeline-scroll"><div className="timeline-board" style={{ "--period-count": Math.max(periods.length, 1), "--day-count": Math.max(days.length, 1) } as CSSProperties}><div className="timeline-header"><div className="timeline-corner">TIME</div>{days.map(day => <div className="calendar-day" key={day}>{day}</div>)}</div><div className="timeline-body"><div className="timeline-rail">{periods.map(period => <div className="timeline-time" key={period}><span>P{period}</span><small>Period {period}</small><small>{schedule.find(item => item.slot.period === period)?.slot.start_time}</small></div>)}</div>{days.map(day => { const dayItems = visibleSchedule.filter(item => item.slot.day === day); return <div className="timeline-day" key={day}><div className="timeline-track">{dayItems.map(item => { const placement = sessionPlacement(item, dayItems); const timeLabel = `${item.slot.start_time} – ${item.slot.end_time}`;    return <div className="session-card" key={item.session_id} title={timeLabel} aria-label={`${item.course_id}, ${timeLabel}`} tabIndex={0} style={{ "--session-top": (item.slot.period - 1) * 132, "--session-duration": placement.duration, "--session-lane": placement.lane, "--session-lanes": placement.laneCount } as CSSProperties}><strong>{item.course_id}</strong>{item.course && <span className="session-course">{item.course.code}</span>}<span className="session-time">{timeLabel}</span><span><b>{item.room.id}</b></span><small><b>{item.section_id}</b></small><small><b>{item.faculty_id}</b></small></div>; })}</div></div>; })}</div></div></div>}
 </div>;
}

function TimetableSummary({ schedule, run, openTimetable }: { schedule: Session[]; run: Run | null; openTimetable: () => void }) {
 const days = sortDays([...new Set(schedule.map(item => item.slot.day))]);
 const rooms = [...new Set(schedule.map(item => item.room.name))];
 const sections = [...new Set(schedule.map(item => item.section_id))];
 return <div className="panel timetable-summary">
   <div className="panel-head"><div><p className="eyebrow">SCHEDULE SNAPSHOT</p><h3>Timetable overview</h3></div><button className="outline" onClick={openTimetable}>Open timetable →</button></div>
   {run && schedule.length ? <><p className="muted-dark">Your latest generated timetable is ready to explore in the focused calendar view.</p><div className="summary-metrics"><Metric label="Scheduled sessions" value={schedule.length} /><Metric label="Teaching days" value={days.length} /><Metric label="Rooms used" value={rooms.length} /><Metric label="Sections covered" value={sections.length} /></div><div className="summary-meta"><span>Days: {days.join(", ") || "—"}</span><span>Run status: {run.status}</span><span>Hard violations: {run.hard_violations ?? "—"}</span></div></> : <p className="empty">Generate a timetable to see its summary here. The detailed calendar will appear in the Timetable tab.</p>}
 </div>;
}

function AnalyticsPanel({ analytics, history, run }: { analytics: Analytics | null; history: Point[]; run: Run | null }) {
  return <div className="analytics-grid"><div className="panel"><h3>Fitness progression</h3>{history.length ? history.map(point => <div className="bar-row" key={point.generation}><span>G{point.generation}</span><div><i style={{ width: `${Math.min(100, point.hard_violations * 20 + point.soft_penalty)}%` }} /></div><b>{point.hard_violations} / {point.soft_penalty.toFixed(1)}</b></div>) : <p className="empty">Generate a timetable to see metrics.</p>}{run?.violations?.length ? <ViolationList violations={run.violations} /> : null}</div><div className="panel"><h3>Resource distribution</h3>{analytics ? <><Distribution title="By slot" values={analytics.sessions_by_slot} /><Distribution title="By room" values={analytics.sessions_by_room} /><Distribution title="By section" values={analytics.sessions_by_section} /></> : <p className="empty">Run analytics will appear here after generation.</p>}</div></div>;
}

function Distribution({ title, values }: { title: string; values: Record<string, number> }) { return <div className="distribution"><strong>{title}</strong>{Object.keys(values).length ? Object.entries(values).map(([key, value]) => <div key={key}><span>{key}</span><b>{value}</b></div>) : <p className="empty">No sessions</p>}</div>; }
function Metric({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
