import { createContext, useContext, useEffect, useState } from "react";
import { DEMO_RESUMES } from "../data/demoResumes.js";

const ResumeContext = createContext(null);
const STORAGE_KEY = "job_board_resumes_v1";
const MAX_RESUMES = 3;

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { resumes: [], activeResumeId: null };
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.resumes)) return { resumes: [], activeResumeId: null };
    // Re-sync sample-resume labels from the current source data - a browser that cached
    // an older copy (e.g. from before the "(demo)" suffix was removed) would otherwise
    // keep showing stale label text indefinitely, since resumes persist across reloads.
    const demoById = Object.fromEntries(DEMO_RESUMES.map((d) => [d.id, d]));
    const resumes = parsed.resumes.map((r) => (demoById[r.id] ? { ...r, label: demoById[r.id].label } : r));
    return { ...parsed, resumes };
  } catch {
    return { resumes: [], activeResumeId: null };
  }
}

export function ResumeProvider({ children }) {
  const [resumes, setResumes] = useState([]);
  const [activeResumeId, setActiveResumeId] = useState(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const { resumes: storedResumes, activeResumeId: storedActiveId } = loadFromStorage();
    setResumes(storedResumes);
    setActiveResumeId(storedActiveId);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ resumes, activeResumeId }));
    } catch {
      // localStorage unavailable (private mode, quota) - state still works for this session
    }
  }, [resumes, activeResumeId, hydrated]);

  const addResume = (resume) => {
    const withId = { ...resume, id: resume.id || `resume-${Date.now()}` };
    setResumes((prev) => {
      const next = prev.length >= MAX_RESUMES ? [...prev.slice(1), withId] : [...prev, withId];
      return next;
    });
    setActiveResumeId(withId.id);
    return withId.id;
  };

  const removeResume = (id) => {
    setResumes((prev) => prev.filter((r) => r.id !== id));
    setActiveResumeId((prev) => (prev === id ? null : prev));
  };

  const loadDemoResume = (demoResume) => {
    return addResume({ ...demoResume, source: "demo" });
  };

  const activeResume = resumes.find((r) => r.id === activeResumeId) || null;

  const value = {
    resumes,
    activeResumeId,
    activeResume,
    setActiveResumeId,
    addResume,
    removeResume,
    loadDemoResume,
    maxResumes: MAX_RESUMES,
  };

  return <ResumeContext.Provider value={value}>{children}</ResumeContext.Provider>;
}

export function useResumes() {
  const ctx = useContext(ResumeContext);
  if (!ctx) throw new Error("useResumes must be used within a ResumeProvider");
  return ctx;
}
