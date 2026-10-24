export type ScheduleItem = {
  session_id: string;
  slot_id: string;
  room_id: string;
  section_id: string;
  faculty_id: string;
};

export function filterSchedule<T extends ScheduleItem>(items: T[], query: string): T[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return items;
  return items.filter(item => Object.values(item).some(value => (typeof value === "object" ? JSON.stringify(value) : String(value)).toLowerCase().includes(normalized)));
}
