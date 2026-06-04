import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { StateBlock } from "../components/ui/StateBlock";
import {
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
    CartesianGrid,
} from "recharts";
import {
    getCompanyOverview,
    type CompanyLinkedNews,
    type CompanyLinkedReport,
    type MarketPrice,
} from "../api/companies";

export function CompanyDetailPage() {
    const navigate = useNavigate();
    const { ticker } = useParams();

    const tickerOrAlias = ticker ?? "";

    const { data, isLoading, error } = useQuery({
        queryKey: ["company-overview", tickerOrAlias],
        queryFn: () => getCompanyOverview(tickerOrAlias),
        enabled: tickerOrAlias.length > 0,
    });

    if (isLoading) {
        return <StateBlock type="loading" message="Loading company detail..." />;
    }

    if (error || !data) {
        return (
            <div className="space-y-4">
                <StateBlock type="error" message="Failed to load company detail." />

                <Link
                    to="/companies"
                    className="text-sm text-cyan-400 transition hover:text-cyan-300"
                >
                    Back to company search
                </Link>
            </div>
        );
    }

    const company = data.company;
    const security = data.primary_security;
    const latestPrice = data.latest_price;
    const priceHistory = data.price_history ?? [];

    const displayTicker = security?.ticker ?? tickerOrAlias.toUpperCase();

    const previousPrice =
        priceHistory.length >= 2 ? priceHistory[priceHistory.length - 2] : null;

    const priceChange =
        latestPrice?.close != null && previousPrice?.close != null
            ? latestPrice.close - previousPrice.close
            : null;

    const priceChangePct =
        priceChange != null && previousPrice?.close
            ? (priceChange / previousPrice.close) * 100
            : null;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <button
                    type="button"
                    onClick={() => navigate(-1)}
                    className="terminal-button-secondary"
                >
                    ← Back
                </button>

                <Link
                    to="/companies"
                    className="text-sm text-slate-400 transition hover:text-cyan-300"
                >
                    Company Search
                </Link>
            </div>
            <section className="terminal-panel flex flex-col justify-between gap-4 p-5 md:flex-row md:items-start">
                <div>
                    <div className="flex flex-wrap items-center gap-3">
                        <h1 className="text-2xl font-semibold text-slate-100">
                            {company.canonical_name}
                        </h1>

                        <span className="terminal-badge">
                            {displayTicker}
                        </span>
                    </div>

                    <p className="mt-1 text-sm text-slate-400">
                        {company.legal_name ?? "No legal name available"}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                        {data.aliases.map((alias) => (
                            <span
                                key={alias}
                                className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-400"
                            >
                                {alias}
                            </span>
                        ))}
                    </div>
                </div>

                <div className="terminal-gradient-card min-w-[240px] p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">
                        Latest Close
                    </div>

                    <div className="mt-2 text-3xl font-semibold text-slate-100">
                        {formatMoney(latestPrice?.close, security?.currency)}
                    </div>

                    <div className={priceChange != null && priceChange >= 0 ? "mt-1 text-sm text-emerald-400" : "mt-1 text-sm text-red-400"}>
                        {priceChange == null
                            ? "Change unavailable"
                            : `${priceChange >= 0 ? "+" : ""}${priceChange.toFixed(2)} ${priceChangePct == null
                                ? ""
                                : `(${priceChangePct >= 0 ? "+" : ""}${priceChangePct.toFixed(2)}%)`
                            }`}
                    </div>

                    <div className="mt-2 text-xs text-slate-500">
                        {latestPrice?.price_date ? `As of ${formatDate(latestPrice.price_date)}` : "-"}
                    </div>
                </div>
            </section>

            <section className="grid gap-4 md:grid-cols-4">
                <InfoCard label="Exchange" value={security?.exchange} />
                <InfoCard label="Currency" value={security?.currency} />
                <InfoCard label="Sector" value={company.sector} />
                <InfoCard label="Industry" value={company.industry} />
            </section>

            <section className="terminal-panel p-5">
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-slate-100">
                            Price History
                        </h2>
                        <p className="text-sm text-slate-400">
                            Recent closing prices from the market_prices table.
                        </p>
                    </div>
                </div>

                {priceHistory.length === 0 ? (
                    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
                        No price history available.
                    </div>
                ) : (
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={toChartData(priceHistory)}>
                                <CartesianGrid
                                    stroke="rgba(148, 163, 184, 0.14)"
                                    strokeDasharray="4 6"
                                    vertical={false}
                                />

                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12, fill: "#64748b" }}
                                    axisLine={{ stroke: "rgba(148, 163, 184, 0.18)" }}
                                    tickLine={false}
                                />

                                <YAxis
                                    tick={{ fontSize: 12, fill: "#64748b" }}
                                    axisLine={false}
                                    tickLine={false}
                                    domain={["auto", "auto"]}
                                    tickFormatter={(value) => Number(value).toFixed(0)}
                                />

                                <Tooltip
                                    contentStyle={{
                                        background: "rgba(15, 23, 42, 0.96)",
                                        border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: "14px",
                                        color: "#e5e7eb",
                                    }}
                                    labelStyle={{ color: "#94a3b8" }}
                                    formatter={(value) => [Number(value).toFixed(2), "Close"]}
                                    labelFormatter={(label) => `Date: ${label}`}
                                />

                                <Line
                                    type="monotone"
                                    dataKey="close"
                                    dot={false}
                                    stroke="#38bdf8"
                                    strokeWidth={2.5}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </section>

            <section className="grid gap-6 xl:grid-cols-2">
                <div className="terminal-panel p-5">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold text-slate-100">
                                Linked News
                            </h2>
                            <p className="text-sm text-slate-400">
                                Accepted news links from document_company_links.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {data.latest_news.length === 0 ? (
                            <EmptyState message="No linked news available." />
                        ) : (
                            data.latest_news.map((news) => (
                                <NewsItem key={news.id} news={news} />
                            ))
                        )}
                    </div>
                </div>

                <div className="terminal-panel p-5">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold text-slate-100">
                                Linked Reports
                            </h2>
                            <p className="text-sm text-slate-400">
                                Accepted report links from document_company_links.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {data.latest_reports.length === 0 ? (
                            <EmptyState message="No linked reports available." />
                        ) : (
                            data.latest_reports.map((report) => (
                                <ReportItem key={report.id} report={report} />
                            ))
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

function InfoCard({ label, value }: { label: string; value?: string | null }) {
    return (
        <div className="terminal-card p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">
                {label}
            </div>
            <div className="mt-2 truncate text-sm font-medium text-slate-200">
                {value || "-"}
            </div>
        </div>
    );
}

function NewsItem({ news }: { news: CompanyLinkedNews }) {
    const content = (
        <div className="terminal-card p-4">
            <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-medium text-slate-100">
                    {news.title}
                </h3>
                <span className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-400">
                    {news.source ?? "-"}
                </span>
            </div>

            <p className="mt-2 line-clamp-2 text-sm text-slate-400">
                {news.summary || "No summary available."}
            </p>

            <div className="mt-3 text-xs text-slate-500">
                {news.published_at ? formatDate(news.published_at) : "Date unavailable"}
            </div>
        </div>
    );

    if (!news.url) {
        return content;
    }

    return (
        <a href={news.url} target="_blank" rel="noreferrer">
            {content}
        </a>
    );
}

function ReportItem({ report }: { report: CompanyLinkedReport }) {
    const targetUrl = report.pdf_url || report.detail_url;

    const content = (
        <div className="terminal-card p-4">
            <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-medium text-slate-100">
                    {report.title}
                </h3>
                <span className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-400">
                    {report.report_type ?? report.source ?? "-"}
                </span>
            </div>

            <p className="mt-2 line-clamp-2 text-sm text-slate-400">
                {report.summary || "No summary available."}
            </p>

            <div className="mt-3 text-xs text-slate-500">
                {report.published_at ? formatDate(report.published_at) : "Date unavailable"}
            </div>
        </div>
    );

    if (!targetUrl) {
        return content;
    }

    return (
        <a href={targetUrl} target="_blank" rel="noreferrer">
            {content}
        </a>
    );
}

function EmptyState({ message }: { message: string }) {
    return (
        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
            {message}
        </div>
    );
}

function toChartData(rows: MarketPrice[]) {
    return rows
        .filter((row) => row.close != null)
        .map((row) => ({
            date: shortDate(row.price_date),
            close: row.close,
        }));
}

function formatMoney(value?: number | null, currency?: string | null) {
    if (value == null) {
        return "-";
    }

    const prefix = currency ? `${currency} ` : "";

    return `${prefix}${value.toFixed(2)}`;
}

function formatDate(value: string) {
    return new Date(value).toLocaleDateString();
}

function shortDate(value: string) {
    const date = new Date(value);
    return `${date.getMonth() + 1}/${date.getDate()}`;
}