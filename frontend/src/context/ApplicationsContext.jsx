import { createContext, useContext, useEffect, useState } from "react";

const ApplicationsContext = createContext(null);
const STORAGE_KEY = "job_board_applications_v1";

export const APPLICATION_STATUSES = ["Saved", "Applied", "Interviewing", "Offer", "Rejected"];

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function ApplicationsProvider({ children }) {
  const [applications, setApplications] = useState([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setApplications(loadFromStorage());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(applications));
    } catch {
      // localStorage unavailable - state still works for this session
    }
  }, [applications, hydrated]);

  const addApplication = (job, status = "Saved") => {
    setApplications((prev) => {
      const existing = prev.find((a) => a.job_id === job.job_id);
      if (existing) {
        return prev.map((a) => (a.job_id === job.job_id ? { ...a, status } : a));
      }
      return [
        ...prev,
        {
          job_id: job.job_id,
          title: job.title,
          company_name: job.company_name,
          location: job.location,
          status,
          appliedAt: new Date().toISOString(),
        },
      ];
    });
  };

  const updateStatus = (jobId, status) => {
    setApplications((prev) => prev.map((a) => (a.job_id === jobId ? { ...a, status } : a)));
  };

  const removeApplication = (jobId) => {
    setApplications((prev) => prev.filter((a) => a.job_id !== jobId));
  };

  const isTracked = (jobId) => applications.some((a) => a.job_id === jobId);

  const value = { applications, addApplication, updateStatus, removeApplication, isTracked };

  return <ApplicationsContext.Provider value={value}>{children}</ApplicationsContext.Provider>;
}

export function useApplications() {
  const ctx = useContext(ApplicationsContext);
  if (!ctx) throw new Error("useApplications must be used within an ApplicationsProvider");
  return ctx;
}
