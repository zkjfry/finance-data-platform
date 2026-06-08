import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getDashboardSummary,
  type CrawlRun,
  type DashboardNewsItem,
  type DashboardReportItem,
  type MarketDashboardItem,
} from "../api/dashboard";
import { PageHeader } from "../components/ui/PageHeader";
import { StateBlock } from "../components/ui/StateBlock";

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  if (isLoading) {
    return <StateBlock type="loading" message="Loading dashboard..." />;
  }

  if (error || !data) {
    return <StateBlock type="error" message="Failed to load dashboard summary." />;
  }

  const counts = data.counts ?? {};
  const marketOverview = data.market_overview ?? [];
  const topMovers = data.top_movers ?? [];
  const latestNews = data.latest_news ?? [];
  const recentReports = data.recent_reports ?? [];
  const heatmap = data.heatmap ?? [];
  const latestRuns = data.latest_crawl_runs ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Market intelligence overview built from your collected finance data."
      />

      <section className="terminal-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="terminal-section-title">Market Overview</h2>
            <p className="terminal-section-subtitle">
              Latest close and one-day movement for tracked securities.
            </p>
          </div>

          <span className="terminal-badge">
            {counts.securities ?? 0} Securities
          </span>
        </div>

        {marketOverview.length === 0 ? (
          <StateBlock type="empty" message="No market price data available." />
        ) : (
          <div className="grid gap-4 md:grid-cols-4">
            {marketOverview.map((item) => (
              <MarketOverviewCard key={item.ticker} item={item} />
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1.35fr]">
        <TopMoversPanel items={topMovers} />
        <LatestNewsPanel items={latestNews} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1.35fr]">
        <RecentReportsPanel items={recentReports} />
        <HeatmapPanel items={heatmap} />
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Companies" value={counts.companies} />
        <MetricCard title="News" value={counts.news_articles} />
        <MetricCard title="Reports" value={counts.research_reports} />
        <MetricCard title="Price Rows" value={counts.market_prices} />
      </section>

      <LatestCrawlRunsPanel runs={latestRuns} />
    </div>
  );
}

function MarketOverviewCard({ item }: { item: MarketDashboardItem }) {
  const positive = (item.change_pct ?? 0) >= 0;

  return (
    <Link
      to={`/companies/${item.ticker}`}
      className="terminal-gradient-card group relative overflow-hidden p-4"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-cyan-400/10 blur-2xl transition group-hover:bg-cyan-400/20" />

      <div className="relative">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            {item.ticker}
          </div>
          <div className="text-xs text-slate-500">{item.exchange ?? "-"}</div>
        </div>

        <div className="mt-3 text-2xl font-semibold text-slate-100">
          {formatMoney(item.close, item.currency)}
        </div>

        <div
          className={
            positive
              ? "mt-2 text-sm font-medium text-emerald-300"
              : "mt-2 text-sm font-medium text-red-300"
          }
        >
          {formatChange(item.change, item.change_pct)}
        </div>

        <div className="mt-4 h-8">
          <MiniSparkline data={item.sparkline} positive={positive} />
        </div>
      </div>
    </Link>
  );
}

function TopMoversPanel({ items }: { items: MarketDashboardItem[] }) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="terminal-section-title">Top Movers</h2>
          <p className="terminal-section-subtitle">
            Largest absolute daily moves among tracked securities.
          </p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-sm text-slate-400">No movers available.</div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/60 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Symbol</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3 text-right">Price</th>
                <th className="px-4 py-3 text-right">Change</th>
                <th className="px-4 py-3 text-right">% Change</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/10">
              {items.map((item) => {
                const positive = (item.change_pct ?? 0) >= 0;

                return (
                  <tr key={item.ticker} className="transition hover:bg-white/[0.03]">
                    <td className="px-4 py-3">
                      <Link
                        to={`/companies/${item.ticker}`}
                        className="font-semibold text-cyan-300 hover:text-cyan-200"
                      >
                        {item.ticker}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {item.company_name}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-300">
                      {formatMoney(item.close, item.currency)}
                    </td>
                    <td
                      className={
                        positive
                          ? "px-4 py-3 text-right text-emerald-300"
                          : "px-4 py-3 text-right text-red-300"
                      }
                    >
                      {formatSignedNumber(item.change)}
                    </td>
                    <td
                      className={
                        positive
                          ? "px-4 py-3 text-right text-emerald-300"
                          : "px-4 py-3 text-right text-red-300"
                      }
                    >
                      {formatPercent(item.change_pct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function LatestNewsPanel({ items }: { items: DashboardNewsItem[] }) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="terminal-section-title">Latest News</h2>
          <p className="terminal-section-subtitle">
            Most recent articles collected by the news pipeline.
          </p>
        </div>

        <Link to="/news" className="text-sm text-cyan-300 hover:text-cyan-200">
          View all
        </Link>
      </div>

      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="text-sm text-slate-400">No news available.</div>
        ) : (
          items.map((item) => (
            <a
              key={item.id}
              href={item.url ?? undefined}
              target="_blank"
              rel="noreferrer"
              className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan-400/40 hover:bg-white/[0.05]"
            >
              <div className="flex items-start justify-between gap-4">
                <h3 className="line-clamp-2 text-sm font-semibold text-slate-100">
                  {item.title}
                </h3>

                <span className="shrink-0 text-xs text-slate-500">
                  {formatTime(item.published_at)}
                </span>
              </div>

              <div className="mt-2 text-xs text-slate-500">
                {item.source ?? "Unknown source"}
              </div>
            </a>
          ))
        )}
      </div>
    </section>
  );
}

function RecentReportsPanel({ items }: { items: DashboardReportItem[] }) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="terminal-section-title">Recent Reports</h2>
          <p className="terminal-section-subtitle">
            Latest filings and research documents.
          </p>
        </div>

        <Link to="/reports" className="text-sm text-cyan-300 hover:text-cyan-200">
          View all
        </Link>
      </div>

      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="text-sm text-slate-400">No reports available.</div>
        ) : (
          items.map((item) => {
            const targetUrl = item.pdf_url || item.detail_url;

            return (
              <a
                key={item.id}
                href={targetUrl ?? undefined}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan-400/40 hover:bg-white/[0.05]"
              >
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold text-slate-100">
                    {item.title}
                  </h3>

                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    <span>{item.source ?? "-"}</span>
                    {item.company_name && <span>· {item.company_name}</span>}
                    <span>· {formatDate(item.published_at)}</span>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  {item.ticker && <span className="terminal-badge">{item.ticker}</span>}
                  {item.report_type && (
                    <span className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs font-semibold text-slate-300">
                      {item.report_type}
                    </span>
                  )}
                </div>
              </a>
            );
          })
        )}
      </div>
    </section>
  );
}

