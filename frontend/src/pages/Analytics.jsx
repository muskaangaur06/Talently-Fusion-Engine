import { CheckCircle2, Loader2, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useResumes } from "../context/ResumeContext.jsx";
import api from "../services/api.js";

const COLORS = ["#0e7466", "#1fbfa8", "#0a574d", "#5b6370", "#8b93a1"];
const UNKNOWN_COLOR = "#a8e0d4";

function sourceColor(source, fallbackIndex) {
  if (source?.toLowerCase() === "unknown") return UNKNOWN_COLOR;
  return COLORS[fallbackIndex % COLORS.length];
}

function MetricCard({ label, value, hint, dark }) {
  return (
    <div className={`rounded-2xl p-4 shadow-[0_2px_10px_rgba(35,39,43,0.08)] ${dark ? "bg-night" : "bg-card"}`}>
      <p className={`text-[11px] font-extrabold uppercase tracking-wide ${dark ? "text-[#7fd9c4]" : "text-ink-faint"}`}>
        {label}
      </p>
      <p className={`mt-1 text-2xl font-extrabold ${dark ? "text-white" : "text-success"}`}>{value}</p>
      {hint && <p className={`text-xs font-semibold ${dark ? "text-white/60" : "text-ink-faint"}`}>{hint}</p>}
    </div>
  );
}

