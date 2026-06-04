import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchReports, type ResearchReport } from "../api/reports";
import { PageHeader } from "../components/ui/PageHeader";
import { StateBlock } from "../components/ui/StateBlock";
import { Pagination } from "../components/ui/Pagination";
import { FilterBadge } from "../components/ui/FilterBadge";
import { TerminalCard } from "../components/ui/TerminalCard";

const PAGE_SIZE = 20;

export function ReportsPage() {
    const [keyword, setKeyword] = useState("");
    const [ticker, setTicker] = useState("");
    const [reportType, setReportType] = useState("");

    const [submittedKeyword, setSubmittedKeyword] = useState("");
    const [submittedTicker, setSubmittedTicker] = useState("");
    const [submittedReportType, setSubmittedReportType] = useState("");

    const [offset, setOffset] = useState(0);

    const normalizedKeyword = submittedKeyword.trim();
    const normalizedTicker = submittedTicker.trim().toUpperCase();
    const normalizedReportType = submittedReportType.trim();

    const { data, isLoading, isFetching, error } = useQuery({
        queryKey: [
            "reports",
            normalizedKeyword,
            normalizedTicker,
            normalizedReportType,
            offset,
        ],
        queryFn: () =>
            searchReports({
                keyword: normalizedKeyword,
                ticker: normalizedTicker,
                report_type: normalizedReportType,
                limit: PAGE_SIZE,
                offset,
            }),
    });

    const reports = data?.data ?? [];
    const total = data?.meta?.total ?? 0;

    const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

    const canGoPrevious = offset > 0;
    const canGoNext = offset + PAGE_SIZE < total;

    const hasFilter =
        normalizedKeyword.length > 0 ||
        normalizedTicker.length > 0 ||
        normalizedReportType.length > 0;

    const hasDraftFilter =
        keyword.length > 0 ||
        ticker.length > 0 ||
        reportType.length > 0 ||
        hasFilter ||
        offset > 0;

    function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();

        setSubmittedKeyword(keyword.trim());
        setSubmittedTicker(ticker.trim().toUpperCase());
        setSubmittedReportType(reportType.trim());
        setOffset(0);
    }

    function handleClear() {
        setKeyword("");
        setTicker("");
        setReportType("");

        setSubmittedKeyword("");
        setSubmittedTicker("");
        setSubmittedReportType("");

        setOffset(0);
    }

    function handlePreviousPage() {
        if (!canGoPrevious) {
            return;
        }

        setOffset((value) => Math.max(0, value - PAGE_SIZE));
    }

    function handleNextPage() {
        if (!canGoNext) {
            return;
        }

        setOffset((value) => value + PAGE_SIZE);
    }

    return (
        <div className="space-y-6">
            <PageHeader
                title="Reports"
                description="Browse filings and research reports, or filter by keyword, ticker, and report type."
            />

            <form
                onSubmit={handleSubmit}
                className="terminal-panel grid gap-3 p-4 md:grid-cols-[1fr_160px_160px_auto_auto]"
            >
                <input
                    value={keyword}
                    onChange={(event) => setKeyword(event.target.value)}
                    placeholder="Search keyword, e.g. annual, revenue, risk..."
                    className="terminal-input min-w-0"
                />

                <input
                    value={ticker}
                    onChange={(event) => setTicker(event.target.value)}
                    placeholder="Ticker, e.g. AAPL"
                    className="terminal-input min-w-0"
                />

                <input
                    value={reportType}
                    onChange={(event) => setReportType(event.target.value)}
                    placeholder="Type, e.g. 10-K"
                    className="terminal-input min-w-0"
                />

                <button
                    type="submit"
                    disabled={isFetching}
                    className="terminal-button-primary"
                    >
                    {isFetching ? "Loading..." : "Search"}
                </button>

                {hasDraftFilter && (
                    <button
                        type="button"
                        onClick={handleClear}
                        disabled={isFetching}
                        className="terminal-button-secondary"
                        >
                        Clear
                    </button>
                )}
            </form>

            <div className="flex flex-col justify-between gap-2 text-sm text-slate-400 md:flex-row md:items-center">
                <div>
                    {hasFilter ? (
                        <span>
                            Filters:
                            {normalizedKeyword && (
                                <FilterBadge label="keyword" value={normalizedKeyword} />
                            )}
                            {normalizedTicker && (
                                <FilterBadge label="ticker" value={normalizedTicker} />
                            )}
                            {normalizedReportType && (
                                <FilterBadge label="type" value={normalizedReportType} />
                            )}
                        </span>
                    ) : (
                        <span>Showing latest reports</span>
                    )}
                </div>

                <div>
                    {total} result{total === 1 ? "" : "s"} · Page {currentPage} /{" "}
                    {totalPages}
                </div>
            </div>

            {isLoading && <StateBlock type="loading" message="Loading reports..." />}

            {error && <StateBlock type="error" message="Failed to load reports." />}

            {!isLoading && !error && reports.length === 0 && (
                <StateBlock type="empty" message="No reports found." />
            )}

            {reports.length > 0 && (
                <section className="space-y-3">
                    {reports.map((report) => (
                        <ReportCard key={report.id} report={report} />
                    ))}
                </section>
            )}

            {total > PAGE_SIZE && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    total={total}
                    canGoPrevious={canGoPrevious}
                    canGoNext={canGoNext}
                    isLoading={isFetching}
                    onPrevious={handlePreviousPage}
                    onNext={handleNextPage}
                />
            )}
        </div>
    );
}

function ReportCard({ report }: { report: ResearchReport }) {
    const targetUrl = report.pdf_url || report.detail_url;

    return (
        <TerminalCard href={targetUrl}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                <div className="min-w-0">
                    <h2 className="text-base font-medium text-slate-100">
                        {report.title}
                    </h2>

                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <span>{report.source ?? "Unknown Source"}</span>

                        {report.company_name && (
                            <>
                                <span>·</span>
                                <span>{report.company_name}</span>
                            </>
                        )}

                        <span>·</span>

                        <span>
                            {report.published_at
                                ? formatDate(report.published_at)
                                : "Date unavailable"}
                        </span>

                        {report.authors && report.authors.length > 0 && (
                            <>
                                <span>·</span>
                                <span>{report.authors.join(", ")}</span>
                            </>
                        )}
                    </div>
                </div>

                <div className="flex shrink-0 flex-wrap gap-2">
                    {report.ticker && (
                        <span className="terminal-badge">
                            {report.ticker}
                        </span>
                    )}

                    {report.report_type && (
                        <span className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs font-semibold text-slate-300">
                            {report.report_type}
                        </span>
                    )}

                    {report.pdf_url && (
                        <span className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 text-xs font-semibold text-emerald-300">
                            PDF
                        </span>
                    )}
                </div>
            </div>

            <p className="mt-3 line-clamp-3 text-sm text-slate-400">
                {report.summary || report.body_text || "No summary available."}
            </p>

            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                {targetUrl ? (
                    <span className="text-cyan-400">
                        Click to open {report.pdf_url ? "PDF" : "detail page"}
                    </span>
                ) : (
                    <span>No external URL available</span>
                )}

                {report.relevance != null && (
                    <span>Relevance: {report.relevance.toFixed(4)}</span>
                )}
            </div>
        </TerminalCard>
    );
}

function formatDate(value: string) {
    return new Date(value).toLocaleString();
}