function HeatmapPanel({ items }: { items: MarketDashboardItem[] }) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="terminal-section-title">Market Heatmap</h2>
          <p className="terminal-section-subtitle">
            Tracked companies grouped by daily movement.
          </p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-sm text-slate-400">No heatmap data available.</div>
      ) : (
        <div className="grid min-h-[220px] grid-cols-2 gap-3 md:grid-cols-3">
          {items.map((item) => {
            const positive = (item.change_pct ?? 0) >= 0;

            return (
              <Link
                key={item.ticker}
                to={`/companies/${item.ticker}`}
                className={
                  positive
                    ? "flex min-h-24 flex-col justify-between rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 transition hover:border-emerald-300/50"
                    : "flex min-h-24 flex-col justify-between rounded-2xl border border-red-400/20 bg-red-400/10 p-4 transition hover:border-red-300/50"
                }
              >
                <div className="font-semibold text-slate-100">{item.ticker}</div>
                <div>
                  <div className="truncate text-xs text-slate-400">
                    {item.company_name}
                  </div>
                  <div
                    className={
                      positive
                        ? "mt-1 text-sm font-semibold text-emerald-300"
                        : "mt-1 text-sm font-semibold text-red-300"
                    }
                  >
                    {formatPercent(item.change_pct)}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </section>
  );
}

function MetricCard({
  title,
  value,
}: {
  title: string;
  value: number | undefined;
}) {
  return (
    <div className="terminal-card group relative overflow-hidden p-5">
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-cyan-400/10 blur-2xl transition group-hover:bg-cyan-400/20" />

      <div className="relative">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {title}
        </div>

        <div className="mt-4 text-4xl font-semibold tracking-tight text-slate-100">
          {value ?? 0}
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow shadow-cyan-300/60" />
          <span>Platform dataset</span>
        </div>
      </div>
    </div>
  );
}

function LatestCrawlRunsPanel({ runs }: { runs: CrawlRun[] }) {
  return (
    <section className="terminal-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="terminal-section-title">Platform Operations</h2>
          <p className="terminal-section-subtitle">
            Recent crawler jobs and insertion results.
          </p>
        </div>

        <span className="terminal-badge">Live</span>
      </div>

      {runs.length === 0 ? (
        <div className="text-sm text-slate-400">No crawl runs yet.</div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/60 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Crawler</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Fetched</th>
                <th className="px-4 py-3">Inserted</th>
                <th className="px-4 py-3">Failed</th>
                <th className="px-4 py-3">Started</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/10">
              {runs.map((run) => (
                <tr key={run.id} className="bg-slate-900/20 transition hover:bg-white/[0.03]">
                  <td className="px-4 py-3 font-medium text-slate-200">
                    {run.crawler_name}
                  </td>
                  <td className="px-4 py-3 text-slate-300">{run.source}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-300">{run.items_fetched}</td>
                  <td className="px-4 py-3 text-slate-300">{run.items_inserted}</td>
                  <td className="px-4 py-3 text-slate-300">{run.items_failed}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status?.toLowerCase();

  if (normalized === "success") {
    return (
      <span className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-xs font-semibold text-emerald-300">
        success
      </span>
    );
  }

  if (normalized === "failed" || normalized === "error") {
    return (
      <span className="rounded-lg border border-red-400/20 bg-red-400/10 px-2 py-1 text-xs font-semibold text-red-300">
        {status}
      </span>
    );
  }

  return (
    <span className="rounded-lg border border-cyan-400/20 bg-cyan-400/10 px-2 py-1 text-xs font-semibold text-cyan-300">
      {status}
    </span>
  );
}

function MiniSparkline({
  data,
  positive,
}: {
  data?: { date?: string | null; close?: number | null }[];
  positive: boolean;
}) {
  const points = (data ?? []).filter(
    (item): item is { date?: string | null; close: number } =>
      typeof item.close === "number"
  );

  if (points.length < 2) {
    return (
      <div className="flex h-full items-center text-xs text-slate-500">
        No price data
      </div>
    );
  }

  const width = 120;
  const height = 32;
  const padding = 3;

  const values = points.map((point) => point.close);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const path = points
    .map((point, index) => {
      const x =
        padding +
        (index / (points.length - 1)) * (width - padding * 2);

      const y =
        height -
        padding -
        ((point.close - min) / range) * (height - padding * 2);

      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  const areaPath = `${path} L ${width - padding} ${height - padding} L ${padding} ${height - padding
    } Z`;

  const strokeColor = positive ? "#22c55e" : "#fb7185";
  const fillColor = positive ? "rgba(34, 197, 94, 0.12)" : "rgba(251, 113, 133, 0.12)";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-full w-full overflow-visible"
      preserveAspectRatio="none"
    >
      <path d={areaPath} fill={fillColor} />
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function formatMoney(value?: number | null, currency?: string | null) {
  if (value == null) {
    return "-";
  }

  const prefix = currency ? `${currency} ` : "";
  return `${prefix}${value.toFixed(2)}`;
}

function formatSignedNumber(value?: number | null) {
  if (value == null) {
    return "-";
  }

  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

function formatPercent(value?: number | null) {
  if (value == null) {
    return "-";
  }

  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatChange(change?: number | null, changePct?: number | null) {
  if (change == null || changePct == null) {
    return "-";
  }

  return `${formatSignedNumber(change)} (${formatPercent(changePct)})`;
}

function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleDateString();
}

function formatTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}