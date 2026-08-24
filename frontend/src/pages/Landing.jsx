import { ArrowRight, CheckCircle2, PenLine, SearchCheck, Target } from "lucide-react";
import { Link } from "react-router-dom";

const SAMPLE_JOB = {
  title: "Senior Product Analyst",
  company: "Spotify",
  location: "Remote",
  initials: "SP",
  score: 94,
};

const FEATURES = [
  {
    icon: SearchCheck,
    eyebrow: "The search that understands you",
    title: "Say it like a human. We'll search it like a machine.",
    body: "“Backend, no on-call, sane humans only” just works. No keyword guessing, no exact phrases. Just what you meant.",
  },
  {
    icon: CheckCircle2,
    eyebrow: "A number you can actually trust",
    title: "Know your odds before you write the cover letter.",
    body: "Skills, experience, and meaning, scored against every listing. No more finding out three paragraphs in.",
  },
  {
    icon: PenLine,
    eyebrow: "The words you deserved the first time",
    title: "You did the work. Your resume just never quite said it out loud.",
    body: "We find the lines where you played yourself down, “helped with,” “was involved in,” and rewrite them using nothing but what's already true.",
  },
  {
    icon: Target,
    eyebrow: "The gap, named instead of felt",
    title: "Not fourteen skills. The one that's actually in your way.",
    body: "Ranked by real demand, not a wishlist. Then prep built for the exact role, not a generic guide.",
  },
];

function TopNav() {
  return (
    <div className="flex items-center justify-between px-8 py-6 md:px-16">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-[11px] bg-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f4f3ee" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2l2.4 6.5L21 11l-6.6 2.5L12 20l-2.4-6.5L3 11l6.6-2.5z" />
          </svg>
        </div>
        <span className="text-xl font-extrabold text-ink">Talently</span>
      </div>
      <div className="hidden items-center gap-1 sm:flex">
        <Link to="/app" className="rounded-lg px-5 py-2.5 text-sm font-bold text-ink-soft hover:text-ink">
          Browse jobs
        </Link>
        <a href="#how-it-works" className="rounded-lg px-5 py-2.5 text-sm font-bold text-ink-soft hover:text-ink">
          How it works
        </a>
        <Link
          to="/login"
          className="ml-2.5 rounded-xl bg-primary px-6 py-2.5 text-sm font-extrabold text-paper hover:bg-primary-deep"
        >
          Sign in
        </Link>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <div className="px-8 pt-8 text-center md:px-16">
      <div className="mx-auto mb-8 inline-flex items-center gap-2 rounded-full bg-primary-faint px-4 py-2 text-[12.5px] font-extrabold text-primary-deep">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
        45,107 roles, scored fresh every search
      </div>
      <h1 className="mx-auto max-w-4xl text-4xl font-extrabold leading-[1.08] tracking-tight text-ink sm:text-5xl md:text-[70px]">
        Stop applying blind.
        <br />
        <span className="bg-gradient-to-r from-primary to-[#1fbfa8] bg-clip-text text-transparent">
          Start applying matched.
        </span>
      </h1>
      <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-ink-soft sm:text-lg">
        Upload your resume once. We read it the way a real hiring manager would, then show you exactly where you
        stand before you spend another hour writing a cover letter.
      </p>
      <div className="mt-9 flex flex-col items-center justify-center gap-3.5 sm:flex-row">
        <Link
          to="/login"
          className="flex items-center gap-2 rounded-2xl bg-gradient-to-br from-primary to-[#14a08d] px-8 py-4 text-base font-extrabold text-paper shadow-[0_12px_28px_rgba(14,116,102,0.28)] transition hover:-translate-y-0.5"
        >
          Get matched free <ArrowRight size={17} />
        </Link>
        <Link
          to="/app"
          className="rounded-2xl border-[1.5px] border-line px-8 py-4 text-base font-bold text-ink hover:border-primary hover:text-primary"
        >
          Explore as guest
        </Link>
      </div>
      <p className="mt-4 text-[13px] font-semibold text-ink-faint">
        No credit card. No spam. Just a straight answer on your fit.
      </p>
    </div>
  );
}

