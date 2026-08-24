import {
  AlertTriangle,
  Bookmark,
  BookmarkCheck,
  Briefcase,
  CheckCircle2,
  Circle,
  Copy,
  ExternalLink,
  FileText,
  Loader2,
  MapPin,
  MessageSquare,
  Sparkles,
  Wand2,
} from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useParams } from "react-router-dom";
import ChatAssistant from "../components/ChatAssistant.jsx";
import JobCard from "../components/JobCard.jsx";
import { useApplications } from "../context/ApplicationsContext.jsx";
import { useResumes } from "../context/ResumeContext.jsx";
import api from "../services/api.js";

const REASON_ICONS = {
  positive: <CheckCircle2 size={14} className="shrink-0 text-success" />,
  warning: <AlertTriangle size={14} className="shrink-0 text-warning" />,
  neutral: <Circle size={14} className="shrink-0 text-ink-faint" />,
};

const TABS = [
  { key: "description", label: "Description" },
  { key: "fit", label: "Fit & Score" },
  { key: "cover-letter", label: "Cover Letter" },
  { key: "prep", label: "Interview Prep" },
];

function NoResumeNotice() {
  return (
    <div className="rounded-xl bg-warning-soft p-4 text-sm font-semibold text-warning">
      Select or upload a resume on the{" "}
      <a href="/recommendations" className="underline">
        Matched Profiles
      </a>{" "}
      page first, so this tab can be tailored to you.
    </div>
  );
}

