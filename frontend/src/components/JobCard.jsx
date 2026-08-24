import { ArrowRight, Banknote, Clock3, MapPin } from "lucide-react";
import { Link } from "react-router-dom";

const SOURCE_STYLES = {
  LinkedIn: { chip: "bg-primary-soft text-primary-deep", bar: "bg-primary" },
  Naukri: { chip: "bg-accent-soft text-accent", bar: "bg-accent" },
  Indeed: { chip: "bg-warning-soft text-warning", bar: "bg-warning" },
  Internshala: { chip: "bg-success-soft text-success", bar: "bg-success" },
};
const DEFAULT_SOURCE_STYLE = { chip: "bg-line-soft text-ink-soft", bar: "bg-ink-faint" };

function relativeTime(isoString) {
  if (!isoString) return "recently";
  const posted = new Date(isoString).getTime();
  if (Number.isNaN(posted)) return "recently";
  const days = Math.max(0, Math.floor((Date.now() - posted) / 86400000));
  if (days === 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

function companyInitials(name) {
  if (!name) return "?";
  const words = name.trim().split(/\s+/).slice(0, 2);
  return words.map((w) => w[0]?.toUpperCase()).join("");
}

export default function JobCard({ job }) {
  const salaryText =
    job.salary_min && job.salary_max ? `Rs ${job.salary_min}-${job.salary_max} LPA` : null;
  const sourceStyle = SOURCE_STYLES[job.source] || DEFAULT_SOURCE_STYLE;

  return (
    <Link
      to={`/jobs/${job.job_id}`}
      className="group relative flex flex-col overflow-hidden rounded-[22px] bg-card shadow-[0_2px_10px_rgba(35,39,43,0.09)] transition-all duration-200 hover:-translate-y-1.5 hover:shadow-[0_20px_44px_rgba(14,116,102,0.20)]"
    >
      <span className={`absolute inset-x-0 top-0 h-1.5 ${sourceStyle.bar}`} />

      <div className="flex flex-1 flex-col p-6 pt-7">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-[#14a08d] text-[13px] font-extrabold text-white shadow-[0_4px_12px_rgba(14,116,102,0.25)]">
              {companyInitials(job.company_name)}
            </div>
            <div className="min-w-0">
              <h3 className="font-display truncate text-[18px] font-extrabold leading-snug text-ink transition-colors group-hover:text-primary">
                {job.title}
              </h3>
              <p className="truncate text-sm font-bold text-ink-soft">{job.company_name}</p>
            </div>
          </div>
          <span className={`shrink-0 rounded-full px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide ${sourceStyle.chip}`}>
            {job.source}
          </span>
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-semibold text-ink-soft">
          <span className="flex items-center gap-1.5">
            <MapPin size={14} className="text-primary" /> {job.location}
          </span>
          <span className="flex items-center gap-1.5">
            <Clock3 size={14} className="text-primary" /> {relativeTime(job.posted_at)}
          </span>
          {job.experience_min !== null && job.experience_min !== undefined && (
            <span>
              {job.experience_min}-{job.experience_max ?? "n/a"} yrs
            </span>
          )}
          {salaryText && (
            <span className="flex items-center gap-1.5 font-extrabold text-success">
              <Banknote size={14} /> {salaryText}
            </span>
          )}
        </div>

        {job.skills?.length > 0 && (
          <div className="mb-5 flex flex-wrap gap-2">
            {job.skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="rounded-lg bg-primary-faint px-3 py-1.5 text-[13px] font-bold text-primary-deep"
              >
                {skill}
              </span>
            ))}
            {job.skills.length > 4 && (
              <span className="rounded-lg px-3 py-1.5 text-[13px] font-bold text-ink-faint">
                +{job.skills.length - 4} more
              </span>
            )}
          </div>
        )}

        <div className="mt-auto flex items-center justify-between border-t border-line-soft pt-4">
          <span className="text-sm font-bold text-ink-faint">View full details</span>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-faint text-primary transition-all group-hover:bg-primary group-hover:text-white">
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
          </span>
        </div>
      </div>
    </Link>
  );
}