function PersonalizedAnalyticsSection({ resume }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .personalizedAnalytics({
        resume_text: resume.text,
        resume_skills: resume.skills,
        experience_years: resume.experience_years,
      })
      .then(setData)
      .finally(() => setLoading(false));
  }, [resume.id]);

  if (loading) {
    return (
      <div className="flex justify-center rounded-2xl bg-card py-10 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
        <Loader2 className="animate-spin text-primary" size={26} />
      </div>
    );
  }
  if (!data || data.matched_count === 0) return null;

  return (
    <div className="rounded-[28px] bg-gradient-to-br from-primary via-[#14a08d] to-[#1fbfa8] p-7 shadow-[0_20px_50px_rgba(14,116,102,0.22)]">
      <div className="mb-5 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
          <UserRound size={18} className="text-white" />
        </div>
        <div>
          <h2 className="font-display text-lg font-extrabold text-white">Personalized for "{resume.label}"</h2>
          <p className="text-xs font-semibold text-white/75">
            Based on {data.matched_count.toLocaleString()} matched roles, avg. score {data.average_match_score}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <MetricCard label="Matched roles" value={data.matched_count.toLocaleString()} hint="score 40%+" dark />
        <MetricCard
          label="Median salary"
          value={data.salary_percentiles.p50 ? `Rs ${data.salary_percentiles.p50}L` : "N/A"}
          hint="for matched roles"
          dark
        />
        <MetricCard label="Top company" value={data.top_companies[0]?.company_name ?? "N/A"} hint={`${data.top_companies[0]?.count ?? 0} roles`} dark />
        <MetricCard label="Top location" value={data.top_locations[0]?.location ?? "N/A"} hint={`${data.top_locations[0]?.count ?? 0} roles`} dark />
      </div>

      {data.top_companies.length > 0 && (
        <div className="mt-5 rounded-2xl bg-white/10 p-5">
          <p className="mb-3 text-xs font-extrabold uppercase tracking-wide text-white/70">Top hiring companies for you</p>
          <div className="flex flex-wrap gap-2">
            {data.top_companies.slice(0, 8).map((c) => (
              <span key={c.company_name} className="rounded-full bg-white/15 px-3 py-1.5 text-xs font-bold text-white">
                {c.company_name} &middot; {c.count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Analytics() {
  const { activeResume } = useResumes();
  const [data, setData] = useState(null);
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    api.getAnalytics().then(setData);
    api.getEvaluation().then(setEvaluation);
  }, []);

  if (!data) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  const maxSkillCount = Math.max(...data.top_skills.map((s) => s.count), 1);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-extrabold text-ink">Job Market Intelligence</h1>
        <p className="text-[15px] font-medium text-ink-soft">
          Live aggregates over the deduplicated jobs index, the skills-gap heatmap, and the retrieval evaluation
          matrix.
        </p>
      </div>

      {activeResume ? (
        <PersonalizedAnalyticsSection resume={activeResume} />
      ) : (
        <div className="flex items-center gap-3 rounded-2xl bg-primary-faint px-5 py-4 text-sm font-semibold text-primary-deep">
          <Sparkles size={16} />
          Select a resume on Matched Profiles to see market analytics personalized to your profile.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <MetricCard label="Roles ingested" value={data.total_jobs.toLocaleString()} hint="after 3-level dedup" />
        <MetricCard label="Median salary" value={data.salary_percentiles.p50 ? `Rs ${data.salary_percentiles.p50}L` : "N/A"} hint="across disclosed bands" />
        <MetricCard label="P90 salary" value={data.salary_percentiles.p90 ? `Rs ${data.salary_percentiles.p90}L` : "N/A"} hint="90th percentile band" />
        <MetricCard label="Top location" value={data.top_locations[0]?.location ?? "N/A"} hint={`${data.top_locations[0]?.count ?? 0} roles`} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-line bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-soft">Postings by source</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={data.sources} dataKey="count" nameKey="source" innerRadius={55} outerRadius={90} paddingAngle={2}>
                {data.sources.map((s, i) => (
                  <Cell key={i} fill={sourceColor(s.source, i)} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            {data.sources.map((s, i) => (
              <span key={s.source} className="flex items-center gap-1.5 text-xs text-ink-soft">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: sourceColor(s.source, i) }} />
                {s.source} ({s.count.toLocaleString()})
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-soft">Top hiring locations</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.top_locations.slice(0, 6)}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="location" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={50} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl border border-line bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-soft">Experience distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.experience_distribution} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="bucket" width={110} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#1fbfa8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl border border-line bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-soft">Top domains</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.top_domains} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="domain" width={110} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#0a574d" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-line bg-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-ink-soft">Role-skills match gap heatmap</h3>
          <span className="text-xs text-ink-faint">Click a skill for a learning resource</span>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-5">
          {data.top_skills.map((s) => {
            const intensity = s.count / maxSkillCount;
            const bg = `rgba(15, 118, 110, ${0.12 + intensity * 0.7})`;
            const link = s.study_link;
            const content = (
              <div
                style={{ backgroundColor: bg }}
                className="flex h-20 flex-col items-center justify-center rounded-lg p-2 text-center transition hover:scale-105"
              >
                <p className={`text-xs font-semibold ${intensity > 0.5 ? "text-white" : "text-ink"}`}>{s.skill}</p>
                <p className={`text-xs ${intensity > 0.5 ? "text-success-soft" : "text-ink-faint"}`}>{s.count} jobs</p>
              </div>
            );
            return link ? (
              <a key={s.skill} href={link} target="_blank" rel="noreferrer">
                {content}
              </a>
            ) : (
              <div key={s.skill}>{content}</div>
            );
          })}
        </div>
      </div>

      {evaluation && (
        <div className="rounded-2xl border border-line bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-soft">Retrieval evaluation matrix</h3>
          <div className="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-line p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">Mean NDCG@10</p>
              <p className="text-2xl font-bold text-success">{evaluation.ndcg_at_10}</p>
            </div>
            <div className="rounded-lg border border-line p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">Mean Reciprocal Rank</p>
              <p className="text-2xl font-bold text-success">{evaluation.mrr}</p>
            </div>
            <div className="rounded-lg border border-line p-3">
              <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                <ShieldCheck size={12} /> RAG Faithfulness Audit
              </p>
              <p className="flex items-center gap-1.5 text-2xl font-bold text-success">
                {evaluation.faithfulness_audit.passed && <CheckCircle2 size={18} />}
                {evaluation.faithfulness_audit.passed ? "PASS" : "FAIL"}
              </p>
              <p className="text-xs text-ink-faint">{evaluation.faithfulness_audit.detail}</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-ink-faint">
                  <th className="py-1.5 pr-4">Probe query</th>
                  <th className="py-1.5 pr-4">NDCG@10</th>
                  <th className="py-1.5 pr-4">Reciprocal rank</th>
                  <th className="py-1.5">Results found</th>
                </tr>
              </thead>
              <tbody>
                {evaluation.per_query.map((q) => (
                  <tr key={q.query} className="border-b border-line-soft">
                    <td className="py-1.5 pr-4">{q.query}</td>
                    <td className="py-1.5 pr-4">{q.ndcg}</td>
                    <td className="py-1.5 pr-4">{q.mrr}</td>
                    <td className="py-1.5">{q.results_found}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
