import { describe, expect, it } from "vitest";
import { filterSchedule } from "../app/schedule";

describe("filterSchedule", () => {
  const items = [
    { session_id: "tr1:1", slot_id: "mon-1", room_id: "r1", section_id: "s1", faculty_id: "f1" },
    { session_id: "tr1:2", slot_id: "tue-1", room_id: "r2", section_id: "s2", faculty_id: "f2" },
  ];

  it("matches every visible schedule field", () => {
    expect(filterSchedule(items, "TUE")).toEqual([items[1]]);
    expect(filterSchedule(items, "s1")).toEqual([items[0]]);
  });

  it("returns all items for an empty query", () => {
    expect(filterSchedule(items, " ")).toEqual(items);
  });

  it("handles non-string schedule values", () => {
    const nested = [{ ...items[0], slot: { day: "Monday", period: 1 } }];
    expect(filterSchedule(nested, "monday")).toEqual(nested);
  });
});
