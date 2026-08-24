import { RotateCcw } from "lucide-react";

const SOURCES = ["LinkedIn", "Naukri", "Indeed", "Internshala"];

const AGE_OPTIONS = [
  { label: "Any time", value: "" },
  { label: "Today", value: "1" },
  { label: "Last 3 days", value: "3" },
  { label: "Last week", value: "7" },
  { label: "Last month", value: "30" },
  { label: "Last 3 months", value: "90" },
  { label: "Last 6 months", value: "180" },
];

const EMPTY_FILTERS = { location: null, source: null, min_experience: null, max_experience: null, max_age_days: null };

export default function FilterPanel({ filters, onChange, lastQueryUsedVector }) {
  const update = (key, value) => onChange({ ...filters, [key]: value });
  const hasActiveFilters = Object.values(filters).some((v) => v !== null && v !== "");

  return (
    <div className="rounded-2xl bg-card p-6 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-extrabold text-ink">Filter Controls</h3>
        {hasActiveFilters && (
          <button
            onClick={() => onChange(EMPTY_FILTERS)}
            className="flex items-center gap-1.5 text-sm font-bold text-ink-faint hover:text-primary"
          >
            <RotateCcw size={13} /> Reset
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            Source Portal
          </label>
          <select
            value={filters.source || ""}
            onChange={(e) => update("source", e.target.value || null)}
            className="w-full rounded-xl border-[1.5px] border-line-soft bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          >
            <option value="">All portals</option>
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            Location Target
          </label>
          <input
            value={filters.location || ""}
            onChange={(e) => update("location", e.target.value)}
            placeholder="e.g. Pune, Remote..."
            className="w-full rounded-xl border-[1.5px] border-line-soft bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            Min experience (years)
          </label>
          <input
            type="number"
            min="0"
            value={filters.min_experience ?? ""}
            onChange={(e) => update("min_experience", e.target.value ? Number(e.target.value) : null)}
            placeholder="Any"
            className="w-full rounded-xl border-[1.5px] border-line-soft bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            Max experience (years)
          </label>
          <input
            type="number"
            min="0"
            value={filters.max_experience ?? ""}
            onChange={(e) => update("max_experience", e.target.value ? Number(e.target.value) : null)}
            placeholder="Any"
            className="w-full rounded-xl border-[1.5px] border-line-soft bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            Job age
          </label>
          <select
            value={filters.max_age_days ?? ""}
            onChange={(e) => update("max_age_days", e.target.value ? Number(e.target.value) : null)}
            className="w-full rounded-xl border-[1.5px] border-line-soft bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          >
            {AGE_OPTIONS.map((opt) => (
              <option key={opt.label} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-5 border-t border-line-soft pt-4">
        <p className="text-sm font-extrabold text-ink-soft">Retrieval engine</p>
        <p className="text-sm text-ink-faint">
          Keyword and vector results are merged with{" "}
          <span className="font-bold text-primary">Reciprocal Rank Fusion</span>
          {" - "}
          {lastQueryUsedVector ? "last query ran on the hybrid path." : "showing the structured filter path."}
        </p>
      </div>
    </div>
  );
}
