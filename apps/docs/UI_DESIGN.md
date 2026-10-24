# UI Design Specification

## Direction
Modern, professional academic dashboard. Prioritize clarity and data density over decorative effects.

## Design system
The current MVP uses semantic React controls and a restrained neutral/light visual system.
Use accessible labels, visible focus rings, compact cards, and restrained accent color.
Avoid excessive gradients and glass effects.

## Screens
### Dashboard
The overview uses a Smart Scheduling hero, configured counts for sections, faculty, rooms,
and teaching requirements, plus actions for validation and timetable generation. It also
shows the latest run and a timetable snapshot.

### Setup
Guided record additions for courses, faculty, sections, rooms, time slots, and teaching
requirements plus a complete JSON editor for advanced changes. Entity-specific constraint
fields are available in the guided form: faculty can define unavailable/preferred slots and
daily load limits; rooms and sections can define unavailable slots; courses can define
duration and consecutive-slot requirements; and teaching requirements can override duration
and room type. Slot lists use comma-separated time-slot IDs. API errors are shown next to
the action and empty data is explicit.

### Timetable
Custom React grid. Display days and periods; each session shows course, faculty abbreviation, and room. Filters by section/faculty/room/day. Session times are fully visible on hover and keyboard focus. Make conflicts clear without relying on color alone.

### Optimization
Controls for GA parameters; validate-before-run; run status, generation, runtime, hard
violations, soft penalty, and diagnostics. Technical GA terminology remains in advanced
controls and analytics, while the primary overview uses plain-language feedback copy.

### Analytics
Custom API-backed bars for fitness by generation and resource distributions by slot, room,
and section. Use actual API data and explicit empty states; richer chart libraries remain optional.

### Export
CSV export for the selected run with clear status feedback.

## Motion
Use only subtle CSS card/panel transitions or progress effects. Respect `prefers-reduced-motion`;
never make animation necessary to access content.

## Accessibility
Keyboard-operable controls, visible focus, labels, sufficient contrast, descriptive errors, responsive layout, and reduced-motion support.

## Suggested components
`AppSidebar`, `Topbar`, `StatCard`, `ConstraintSummary`, `DataTable`, `EntityFormDialog`, `TimetableGrid`, `TimetableCell`, `SessionDetailsSheet`, `OptimizationConfigForm`, `RunProgressPanel`, `FitnessLineChart`, `WorkloadBarChart`, `ConstraintPieChart`, `ExportMenu`, `EmptyState`, `ErrorState`.

Every API-driven screen should handle loading, empty, success, validation-error, server-error, and stale-data states. Do not show fabricated chart data.
