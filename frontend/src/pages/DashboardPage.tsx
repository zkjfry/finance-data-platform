import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary } from "../api/dashboard";
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

  if (error) {
    return <StateBlock type="error" message="Failed to load dashboard summary." />;
  }

  const counts = data?.counts ?? {};
  const latestRuns = data?.latest_crawl_runs ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your finance data platform."
      />

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Companies" value={counts.companies} variant="gradient" />
        <MetricCard title="News" value={counts.news_articles} variant="gradient" />
        <MetricCard title="Reports" value={counts.research_reports} variant="gradient" />
        <MetricCard title="Prices" value={counts.market_prices} variant="gradient" />
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Securities" value={counts.securities} />
        <MetricCard title="Document Links" value={counts.document_company_links} />
        <MetricCard title="Accepted Links" value={counts.accepted_document_links} />
        <MetricCard title="Pending Links" value={counts.pending_document_links} />
      </section>

      <section className="terminal-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">
              Latest Crawl Runs
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Recent data collection jobs and insertion results.
            </p>
          </div>

          <span className="terminal-badge">
            Live
          </span>
        </div>

        {latestRuns.length === 0 ? (
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
                {latestRuns.map((run) => (
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
    </div>
  );
}

function MetricCard({
  title,
  value,
  variant = "default",
}: {
  title: string;
  value: number | undefined;
  variant?: "default" | "gradient";
}) {
  const className =
    variant === "gradient"
      ? "terminal-gradient-card p-5"
      : "terminal-card p-5";

  return (
    <div className={className}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {title}
      </div>

      <div className="mt-3 text-3xl font-semibold text-slate-100">
        {value ?? 0}
      </div>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-950/60">
        <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-cyan-400 to-violet-500" />
      </div>
    </div>
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