export default function JobDetails() {
  const { jobId } = useParams();
  const { activeResume, resumes } = useResumes();
  const { addApplication, isTracked } = useApplications();
  const [job, setJob] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [activeTab, setActiveTab] = useState("description");

  const [interviewPrep, setInterviewPrep] = useState(null);
  const [loadingPrep, setLoadingPrep] = useState(false);

  const [fit, setFit] = useState(null);
  const [loadingFit, setLoadingFit] = useState(false);

  const [boostResult, setBoostResult] = useState(null);
  const [boosting, setBoosting] = useState(false);

  const [bestResumeMode, setBestResumeMode] = useState("recommend");
  const [bestResumeResult, setBestResumeResult] = useState(null);
  const [findingBestResume, setFindingBestResume] = useState(false);

  const [coverLetter, setCoverLetter] = useState(null);
  const [generatingLetter, setGeneratingLetter] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getJob(jobId).then(setJob);
    api.getSimilarJobs(jobId).then((data) => setSimilar(data.jobs || []));
    // Reset per-job AI results when navigating between jobs so stale data from the
    // previous job never lingers on screen.
    setFit(null);
    setBoostResult(null);
    setCoverLetter(null);
    setInterviewPrep(null);
    setBestResumeResult(null);
  }, [jobId]);

  const resumePayload = () =>
    activeResume
      ? {
          resume_text: activeResume.text,
          resume_skills: activeResume.skills,
          experience_years: activeResume.experience_years,
        }
      : null;

  const handleLoadFit = async () => {
    if (!activeResume) return;
    setLoadingFit(true);
    try {
      const data = await api.fitScore({ ...resumePayload(), job_id: jobId });
      setFit(data);
    } finally {
      setLoadingFit(false);
    }
  };

  const handleGeneratePrep = async () => {
    setLoadingPrep(true);
    try {
      const data = await api.interviewPrep(jobId, activeResume?.skills || []);
      setInterviewPrep(data);
    } finally {
      setLoadingPrep(false);
    }
  };

  const handleBoost = async () => {
    if (!activeResume) return;
    setBoosting(true);
    try {
      const data = await api.boostResume({ ...resumePayload(), job_id: jobId });
      setBoostResult(data);
    } finally {
      setBoosting(false);
    }
  };

  const handleFindBestResume = async () => {
    if (resumes.length < 2) return;
    setFindingBestResume(true);
    try {
      const data = await api.compareResumes({
        resumes: resumes.map((r) => ({ text: r.text, skills: r.skills, experience_years: r.experience_years, label: r.label })),
        job_id: jobId,
        mode: bestResumeMode,
      });
      setBestResumeResult(data);
    } finally {
      setFindingBestResume(false);
    }
  };

  const handleGenerateCoverLetter = async () => {
    if (!activeResume) return;
    setGeneratingLetter(true);
    setCopied(false);
    try {
      const data = await api.coverLetter({ ...resumePayload(), job_id: jobId });
      setCoverLetter(data);
    } finally {
      setGeneratingLetter(false);
    }
  };

  const handleCopyLetter = async () => {
    if (!coverLetter?.letter) return;
    try {
      await navigator.clipboard.writeText(coverLetter.letter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard access denied, ignore
    }
  };

  const handleTrack = (status) => {
    if (!job) return;
    addApplication(job, status);
  };

  if (!job) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  const tracked = isTracked(job.job_id);

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <div className="rounded-2xl bg-card p-6 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="font-display text-xl font-extrabold text-ink">{job.title}</h1>
              <p className="font-bold text-ink-soft">{job.company_name}</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                onClick={() => handleTrack(tracked ? "Applied" : "Saved")}
                className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-bold transition ${
                  tracked ? "bg-success-soft text-success" : "bg-line-soft text-ink-soft hover:bg-line"
                }`}
              >
                {tracked ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
                {tracked ? "Saved" : "Save"}
              </button>
              {job.apply_link && (
                <a
                  href={job.apply_link}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => handleTrack("Applied")}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-4 py-2 text-sm font-bold text-white transition hover:-translate-y-0.5"
                >
                  Apply <ExternalLink size={14} />
                </a>
              )}
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-3 text-sm font-semibold text-ink-soft">
            <span className="flex items-center gap-1">
              <MapPin size={14} /> {job.location}
            </span>
            {job.experience_min !== null && (
              <span className="flex items-center gap-1">
                <Briefcase size={14} /> {job.experience_min}-{job.experience_max ?? "?"} yrs
              </span>
            )}
            <span className="rounded-full bg-paper px-2.5 py-1 text-xs font-extrabold">{job.source}</span>
          </div>

          {job.skills?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {job.skills.map((skill) => (
                <span key={skill} className="rounded-lg bg-primary-faint px-2.5 py-1 text-xs font-bold text-primary-deep">
                  {skill}
                </span>
              ))}
            </div>
          )}

          <div className="mt-5 flex gap-1 overflow-x-auto border-b border-line-soft">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`shrink-0 whitespace-nowrap px-3.5 py-2.5 text-sm font-bold transition ${
                  activeTab === tab.key ? "border-b-2 border-primary text-primary-deep" : "text-ink-faint hover:text-ink"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === "description" && (
            <div className="prose prose-sm mt-4 max-w-none text-ink-soft">
              <ReactMarkdown>{job.formatted_description || job.description}</ReactMarkdown>
            </div>
          )}

          {activeTab === "fit" && (
            <div className="mt-4 space-y-4">
              {!activeResume ? (
                <NoResumeNotice />
              ) : !fit ? (
                <button
                  onClick={handleLoadFit}
                  disabled={loadingFit}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-4 py-2.5 text-sm font-bold text-white transition hover:-translate-y-0.5 disabled:opacity-60"
                >
                  {loadingFit ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                  See why you're a fit
                </button>
              ) : (
                <>
                  <div className="flex items-center gap-4 rounded-2xl bg-paper p-5">
                    <span className="text-4xl font-extrabold text-primary">{fit.composite_score}%</span>
                    <div className="grid flex-1 grid-cols-3 gap-2 text-center text-xs font-bold text-ink-faint">
                      <div>
                        <p className="text-base font-extrabold text-ink">{fit.semantic_score}%</p>
                        Semantic
                      </div>
                      <div>
                        <p className="text-base font-extrabold text-ink">{fit.skills_score}%</p>
                        Skills
                      </div>
                      <div>
                        <p className="text-base font-extrabold text-ink">{fit.experience_score}%</p>
                        Experience
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {fit.match_explanation.reasons.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm font-medium text-ink-soft">
                        {REASON_ICONS[r.type]}
                        <span>{r.text}</span>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-2xl bg-card p-5 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-sm font-extrabold text-ink">Boost how you present your experience</h3>
                      <button
                        onClick={handleBoost}
                        disabled={boosting}
                        className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-white transition hover:opacity-90 disabled:opacity-50"
                      >
                        {boosting ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                        Boost resume
                      </button>
                    </div>
                    <p className="mb-3 text-xs font-medium text-ink-faint">
                      Rewrites weak or generic lines using only what's already in your resume, no invented skills,
                      then recomputes your match score.
                    </p>

                    {boostResult && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 rounded-xl bg-paper px-3.5 py-2.5 text-sm font-bold">
                          <span className="text-ink-faint">{boostResult.original_score}%</span>
                          <span className="text-ink-faint">&rarr;</span>
                          <span className="text-primary-deep">{boostResult.boosted_score}%</span>
                          <span className={boostResult.boost_delta >= 0 ? "text-success" : "text-danger"}>
                            ({boostResult.boost_delta >= 0 ? "+" : ""}
                            {boostResult.boost_delta} pts)
                          </span>
                        </div>

                        {boostResult.rewrites.length === 0 ? (
                          <p className="text-sm font-medium text-ink-faint">
                            No presentation improvements found - your resume already reads clearly for this role.
                          </p>
                        ) : (
                          <div className="space-y-3">
                            {boostResult.rewrites.map((r, i) => (
                              <div key={i} className="rounded-xl bg-paper p-3.5 text-sm">
                                <p className="mb-1">
                                  <span className="rounded bg-danger-soft px-1.5 py-0.5 text-danger line-through decoration-danger/60">
                                    {r.original_line}
                                  </span>
                                </p>
                                <p>
                                  <span className="rounded bg-success-soft px-1.5 py-0.5 text-success">
                                    {r.rewritten_line}
                                  </span>
                                </p>
                                {r.reason && <p className="mt-1.5 text-xs font-medium text-ink-faint">{r.reason}</p>}
                                {r.targets_skill && (
                                  <p className="mt-1 text-xs font-bold text-primary-deep">Targets: {r.targets_skill}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {resumes.length >= 2 && (
                    <div className="rounded-2xl bg-card p-5 shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
                      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-sm font-extrabold text-ink">Best resume for this job</h3>
                        <div className="flex items-center gap-2">
                          <div className="flex rounded-lg bg-paper p-1">
                            <button
                              onClick={() => setBestResumeMode("recommend")}
                              className={`rounded-md px-2.5 py-1 text-xs font-extrabold transition ${
                                bestResumeMode === "recommend" ? "bg-card text-primary shadow-sm" : "text-ink-faint"
                              }`}
                            >
                              Recommend best
                            </button>
                            <button
                              onClick={() => setBestResumeMode("generate")}
                              className={`rounded-md px-2.5 py-1 text-xs font-extrabold transition ${
                                bestResumeMode === "generate" ? "bg-card text-primary shadow-sm" : "text-ink-faint"
                              }`}
                            >
                              Generate with AI
                            </button>
                          </div>
                          <button
                            onClick={handleFindBestResume}
                            disabled={findingBestResume}
                            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-white transition hover:opacity-90 disabled:opacity-50"
                          >
                            {findingBestResume ? <Loader2 size={13} className="animate-spin" /> : <Wand2 size={13} />}
                            Check
                          </button>
                        </div>
                      </div>
                      <p className="mb-3 text-xs font-medium text-ink-faint">
                        Compares all {resumes.length} of your resumes against this specific job and either
                        recommends the strongest one or generates a merged best version with AI.
                      </p>

                      {bestResumeResult?.recommendation?.recommended_label && (
                        <div className="flex items-start gap-3 rounded-xl bg-success-soft p-4">
                          <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-success" />
                          <div>
                            <p className="text-sm font-extrabold text-success">
                              Use: {bestResumeResult.recommendation.recommended_label}
                            </p>
                            <p className="text-xs font-medium text-ink-soft">{bestResumeResult.recommendation.reason}</p>
                          </div>
                        </div>
                      )}

                      {bestResumeResult?.recommendation?.merged_text && (
                        <div className="rounded-xl bg-night p-4">
                          <div className="mb-2 flex items-center gap-2">
                            <Wand2 size={14} className="text-[#7fd9c4]" />
                            <p className="text-xs font-extrabold uppercase tracking-wide text-[#7fd9c4]">
                              Merged resume ({bestResumeResult.recommendation.source})
                            </p>
                          </div>
                          <pre className="max-h-72 overflow-y-auto whitespace-pre-wrap text-xs leading-relaxed text-paper">
                            {bestResumeResult.recommendation.merged_text}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === "cover-letter" && (
            <div className="mt-4 space-y-3">
              {!activeResume ? (
                <NoResumeNotice />
              ) : (
                <>
                  <button
                    onClick={handleGenerateCoverLetter}
                    disabled={generatingLetter}
                    className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-4 py-2.5 text-sm font-bold text-white transition hover:-translate-y-0.5 disabled:opacity-60"
                  >
                    {generatingLetter ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
                    Generate cover letter
                  </button>
                  <p className="text-xs font-medium text-ink-faint">
                    Written from your resume and this job's matched skills, no invented employers, projects, or
                    numbers.
                  </p>

                  {coverLetter && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-bold text-ink-soft">
                          {coverLetter.job_title} at {coverLetter.company_name}
                        </p>
                        <button
                          onClick={handleCopyLetter}
                          className="flex items-center gap-1 text-xs font-bold text-primary hover:text-primary-deep"
                        >
                          <Copy size={12} /> {copied ? "Copied" : "Copy"}
                        </button>
                      </div>
                      <pre className="whitespace-pre-wrap rounded-xl bg-paper p-4 text-sm leading-relaxed text-ink">
                        {coverLetter.letter}
                      </pre>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === "prep" && (
            <div className="mt-4">
              {!interviewPrep ? (
                <button
                  onClick={handleGeneratePrep}
                  disabled={loadingPrep}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-4 py-2.5 text-sm font-bold text-white transition hover:-translate-y-0.5 disabled:opacity-60"
                >
                  {loadingPrep ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                  Generate interview prep
                </button>
              ) : (
                <div className="space-y-4 text-sm">
                  {!activeResume && (
                    <p className="rounded-xl bg-warning-soft p-3 text-xs font-semibold text-warning">
                      Select a resume on Matched Profiles for prep tailored to your actual skill gaps.
                    </p>
                  )}
                  <div>
                    <h4 className="mb-1.5 font-extrabold text-ink">Technical questions</h4>
                    <ul className="space-y-2 pl-5 text-ink-soft">
                      {interviewPrep.technical_questions.map((q, i) => (
                        <li key={i} className="list-disc">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">{q.question}</span>
                            {q.targets_skill && (
                              <span className="rounded bg-primary-faint px-1.5 py-0.5 text-xs font-bold text-primary-deep">
                                {q.targets_skill}
                              </span>
                            )}
                          </div>
                          {q.study_link && (
                            <a
                              href={q.study_link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-bold text-primary underline hover:text-primary-deep"
                            >
                              Study material for {q.targets_skill}
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="mb-1.5 font-extrabold text-ink">Behavioral questions</h4>
                    <ul className="list-disc space-y-1 pl-5 font-medium text-ink-soft">
                      {interviewPrep.behavioral_questions.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="mb-1.5 font-extrabold text-ink">Preparation tips</h4>
                    <ul className="list-disc space-y-1 pl-5 font-medium text-ink-soft">
                      {interviewPrep.preparation_tips.map((t, i) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </div>
                  <p className="text-xs font-semibold text-ink-faint">Source: {interviewPrep.source}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {similar.length > 0 && (
          <div>
            <h3 className="mb-3 flex items-center gap-1.5 text-sm font-extrabold text-ink">
              <MessageSquare size={14} /> Similar roles
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {similar.map((j) => (
                <JobCard key={j.job_id} job={j} />
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="lg:sticky lg:top-20 lg:h-fit">
        <ChatAssistant jobId={jobId} resumeSkills={activeResume?.skills} experienceYears={activeResume?.experience_years} />
      </div>
    </div>
  );
}
