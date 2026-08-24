import axios from "axios";

const client = axios.create({
  baseURL: "/api",
});

client.interceptors.request.use((config) => {
  const key = sessionStorage.getItem("gemini_api_key");
  if (key) {
    config.headers["X-Gemini-API-Key"] = key;
  }
  return config;
});

export const api = {
  listJobs: (params) => client.get("/jobs", { params }).then((r) => r.data),
  getJob: (jobId) => client.get(`/jobs/${jobId}`).then((r) => r.data),
  getSimilarJobs: (jobId) => client.get(`/jobs/${jobId}/similar`).then((r) => r.data),

  uploadResume: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return client
      .post("/recommendations/upload-resume", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  matchJobs: (payload) => client.post("/recommendations/match", payload).then((r) => r.data),
  fitScore: (payload) => client.post("/recommendations/fit-score", payload).then((r) => r.data),
  atsAnalyze: (payload) => client.post("/recommendations/ats-analyze", payload).then((r) => r.data),
  optimizePhrasing: (payload) => client.post("/recommendations/optimize-phrasing", payload).then((r) => r.data),
  boostResume: (payload) => client.post("/recommendations/boost-resume", payload).then((r) => r.data),
  coverLetter: (payload) => client.post("/recommendations/cover-letter", payload).then((r) => r.data),
  compareResumes: (payload) => client.post("/recommendations/compare-resumes", payload).then((r) => r.data),
  skillsGap: (payload) => client.post("/recommendations/skills-gap", payload).then((r) => r.data),
  personalizedAnalytics: (payload) =>
    client.post("/recommendations/personalized-analytics", payload).then((r) => r.data),

  parseIntent: (query) => client.post("/chat/parse-intent", { query }).then((r) => r.data),
  chat: (payload) => client.post("/chat", payload).then((r) => r.data),
  interviewPrep: (jobId, resumeSkills = []) =>
    client.post("/chat/interview-prep", { job_id: jobId, resume_skills: resumeSkills }).then((r) => r.data),

  getAnalytics: () => client.get("/analytics").then((r) => r.data),
  getEvaluation: () => client.get("/analytics/evaluation").then((r) => r.data),
};

export default api;
