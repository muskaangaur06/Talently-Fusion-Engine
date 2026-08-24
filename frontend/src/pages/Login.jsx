import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const FEATURES = [
  { tag: "Live right now", text: "45,107 roles indexed, scored in 0.4s per search" },
  { tag: "Resume boost", text: "We rewrite your weak lines using only what's already true" },
  { tag: "Skills gap", text: "See exactly what to learn next, ranked by real employer demand" },
];

const CYCLE_MS = 3200;

export default function Login() {
  const navigate = useNavigate();
  const [featureIndex, setFeatureIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFeatureIndex((i) => (i + 1) % FEATURES.length);
    }, CYCLE_MS);
    return () => clearInterval(timer);
  }, []);

  const handleGuest = (e) => {
    e.preventDefault();
    navigate("/app");
  };

  const active = FEATURES[featureIndex];

  return (
    <div className="grid min-h-screen grid-cols-1 bg-paper md:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-primary via-[#14a08d] to-[#1fbfa8] p-16 md:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-50"
          style={{
            backgroundImage: "radial-gradient(rgba(255,255,255,0.14) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
            animation: "loginDots 6s linear infinite",
          }}
        />
        <div
          className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/10"
          style={{ animation: "loginDrift 9s ease-in-out infinite" }}
        />
        <div
          className="pointer-events-none absolute -bottom-28 -left-16 h-56 w-56 rounded-full bg-white/5"
          style={{ animation: "loginDrift 11s ease-in-out infinite reverse" }}
        />

        <div className="relative flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-[11px] bg-white/15">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2l2.4 6.5L21 11l-6.6 2.5L12 20l-2.4-6.5L3 11l6.6-2.5z" />
            </svg>
          </div>
          <span className="text-lg font-extrabold text-white">Talently</span>
        </div>

        <div className="relative">
          <h1 className="mb-5 max-w-md text-[42px] font-extrabold leading-[1.15] tracking-tight text-white">
            Welcome back. Your matches didn't stop while you were away.
          </h1>
          <p className="mb-7 max-w-sm text-[15.5px] font-medium leading-relaxed text-white/85">
            Sign in to pick up where you left off, or explore as a guest to see what's new first.
          </p>

          <div className="relative h-24 w-[280px]">
            <div
              className="absolute -right-8 -top-3.5 z-10 rounded-full bg-accent px-3 py-1.5 text-[11px] font-extrabold text-white shadow-[0_10px_22px_rgba(194,113,29,0.35)]"
              style={{ animation: "loginFloatBadge 5s ease-in-out infinite" }}
            >
              +3 new matches
            </div>
            <div
              className="relative z-[1] w-[280px] rounded-2xl bg-white p-5 shadow-[0_20px_40px_rgba(10,40,35,0.18)]"
              style={{ animation: "loginFloatCard 6s ease-in-out infinite" }}
            >
              <div className="mb-2.5 flex items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-primary-faint text-[11.5px] font-extrabold text-primary">
                  ML
                </div>
                <div className="flex-1 text-[13px] font-extrabold text-ink">ML Engineer, Netflix</div>
                <span className="text-base font-extrabold text-primary">96%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-primary-faint">
                <div className="h-full w-[96%] rounded-full bg-primary" />
              </div>
            </div>
          </div>
        </div>

        <div className="relative rounded-2xl bg-white/10 p-5">
          <div className="mb-2.5 flex items-center gap-2">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#eafff8]" />
            <span className="text-xs font-extrabold uppercase tracking-wide text-[#eafff8]">{active.tag}</span>
          </div>
          <div key={featureIndex} className="text-[15px] font-bold leading-relaxed text-white" style={{ animation: "loginFadeSwap 0.4s ease-out" }}>
            {active.text}
          </div>
          <div className="mt-3 flex justify-end gap-1.5">
            {FEATURES.map((_, i) => (
              <span
                key={i}
                className="h-[5px] w-[5px] rounded-full transition-colors duration-300"
                style={{ backgroundColor: i === featureIndex ? "#fff" : "rgba(255,255,255,0.35)" }}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-col justify-center px-8 py-16 sm:px-16 md:px-24">
        <div className="mb-9">
          <h2 className="mb-2 text-3xl font-extrabold tracking-tight text-ink">Sign in</h2>
          <p className="text-[14.5px] text-ink-soft">
            New here?{" "}
            <Link to="/app" className="font-bold text-primary hover:text-primary-deep">
              Explore as a guest
            </Link>{" "}
            first, no account needed.
          </p>
        </div>

        <form className="space-y-[18px]" onSubmit={handleGuest}>
          <div>
            <label className="mb-2 block text-xs font-extrabold uppercase tracking-wide text-ink-soft">
              Email address
            </label>
            <input
              type="email"
              placeholder="you@example.com"
              className="w-full rounded-xl border-[1.5px] border-line bg-card px-4 py-3.5 text-[14.5px] text-ink outline-none transition focus:border-primary focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-extrabold uppercase tracking-wide text-ink-soft">Password</label>
              <a href="#" className="text-[13px] font-bold text-primary hover:text-primary-deep">
                Forgot?
              </a>
            </div>
            <input
              type="password"
              placeholder="********"
              className="w-full rounded-xl border-[1.5px] border-line bg-card px-4 py-3.5 text-[14.5px] text-ink outline-none transition focus:border-primary focus:shadow-[0_0_0_4px_rgba(14,116,102,0.12)]"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-xl bg-gradient-to-br from-primary to-[#14a08d] py-4 text-[15px] font-extrabold text-paper shadow-[0_10px_24px_rgba(14,116,102,0.24)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_30px_rgba(14,116,102,0.3)]"
          >
            Sign in
          </button>

          <div className="flex items-center gap-3.5 py-2">
            <div className="h-px flex-1 bg-line" />
            <span className="text-xs font-bold text-ink-faint">OR</span>
            <div className="h-px flex-1 bg-line" />
          </div>

          <button
            type="button"
            onClick={handleGuest}
            className="w-full rounded-xl border-[1.5px] border-line py-3.5 text-[14.5px] font-bold text-ink transition hover:border-primary hover:text-primary"
          >
            Explore as guest, no sign-in needed
          </button>
        </form>
      </div>

      <style>{`
        @keyframes loginDots { 0% { background-position: 0 0; } 100% { background-position: 48px 48px; } }
        @keyframes loginDrift { 0%, 100% { transform: translate(0,0); } 50% { transform: translate(-14px, 10px); } }
        @keyframes loginFloatCard { 0%, 100% { transform: translateY(0) rotate(-1.2deg); } 50% { transform: translateY(-8px) rotate(-1.2deg); } }
        @keyframes loginFloatBadge { 0%, 100% { transform: translateY(0) rotate(2deg); } 50% { transform: translateY(-6px) rotate(2deg); } }
        @keyframes loginFadeSwap { 0% { opacity: 0; transform: translateY(4px); } 100% { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
