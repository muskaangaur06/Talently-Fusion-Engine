import { BarChart3, Bookmark, Briefcase, Key, LogOut, Loader2, Sparkles, UserRound } from "lucide-react";
import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { ApplicationsProvider } from "./context/ApplicationsContext.jsx";
import { ResumeProvider } from "./context/ResumeContext.jsx";

// Route-level code splitting: each page becomes its own chunk instead of one ~827KB
// bundle, so a first-time visitor's initial load only pulls the Landing page's code.
const Analytics = lazy(() => import("./pages/Analytics.jsx"));
const Applications = lazy(() => import("./pages/Applications.jsx"));
const Home = lazy(() => import("./pages/Home.jsx"));
const JobDetails = lazy(() => import("./pages/JobDetails.jsx"));
const Landing = lazy(() => import("./pages/Landing.jsx"));
const Login = lazy(() => import("./pages/Login.jsx"));
const Recommendations = lazy(() => import("./pages/Recommendations.jsx"));

function PageFallback() {
  return (
    <div className="flex justify-center py-24">
      <Loader2 className="animate-spin text-primary" size={32} />
    </div>
  );
}

function ProfileMenu() {
  const navigate = useNavigate();
  const [key, setKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [open, setOpen] = useState(false);
  const [justSaved, setJustSaved] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const existing = sessionStorage.getItem("gemini_api_key");
    if (existing) {
      setKey(existing);
      setSaved(true);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const handleSaveKey = () => {
    if (key.trim()) {
      sessionStorage.setItem("gemini_api_key", key.trim());
      setSaved(true);
    } else {
      sessionStorage.removeItem("gemini_api_key");
      setSaved(false);
    }
    setJustSaved(true);
    setTimeout(() => {
      setJustSaved(false);
      setOpen(false);
    }, 1200);
  };

  const handleLogout = () => {
    sessionStorage.removeItem("gemini_api_key");
    setOpen(false);
    navigate("/login");
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-full border border-line bg-paper py-1 pl-1 pr-3 transition hover:bg-line-soft"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-primary to-[#14a08d] text-white">
          <UserRound size={15} />
        </span>
        <span
          className={`h-1.5 w-1.5 rounded-full ${saved ? "bg-success" : "bg-ink-faint"}`}
          title={saved ? "AI Engine active" : "Heuristic mode"}
        />
      </button>
      {open && (
        <div className="absolute right-0 top-12 z-20 w-80 rounded-2xl border border-line bg-card p-5 shadow-xl">
          <div className="mb-4 flex items-center gap-3 border-b border-line-soft pb-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary to-[#14a08d] text-white">
              <UserRound size={18} />
            </span>
            <div>
              <p className="text-sm font-extrabold text-ink">Your profile</p>
              <p
                className={`text-xs font-bold uppercase tracking-wide ${saved ? "text-success" : "text-ink-faint"}`}
              >
                {saved ? "AI Engine active" : "Heuristic mode"}
              </p>
            </div>
          </div>

          <p className="mb-2 flex items-center gap-1.5 text-xs font-extrabold uppercase tracking-wide text-ink-faint">
            <Key size={12} /> Gemini API key
          </p>
          <p className="mb-3 text-xs leading-relaxed text-ink-faint">
            Stored only in this browser tab's sessionStorage and sent as X-Gemini-API-Key. Leave empty to use
            heuristic fallbacks - every AI feature still works without a key.
          </p>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="AIza..."
            className="mb-3 w-full rounded-xl border-[1.5px] border-line px-3 py-2.5 text-sm text-ink outline-none transition focus:border-primary focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
          />
          <button
            onClick={handleSaveKey}
            className={`mb-4 w-full rounded-xl px-3 py-2.5 text-sm font-bold text-paper transition hover:-translate-y-0.5 ${
              justSaved ? "bg-success" : "bg-gradient-to-br from-primary to-[#14a08d]"
            }`}
          >
            {justSaved ? "Saved" : "Save key"}
          </button>

          <button
            onClick={handleLogout}
            className="flex w-full items-center justify-center gap-2 rounded-xl border-[1.5px] border-line py-2.5 text-sm font-bold text-ink-soft transition hover:border-danger hover:text-danger"
          >
            <LogOut size={15} /> Log out
          </button>
        </div>
      )}
    </div>
  );
}

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      end={to === "/app"}
      className={({ isActive }) =>
        `flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-bold transition ${
          isActive ? "bg-primary text-paper" : "text-ink-soft hover:bg-line-soft hover:text-ink"
        }`
      }
    >
      <Icon size={15} />
      {label}
    </NavLink>
  );
}

function AppShell() {
  return (
    <div className="min-h-screen bg-[#eeece1]">
      <header className="sticky top-0 z-10 border-b border-line bg-paper/95 backdrop-blur-sm">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center px-5 py-4 sm:px-8">
          <Link to="/" className="flex items-center gap-2.5 justify-self-start">
            <div className="flex h-9 w-9 items-center justify-center rounded-[11px] bg-primary">
              <Sparkles size={18} className="text-paper" />
            </div>
            <span className="font-display text-xl font-extrabold text-ink sm:text-2xl">Talently</span>
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            <NavItem to="/app" icon={Briefcase} label="Job Search" />
            <NavItem to="/recommendations" icon={Sparkles} label="Matched Profiles" />
            <NavItem to="/applications" icon={Bookmark} label="Applications" />
            <NavItem to="/analytics" icon={BarChart3} label="Market Analytics" />
          </nav>
          <div className="justify-self-end">
            <ProfileMenu />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-10 sm:px-8">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/app" element={<Home />} />
            <Route path="/jobs/:jobId" element={<JobDetails />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const isStandalonePage = location.pathname === "/" || location.pathname === "/login";

  if (isStandalonePage) {
    return (
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </Suspense>
    );
  }

  return (
    <ResumeProvider>
      <ApplicationsProvider>
        <AppShell />
      </ApplicationsProvider>
    </ResumeProvider>
  );
}
