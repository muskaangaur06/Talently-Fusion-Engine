import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Circle,
  FileUp,
  Loader2,
  Sparkles,
  Trash2,
  Upload,
  Wand2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useResumes } from "../context/ResumeContext.jsx";
import { DEMO_RESUMES } from "../data/demoResumes.js";
import api from "../services/api.js";

const REASON_ICONS = {
  positive: <CheckCircle2 size={13} className="shrink-0 text-success" />,
  warning: <AlertTriangle size={13} className="shrink-0 text-warning" />,
  neutral: <Circle size={13} className="shrink-0 text-ink-faint" />,
};

function ResumeDropzone({ onUpload, uploading }) {
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files) => {
    if (files && files[0]) onUpload(files[0]);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      className={`flex flex-col items-center justify-center rounded-3xl border-2 border-dashed p-12 text-center transition ${
        dragging ? "border-white bg-white/10" : "border-white/30 bg-white/5"
      }`}
    >
      {uploading ? (
        <Loader2 className="animate-spin text-white" size={30} />
      ) : (
        <>
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15">
            <Upload className="text-white" size={26} />
          </div>
          <p className="mb-4 text-[15px] font-semibold text-white/90">Drag and drop your resume, or</p>
          <label className="cursor-pointer rounded-2xl bg-white px-6 py-3 text-sm font-extrabold text-primary-deep transition hover:-translate-y-0.5">
            Browse files
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </label>
          <p className="mt-4 text-xs font-semibold text-white/60">PDF, DOCX, TXT, or MD</p>
        </>
      )}
    </div>
  );
}

function DemoResumeCards({ onLoad, disabled }) {
  return (
    <div className="mx-auto mt-6 max-w-xl">
      <p className="mb-3 text-xs font-bold uppercase tracking-wide text-white/70">
        Or try a demo resume, no upload needed
      </p>
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
        {DEMO_RESUMES.map((demo) => (
          <button
            key={demo.id}
            onClick={() => onLoad(demo)}
            disabled={disabled}
            className="rounded-xl bg-white/10 px-4 py-3 text-left text-[13px] font-bold text-white transition hover:bg-white/20 disabled:opacity-50"
          >
            {demo.persona}
          </button>
        ))}
      </div>
    </div>
  );
}

