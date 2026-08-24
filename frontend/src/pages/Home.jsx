import { Loader2, Search, Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import FilterPanel from "../components/FilterPanel.jsx";
import JobCard from "../components/JobCard.jsx";
import api from "../services/api.js";

export default function Home() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    location: null,
    source: null,
    min_experience: null,
    max_experience: null,
    max_age_days: null,
  });
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [parsingIntent, setParsingIntent] = useState(false);
  const [lastQueryUsedVector, setLastQueryUsedVector] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const pageSize = 12;
  const requestRef = useRef(0);
  const sentinelRef = useRef(null);

  const fetchJobs = async (searchQuery, searchFilters, targetPage, { append = false } = {}) => {
    const requestId = ++requestRef.current;
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const data = await api.listJobs({
        q: searchQuery,
        ...searchFilters,
        page: targetPage,
        page_size: pageSize,
      });
      if (requestId !== requestRef.current) return;
      setJobs((prev) => (append ? [...prev, ...data.jobs] : data.jobs));
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
      setLastQueryUsedVector(Boolean(searchQuery && searchQuery.trim()));
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
        setLoadingMore(false);
      }
    }
  };

  useEffect(() => {
    fetchJobs("", filters, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadNextPage = useCallback(() => {
    if (loading || loadingMore) return;
    if (page >= totalPages) return;
    fetchJobs(query, filters, page + 1, { append: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, loadingMore, page, totalPages, query, filters]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadNextPage();
      },
      { rootMargin: "600px 0px" }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [loadNextPage]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      fetchJobs("", filters, 1);
      return;
    }
    await fetchJobs(query, filters, 1);
  };

  const handleFilterWithAI = async () => {
    if (!query.trim()) return;
    setParsingIntent(true);
    try {
      const intent = await api.parseIntent(query);
      const mergedFilters = {
        ...filters,
        location: intent.location || filters.location,
        source: intent.source || filters.source,
        min_experience: intent.min_experience ?? filters.min_experience,
        max_experience: intent.max_experience ?? filters.max_experience,
      };
      setFilters(mergedFilters);
      await fetchJobs(intent.keywords || query, mergedFilters, 1);
    } finally {
      setParsingIntent(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    fetchJobs(query, newFilters, 1);
  };

  const hasMore = page < totalPages;
  const activeFilterCount = Object.values(filters).filter((v) => v !== null && v !== "").length;

  return (
    <div className="space-y-10">
      <div className="rounded-[28px] bg-gradient-to-br from-primary via-[#14a08d] to-[#1fbfa8] px-8 py-14 text-center shadow-[0_20px_50px_rgba(14,116,102,0.22)] sm:px-16">
        <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-[12.5px] font-extrabold text-white">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
          {total.toLocaleString()} roles, scored fresh every search
        </div>
        <h1 className="font-display mx-auto max-w-2xl text-[34px] font-extrabold leading-tight text-white sm:text-[42px]">
          Find your next role
        </h1>
        <p className="mx-auto mt-3 max-w-md text-[15.5px] font-medium text-white/85">
          Search, filter, and let the scroll do the rest.
        </p>

        <form onSubmit={handleSearch} className="mx-auto mt-8 flex max-w-2xl gap-2.5">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-ink-faint" size={18} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Try “remote data science jobs in bangalore, 3+ years”"
              className="w-full rounded-2xl bg-white py-4 pl-11 pr-3 text-[15px] text-ink shadow-[0_10px_30px_rgba(10,40,35,0.18)] outline-none transition focus:shadow-[0_0_0_4px_rgba(255,255,255,0.35)]"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-night px-7 py-4 text-[15px] font-extrabold text-paper transition hover:-translate-y-0.5 disabled:opacity-60"
          >
            Search
          </button>
        </form>

        <div className="mx-auto mt-4 flex max-w-2xl flex-wrap items-center justify-center gap-3">
          <button
            onClick={handleFilterWithAI}
            disabled={parsingIntent || !query.trim()}
            className="flex items-center gap-1.5 rounded-full bg-white/15 px-4 py-2 text-[13px] font-bold text-white transition hover:bg-white/25 disabled:opacity-50"
          >
            {parsingIntent ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            Let AI parse that for me
          </button>
          <button
            onClick={() => setShowFilters((v) => !v)}
            className="flex items-center gap-1.5 rounded-full bg-white/15 px-4 py-2 text-[13px] font-bold text-white transition hover:bg-white/25"
          >
            {showFilters ? "Hide filters" : "Structured filters"}
            {activeFilterCount > 0 && (
              <span className="rounded-full bg-white px-1.5 text-[11px] font-extrabold text-primary-deep">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {showFilters && (
        <FilterPanel filters={filters} onChange={handleFilterChange} lastQueryUsedVector={lastQueryUsedVector} />
      )}

      <div>
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-display text-xl font-extrabold text-ink">
            {total.toLocaleString()} roles waiting
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {jobs.map((job) => (
                <JobCard key={job.job_id} job={job} />
              ))}
            </div>

            <div ref={sentinelRef} className="h-1 w-full" />

            {loadingMore && (
              <div className="flex justify-center py-10">
                <Loader2 className="animate-spin text-primary" size={24} />
              </div>
            )}

            {!hasMore && jobs.length > 0 && (
              <p className="py-10 text-center text-sm font-semibold text-ink-faint">
                That's every role matching your search, {total.toLocaleString()} in total.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
