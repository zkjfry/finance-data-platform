import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  listCompanies,
  searchCompanies,
  type CompanySearchResult,
} from "../api/companies";

export function CompanySearchPage() {
  const [keyword, setKeyword] = useState("");
  const [submittedKeyword, setSubmittedKeyword] = useState("");
  const [showAll, setShowAll] = useState(false);

  const normalizedKeyword = submittedKeyword.trim();
  const isSearchMode = normalizedKeyword.length > 0;
  const listLimit = showAll ? 500 : 20;

  const { data, isLoading, isFetching, error } = useQuery<CompanySearchResult[]>({
    queryKey: ["companies-page", normalizedKeyword, listLimit],
    queryFn: () => {
      if (isSearchMode) {
        return searchCompanies(normalizedKeyword);
      }

      return listCompanies(listLimit);
    },
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextKeyword = keyword.trim();
    setSubmittedKeyword(nextKeyword);

    if (nextKeyword.length > 0) {
      setShowAll(false);
    }
  }

  function handleClear() {
    setKeyword("");
    setSubmittedKeyword("");
    setShowAll(false);
  }

  function handleShowAll() {
    setKeyword("");
    setSubmittedKeyword("");
    setShowAll(true);
  }

  const results = data ?? [];

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold">Companies</h1>
        <p className="mt-1 text-sm text-slate-400">
          Browse companies or search by ticker, company name, or alias.
        </p>
      </section>

      <form
        onSubmit={handleSubmit}
        className="terminal-panel flex flex-col gap-3 p-4 md:flex-row"
      >
        <input
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="Search apple, AAPL, microsoft, NVDA..."
          className="terminal-input min-w-0 flex-1"
          />

        <button
          type="submit"
          disabled={isFetching}
          className="terminal-button-primary"
          >
          {isFetching ? "Loading..." : "Search"}
        </button>

        {(keyword.length > 0 || submittedKeyword.length > 0 || showAll) && (
          <button
            type="button"
            onClick={handleClear}
            disabled={isFetching}
            className="terminal-button-secondary"
            >
            Clear
          </button>
        )}

        {!isSearchMode && !showAll && (
          <button
            type="button"
            onClick={handleShowAll}
            disabled={isFetching}
            className="terminal-button-secondary"
            >
            Show All
          </button>
        )}
      </form>

      <div className="flex items-center justify-between text-sm text-slate-400">
        <div>
          {isSearchMode ? (
            <span>
              Search results for{" "}
              <span className="font-medium text-slate-200">
                "{normalizedKeyword}"
              </span>
            </span>
          ) : showAll ? (
            <span>Showing all available companies</span>
          ) : (
            <span>Showing first {listLimit} companies</span>
          )}
        </div>

        <div>
          {results.length} result{results.length === 1 ? "" : "s"}
        </div>
      </div>

      {isLoading && (
        <div className="terminal-panel p-4 text-sm text-slate-400">
          Loading companies...
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-500/20 bg-red-950/30 p-4 text-sm text-red-300 shadow-xl shadow-black/20 backdrop-blur-xl">
          Failed to load companies.
        </div>
      )}

      {!isLoading && !error && results.length === 0 && (
        <div className="terminal-panel p-4 text-sm text-slate-400">
          {isSearchMode
            ? `No companies found for "${normalizedKeyword}".`
            : "No companies available."}
        </div>
      )}

      {results.length > 0 && (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {results.map((item) => {
            const company = item.company;
            const security = item.primary_security;
            const ticker = security?.ticker ?? company.canonical_name;

            return (
              <Link
                key={`${company.id}-${security?.id ?? "no-security"}`}
                to={`/companies/${ticker}`}
                className="terminal-card p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-medium text-slate-100">
                      {company.canonical_name}
                    </h2>
                    <p className="mt-1 text-sm text-slate-400">
                      {company.legal_name ?? "-"}
                    </p>
                  </div>

                  <span className="terminal-badge">
                    {security?.ticker ?? "N/A"}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <Info label="Exchange" value={security?.exchange} />
                  <Info label="Currency" value={security?.currency} />
                  <Info label="Sector" value={company.sector} />
                  <Info label="Industry" value={company.industry} />
                </div>
              </Link>
            );
          })}
        </section>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 truncate text-slate-300">{value || "-"}</div>
    </div>
  );
}