function SkillsGapPanel({ skillsGap, loading }) {
  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Loader2 className="animate-spin text-primary" size={24} />
      </div>
    );
  }
  if (!skillsGap) return null;

  const maxDemand = Math.max(...skillsGap.gap.map((g) => g.demand_count), 1);

  return (
    <div className="rounded-2xl bg-card p-6 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
      <h3 className="mb-1.5 text-base font-extrabold text-ink">Your personalized skills gap</h3>
      <p className="mb-4 text-sm font-medium text-ink-soft">
        Based on {skillsGap.matched_jobs} jobs matching your target role. Skills you're missing, ranked by
        how often employers ask for them.
      </p>
      {skillsGap.have.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs font-extrabold uppercase tracking-wide text-success">You already have</p>
          <div className="flex flex-wrap gap-2">
            {skillsGap.have.slice(0, 8).map((h) => (
              <span key={h.skill} className="rounded-lg bg-success-soft px-3 py-1.5 text-sm font-bold text-success">
                {h.skill} &middot; {h.demand_pct}%
              </span>
            ))}
          </div>
        </div>
      )}
      <p className="mb-2 text-xs font-extrabold uppercase tracking-wide text-accent">Worth learning</p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {skillsGap.gap.slice(0, 10).map((g) => {
          const intensity = g.demand_count / maxDemand;
          return (
            <a
              key={g.skill}
              href={g.study_link || undefined}
              target={g.study_link ? "_blank" : undefined}
              rel="noreferrer"
              className={`flex items-center justify-between rounded-xl px-3.5 py-2.5 text-sm ${
                g.study_link ? "cursor-pointer hover:opacity-80" : "cursor-default"
              }`}
              style={{ backgroundColor: `rgba(194, 113, 29, ${0.07 + intensity * 0.18})` }}
            >
              <span className="font-bold text-ink">
                {g.skill}
                {!g.study_link && <span className="ml-1.5 text-[11px] font-semibold text-ink-faint">(no resource yet)</span>}
              </span>
              <span className="font-semibold text-ink-faint">{g.demand_pct}%</span>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function MatchCard({ job }) {
  return (
    <div className="rounded-2xl bg-card p-6 shadow-[0_2px_10px_rgba(35,39,43,0.08)] transition hover:-translate-y-1 hover:shadow-[0_16px_36px_rgba(14,116,102,0.14)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-extrabold text-ink">{job.title}</h3>
          <p className="text-sm font-bold text-ink-soft">
            {job.company_name} &middot; {job.location}
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-gradient-to-br from-primary to-[#14a08d] px-3 py-1.5 text-sm font-extrabold text-white">
          {job.composite_score}%
        </span>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2.5 text-sm">
        <div className="rounded-xl bg-paper p-3 text-center">
          <p className="text-base font-extrabold text-ink">{job.semantic_score}%</p>
          <p className="text-xs font-bold text-ink-faint">Semantic</p>
        </div>
        <div className="rounded-xl bg-paper p-3 text-center">
          <p className="text-base font-extrabold text-ink">{job.skills_score}%</p>
          <p className="text-xs font-bold text-ink-faint">Skills</p>
        </div>
        <div className="rounded-xl bg-paper p-3 text-center">
          <p className="text-base font-extrabold text-ink">{job.experience_score}%</p>
          <p className="text-xs font-bold text-ink-faint">Experience</p>
        </div>
      </div>
      {job.match_explanation?.reasons?.length > 0 && (
        <div className="mt-4 space-y-1.5 border-t border-line-soft pt-4">
          <p className="text-xs font-extrabold uppercase tracking-wide text-ink-faint">Why this match?</p>
          {job.match_explanation.reasons.map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 text-sm font-medium text-ink-soft">
              {REASON_ICONS[r.type]}
              <span>{r.text}</span>
            </div>
          ))}
        </div>
      )}
      <Link
        to={`/jobs/${job.job_id}`}
        className="mt-4 flex items-center justify-between border-t border-line-soft pt-4 text-sm font-bold text-primary hover:text-primary-deep"
      >
        View job & apply
        <ArrowRight size={16} />
      </Link>
    </div>
  );
}

export default function Recommendations() {
  const { resumes, addResume, removeResume, loadDemoResume, activeResumeId, setActiveResumeId, maxResumes } =
    useResumes();
  const [uploading, setUploading] = useState(false);
  const [matches, setMatches] = useState([]);
  const [matching, setMatching] = useState(false);
  const [targetRole, setTargetRole] = useState("");
  const [compareMode, setCompareMode] = useState("recommend");
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [skillsGap, setSkillsGap] = useState(null);
  const [loadingSkillsGap, setLoadingSkillsGap] = useState(false);

  const activeResume = resumes.find((r) => r.id === activeResumeId) || resumes[0] || null;

  const fetchSkillsGap = async (resumeSkills, role) => {
    setLoadingSkillsGap(true);
    try {
      const data = await api.skillsGap({ resume_skills: resumeSkills, target_role: role || null });
      setSkillsGap(data);
    } finally {
      setLoadingSkillsGap(false);
    }
  };

  const runMatchFor = async (resume) => {
    setMatching(true);
    try {
      const matchData = await api.matchJobs({
        resume_text: resume.text,
        resume_skills: resume.skills,
        experience_years: resume.experience_years,
        top_k: 12,
      });
      setMatches(matchData.matches);
      fetchSkillsGap(resume.skills, matchData.matches[0]?.title);
    } finally {
      setMatching(false);
    }
  };

  const handleUpload = async (file) => {
    setUploading(true);
    try {
      const data = await api.uploadResume(file);
      addResume({ text: data.text, skills: data.skills, experience_years: data.experience_years, label: file.name, source: "upload" });
    } finally {
      setUploading(false);
    }
  };

  const handleLoadDemo = (demo) => {
    loadDemoResume({
      text: demo.text,
      skills: demo.skills,
      experience_years: demo.experience_years,
      label: demo.label,
    });
  };

  // Re-run matching whenever the active resume changes, so switching between uploaded/demo
  // resumes updates matches instead of leaving stale results from a previous resume on screen.
  useEffect(() => {
    if (activeResume) runMatchFor(activeResume);
    else {
      setMatches([]);
      setSkillsGap(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeResume?.id]);

  const handleCompare = async () => {
    if (resumes.length < 2) return;
    setComparing(true);
    try {
      const data = await api.compareResumes({
        resumes: resumes.map((r) => ({ text: r.text, skills: r.skills, experience_years: r.experience_years, label: r.label })),
        target_role: targetRole || null,
        mode: compareMode,
      });
      setComparisonResult(data);
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="rounded-[28px] bg-gradient-to-br from-primary via-[#14a08d] to-[#1fbfa8] px-8 py-12 text-center shadow-[0_20px_50px_rgba(14,116,102,0.22)] sm:px-16">
        <h1 className="font-display mb-2 text-[30px] font-extrabold text-white sm:text-[36px]">
          Your resume, actually understood
        </h1>
        <p className="mx-auto mb-8 max-w-lg text-[15.5px] font-medium text-white/85">
          Upload up to 3 versions to get composite-scored job matches and compare them side by side.
        </p>
        <div className="mx-auto max-w-xl">
          <ResumeDropzone onUpload={handleUpload} uploading={uploading} />
        </div>
        <DemoResumeCards onLoad={handleLoadDemo} disabled={uploading} />
      </div>

      {resumes.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-base font-extrabold text-ink">
            Your resumes ({resumes.length}/{maxResumes})
          </h3>
          <div className="flex flex-wrap gap-2.5">
            {resumes.map((r) => (
              <button
                key={r.id}
                onClick={() => setActiveResumeId(r.id)}
                className={`flex items-center gap-2.5 rounded-2xl px-4 py-3 text-sm shadow-[0_2px_10px_rgba(35,39,43,0.08)] transition ${
                  r.id === activeResumeId ? "bg-primary text-white" : "bg-card text-ink hover:bg-line-soft"
                }`}
              >
                <FileUp size={15} className={r.id === activeResumeId ? "text-white" : "text-primary"} />
                <span className="font-bold">{r.label}</span>
                <span className={`text-xs font-semibold ${r.id === activeResumeId ? "text-white/80" : "text-ink-faint"}`}>
                  ({r.skills.length} skills)
                </span>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    e.stopPropagation();
                    removeResume(r.id);
                  }}
                  className={r.id === activeResumeId ? "text-white/80 hover:text-white" : "text-ink-faint hover:text-danger"}
                >
                  <Trash2 size={14} />
                </span>
              </button>
            ))}
          </div>
          <p className="text-xs font-semibold text-ink-faint">
            Click a resume to make it active - matches, skills gap, and interview prep across the site use
            whichever one is active.
          </p>
        </div>
      )}

      {resumes.length >= 2 && (
        <div className="rounded-2xl bg-card p-6 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
          <h3 className="mb-3 text-base font-extrabold text-ink">Compare resumes for a target role</h3>
          <div className="mb-3 flex flex-wrap gap-2.5">
            <input
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Data Scientist (optional)"
              className="flex-1 rounded-xl bg-paper px-3.5 py-2.5 text-[15px] outline-none transition focus:bg-card focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
            />
            <div className="flex rounded-xl bg-paper p-1">
              <button
                onClick={() => setCompareMode("recommend")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-extrabold transition ${
                  compareMode === "recommend" ? "bg-card text-primary shadow-sm" : "text-ink-faint"
                }`}
              >
                Recommend best
              </button>
              <button
                onClick={() => setCompareMode("generate")}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-extrabold transition ${
                  compareMode === "generate" ? "bg-card text-primary shadow-sm" : "text-ink-faint"
                }`}
              >
                Generate best
              </button>
            </div>
            <button
              onClick={handleCompare}
              disabled={comparing}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-5 py-2.5 text-sm font-extrabold text-white transition hover:-translate-y-0.5 disabled:opacity-60"
            >
              {comparing ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              Compare
            </button>
          </div>

          {comparisonResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {comparisonResult.comparison.map((c, i) => (
                  <div key={i} className="rounded-2xl bg-paper p-5">
                    <p className="font-extrabold text-ink">{c.label}</p>
                    <p className="text-3xl font-extrabold text-primary">{c.average_top_match_score}%</p>
                    <p className="text-xs font-semibold text-ink-faint">avg. top-10 match score</p>
                    <p className="mt-1 text-xs font-semibold text-ink-faint">{c.experience_years} yrs experience detected</p>
                  </div>
                ))}
              </div>

              {comparisonResult.recommendation?.recommended_label && (
                <div className="flex items-start gap-3 rounded-2xl bg-success-soft p-5">
                  <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-success" />
                  <div>
                    <p className="font-extrabold text-success">
                      Recommended: {comparisonResult.recommendation.recommended_label}
                    </p>
                    <p className="text-sm font-medium text-ink-soft">{comparisonResult.recommendation.reason}</p>
                  </div>
                </div>
              )}

              {comparisonResult.recommendation?.merged_text && (
                <div className="rounded-2xl bg-night p-6">
                  <div className="mb-3 flex items-center gap-2">
                    <Wand2 size={16} className="text-[#7fd9c4]" />
                    <p className="text-xs font-extrabold uppercase tracking-wide text-[#7fd9c4]">
                      Best-of-3 merged resume ({comparisonResult.recommendation.source})
                    </p>
                  </div>
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed text-paper">
                    {comparisonResult.recommendation.merged_text}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {matching && (
        <div className="flex justify-center py-8">
          <Loader2 className="animate-spin text-primary" size={28} />
        </div>
      )}

      {(skillsGap || loadingSkillsGap) && <SkillsGapPanel skillsGap={skillsGap} loading={loadingSkillsGap} />}

      {matches.length > 0 && (
        <div>
          <h3 className="mb-4 text-lg font-extrabold text-ink">
            Top matches for {activeResume ? `"${activeResume.label}"` : "your resume"}
          </h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {matches.map((job) => (
              <MatchCard key={job.job_id} job={job} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
