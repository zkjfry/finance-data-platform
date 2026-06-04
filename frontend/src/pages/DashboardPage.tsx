import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary } from "../api/dashboard";

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  if (isLoading) {
    return <div className="text-slate-400">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="text-red-400">Failed to load dashboard summary.</div>;
  }

  const counts = data?.counts ?? {};
  const latestRuns = data?.latest_crawl_runs ?? [];

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">
          Overview of your finance data platform.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Companies" value={counts.companies} />
        <MetricCard title="News" value={counts.news_articles} />
        <MetricCard title="Reports" value={counts.research_reports} />
        <MetricCard title="Prices" value={counts.market_prices} />
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Securities" value={counts.securities} />
        <MetricCard title="Document Links" value={counts.document_company_links} />
        <MetricCard title="Accepted Links" value={counts.accepted_document_links} />
        <MetricCard title="Pending Links" value={counts.pending_document_links} />
      </section>

      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-lg font-medium">Latest Crawl Runs</h2>

        {latestRuns.length === 0 ? (
          <div className="text-sm text-slate-400">No crawl runs yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-400">
                <tr>
                  <th className="py-2">Crawler</th>
                  <th className="py-2">Source</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Fetched</th>
                  <th className="py-2">Inserted</th>
                  <th className="py-2">Failed</th>
                  <th className="py-2">Started</th>
                </tr>
              </thead>
              <tbody>
                {latestRuns.map((run: any) => (
                  <tr key={run.id} className="border-t border-slate-800">
                    <td className="py-2">{run.crawler_name}</td>
                    <td className="py-2 text-slate-300">{run.source}</td>
                    <td className="py-2">{run.status}</td>
                    <td className="py-2">{run.items_fetched}</td>
                    <td className="py-2">{run.items_inserted}</td>
                    <td className="py-2">{run.items_failed}</td>
                    <td className="py-2 text-slate-400">
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

function MetricCard({ title, value }: { title: string; value: number | undefined }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="text-sm text-slate-400">{title}</div>
      <div className="mt-2 text-2xl font-semibold">{value ?? 0}</div>
    </div>
  );
}