function ProofStrip() {
  return (
    <div className="grid grid-cols-1 gap-5 px-8 pb-20 pt-16 md:grid-cols-3 md:px-16">
      <div className="rounded-[22px] border border-line bg-card p-7">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-faint text-[13px] font-extrabold text-primary">
            {SAMPLE_JOB.initials}
          </div>
          <div>
            <div className="text-[14.5px] font-extrabold text-ink">{SAMPLE_JOB.title}</div>
            <div className="mt-0.5 text-xs font-semibold text-ink-faint">
              {SAMPLE_JOB.company}, {SAMPLE_JOB.location}
            </div>
          </div>
        </div>
        <div className="mb-2.5 flex items-center justify-between">
          <span className="text-xs font-bold text-ink-faint">Composite match</span>
          <span className="text-xl font-extrabold text-primary">{SAMPLE_JOB.score}%</span>
        </div>
        <div className="h-[7px] overflow-hidden rounded-full bg-primary-faint">
          <div className="h-full rounded-full bg-primary" style={{ width: `${SAMPLE_JOB.score}%` }} />
        </div>
      </div>

      <div className="flex flex-col justify-center rounded-[22px] bg-primary p-7">
        <div className="text-[42px] font-extrabold leading-none text-paper">0.4s</div>
        <div className="mt-2 text-[13px] font-bold text-primary-soft">
          to score every open role against your resume, not just the ones you clicked on
        </div>
      </div>

      <div className="rounded-[22px] bg-night p-7">
        <div className="mb-3.5 text-[11.5px] font-extrabold uppercase tracking-wide text-[#7fd9c4]">
          Same you, said better
        </div>
        <div className="mb-1.5 text-[12.5px] text-ink-faint line-through">"helped with database design"</div>
        <div className="text-sm font-bold leading-relaxed text-paper">
          "led database design across 3 services"
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  return (
    <div id="how-it-works" className="border-t border-line bg-gradient-to-b from-card to-paper px-8 py-24 md:px-16">
      <div className="mx-auto mb-20 max-w-2xl text-center">
        <div className="mb-4 text-[13px] font-extrabold uppercase tracking-widest text-primary">
          What actually happens in here
        </div>
        <h2 className="text-3xl font-extrabold leading-tight tracking-tight text-ink sm:text-[44px]">
          No more rage-quitting job boards.
        </h2>
        <p className="mt-4 text-base font-semibold text-ink-soft">
          Four things make that true. None of them ask you to guess.
        </p>
      </div>

      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-5 md:grid-cols-2">
        {FEATURES.map(({ icon: Icon, eyebrow, title, body }) => (
          <div key={eyebrow} className="flex items-start gap-5 rounded-3xl border border-line bg-card p-9">
            <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-faint to-primary-soft text-primary">
              <Icon size={23} strokeWidth={2} />
            </div>
            <div>
              <div className="mb-2 text-xs font-extrabold uppercase tracking-wide text-primary">{eyebrow}</div>
              <h3 className="mb-3 text-[21px] font-extrabold leading-snug text-ink">{title}</h3>
              <p className="text-[14.5px] leading-relaxed text-ink-soft">{body}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ClosingCta() {
  return (
    <div className="relative overflow-hidden bg-night px-8 py-24 text-center md:px-16">
      <div
        className="pointer-events-none absolute -top-36 left-1/2 h-72 w-[520px] -translate-x-1/2 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(31,191,168,0.18), transparent 70%)" }}
      />
      <div className="relative">
        <div className="mb-[18px] text-[13px] font-extrabold uppercase tracking-widest text-[#7fd9c4]">Before you go</div>
        <h2 className="mx-auto max-w-xl text-2xl font-extrabold leading-snug text-paper sm:text-[38px]">
          You've probably sent fifty resumes into the dark this month. Send the next one somewhere that actually
          looks back.
        </h2>
        <Link
          to="/login"
          className="mt-8 inline-block rounded-2xl bg-paper px-8 py-4 text-base font-extrabold text-primary-deep"
        >
          Get matched free &rarr;
        </Link>
        <p className="mt-4.5 text-[13px] font-semibold text-ink-faint">Takes about ninety seconds. No credit card.</p>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="bg-paper">
      <TopNav />
      <Hero />
      <ProofStrip />
      <HowItWorks />
      <ClosingCta />
    </div>
  );
}
