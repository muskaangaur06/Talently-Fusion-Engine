import { Bookmark, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { APPLICATION_STATUSES, useApplications } from "../context/ApplicationsContext.jsx";

const STATUS_STYLES = {
  Saved: "bg-line-soft text-ink-soft",
  Applied: "bg-primary-soft text-primary-deep",
  Interviewing: "bg-warning-soft text-warning",
  Offer: "bg-success-soft text-success",
  Rejected: "bg-danger-soft text-danger",
};

function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default function Applications() {
  const { applications, updateStatus, removeApplication } = useApplications();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-[28px] font-extrabold text-ink">Your applications</h1>
        <p className="text-[15px] font-medium text-ink-soft">
          Roles you've saved or applied to, tracked right here in your browser.
        </p>
      </div>

      {applications.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-[28px] bg-card py-20 text-center shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-faint text-primary">
            <Bookmark size={26} />
          </div>
          <h3 className="mb-2 text-lg font-extrabold text-ink">Nothing tracked yet</h3>
          <p className="mb-6 max-w-sm text-sm font-medium text-ink-soft">
            Open a job you like and hit "Save" or "Apply" to start tracking it here.
          </p>
          <Link
            to="/app"
            className="rounded-xl bg-gradient-to-br from-primary to-[#14a08d] px-6 py-3 text-sm font-extrabold text-white transition hover:-translate-y-0.5"
          >
            Browse jobs
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl bg-card shadow-[0_2px_10px_rgba(35,39,43,0.08)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line-soft text-xs font-extrabold uppercase tracking-wide text-ink-faint">
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4">Company</th>
                <th className="px-6 py-4">Saved on</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.job_id} className="border-b border-line-soft last:border-0">
                  <td className="px-6 py-4 font-bold text-ink">
                    <Link to={`/jobs/${a.job_id}`} className="hover:text-primary">
                      {a.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 font-semibold text-ink-soft">{a.company_name}</td>
                  <td className="px-6 py-4 font-semibold text-ink-faint">{formatDate(a.appliedAt)}</td>
                  <td className="px-6 py-4">
                    <select
                      value={a.status}
                      onChange={(e) => updateStatus(a.job_id, e.target.value)}
                      className={`rounded-full border-0 px-3 py-1.5 text-xs font-extrabold outline-none ${STATUS_STYLES[a.status] || STATUS_STYLES.Saved}`}
                    >
                      {APPLICATION_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => removeApplication(a.job_id)}
                      className="text-ink-faint hover:text-danger"
                      title="Remove"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
