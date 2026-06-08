import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  globalSearch,
  type SearchCompanyResult,
  type SearchNewsResult,
  type SearchReportResult,
} from "../api/search";
import { PageHeader } from "../components/ui/PageHeader";
import { StateBlock } from "../components/ui/StateBlock";

export function SearchPage() {
  const [searchParams] = useSearchParams();
  const keyword = (searchParams.get("q") ?? "").trim();

  const { data, isLoading, error } = useQuery({
    queryKey: ["global-search", keyword],
    queryFn: () => globalSearch(keyword),
    enabled: keyword.length > 0,
  });

  if (!keyword) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Global Search"
          description="Search companies, market data, news and reports from one place."
        />
        <StateBlock type="info" message="Enter a keyword in the top search bar to start searching." />
      </div>
    );
  }

  const companies = data?.companies ?? [];
  const news = data?.news ?? [];
  const reports = data?.reports ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Global Search"
        description={`Search results for "${keyword}".`}
      />

      {isLoading ? (
        <StateBlock type="loading" message="Searching across companies, news and reports..." />
      ) : error ? (
        <StateBlock type="error" message="Search failed. Please try again later." />
      ) : total === 0 ? (
        <StateBlock type="empty" message={`No results found for "${keyword}".`} />
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <SummaryCard title="Total" value={total} />
            <SummaryCard title="Companies" value={companies.length} />
            <SummaryCard title="News" value={news.length} />
            <SummaryCard title="Reports" value={reports.length} />
          </section>

          <SearchSection
            title="Companies"
            description="Matched by company name, ticker, alias, sector or industry."
            emptyMessage="No matching companies."
            viewAllTo={`/companies?keyword=${encodeURIComponent(keyword)}`}
          >
            {companies.length === 0 ? (
              <EmptyMini message="No matching companies." />
            ) : (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {companies.map((item) => (
                  <CompanyResultCard key={`${item.id}-${item.ticker}`} item={item} />
                ))}
              </div>
            )}
          </SearchSection>

          <SearchSection
            title="News"
            description="Matched by title, summary, body text or ticker symbols."
            emptyMessage="No matching news."
            viewAllTo={`/news?keyword=${encodeURIComponent(keyword)}`}
          >
            {news.length === 0 ? (
              <EmptyMini message="No matching news." />
            ) : (
              <div className="space-y-3">
                {news.map((item) => (
                  <NewsResultCard key={item.id} item={item} />
                ))}
              </div>
            )}
          </SearchSection>

          <SearchSection
            title="Reports"
            description="Matched by title, company, ticker, report type or filing text."
            emptyMessage="No matching reports."
            viewAllTo={`/reports?keyword=${encodeURIComponent(keyword)}`}
          >
            {reports.length === 0 ? (
              <EmptyMini message="No matching reports." />
            ) : (
              <div className="space-y-3">
                {reports.map((item) => (
                  <ReportResultCard key={item.id} item={item} />
                ))}
              </div>
            )}
          </SearchSection>
        </>
      )}
    </div>
  );
}

function SummaryCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="terminal-card p-5">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {title}
      </div>
      <div className="mt-3 text-3xl font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}

function SearchSection({
  title,
  description,
  viewAllTo,
  children,
}: {
  title: string;
  description: string;
  emptyMessage: string;
  viewAllTo: string;
  children: React.ReactNode;
}) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="terminal-section-title">{title}</h2>
          <p className="terminal-section-subtitle">{description}</p>
        </div>

        <Link
          to={viewAllTo}
          className="shrink-0 text-sm font-medium text-cyan-300 hover:text-cyan-200"
        >
          View all
        </Link>
      </div>

      {children}
    </section>
  );
}

function CompanyResultCard({ item }: { item: SearchCompanyResult }) {
  const target = item.ticker ? `/companies/${item.ticker}` : "/companies";

  return (
    <Link to={target} className="terminal-card block p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-slate-100">
            {item.ticker ?? "N/A"}
          </div>
          <div className="mt-1 text-sm text-slate-300">
            {item.company_name}
          </div>
        </div>

        <span className="terminal-badge">
          {item.exchange ?? "Market"}
        </span>
      </div>

      <div className="mt-4 grid gap-2 text-xs text-slate-400">
        <div>
          <span className="text-slate-500">Sector: </span>
          {item.sector ?? "-"}
        </div>
        <div>
          <span className="text-slate-500">Industry: </span>
          {item.industry ?? "-"}
        </div>
      </div>
    </Link>
  );
}

function NewsResultCard({ item }: { item: SearchNewsResult }) {
  const content = (
    <div className="terminal-muted-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="line-clamp-2 font-semibold text-slate-100">
            {item.title}
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span>{item.source ?? "news"}</span>
            <span>•</span>
            <span>{formatDateTime(item.published_at)}</span>
            {item.ticker && (
              <>
                <span>•</span>
                <span className="text-cyan-300">{item.ticker}</span>
              </>
            )}
          </div>
        </div>

        <span className="terminal-badge shrink-0">News</span>
      </div>

      {item.summary && (
        <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-400">
          {item.summary}
        </p>
      )}
    </div>
  );

  if (!item.url) {
    return content;
  }

  return (
    <a href={item.url} target="_blank" rel="noreferrer" className="block">
      {content}
    </a>
  );
}

function ReportResultCard({ item }: { item: SearchReportResult }) {
  const href = item.pdf_url || item.detail_url || item.url;

  const content = (
    <div className="terminal-muted-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="line-clamp-2 font-semibold text-slate-100">
            {item.title}
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span>{item.source ?? "report"}</span>
            <span>•</span>
            <span>{formatDateTime(item.published_at)}</span>
            {item.ticker && (
              <>
                <span>•</span>
                <span className="text-cyan-300">{item.ticker}</span>
              </>
            )}
            {item.report_type && (
              <>
                <span>•</span>
                <span>{item.report_type}</span>
              </>
            )}
          </div>
        </div>

        <span className="terminal-badge shrink-0">Report</span>
      </div>

      {item.summary && (
        <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-400">
          {item.summary}
        </p>
      )}
    </div>
  );

  if (!href) {
    return content;
  }

  return (
    <a href={href} target="_blank" rel="noreferrer" className="block">
      {content}
    </a>
  );
}

function EmptyMini({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4 text-sm text-slate-500">
      {message}
    </div>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}