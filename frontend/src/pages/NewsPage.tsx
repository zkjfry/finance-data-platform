import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchNews, type NewsArticle } from "../api/news";
import { PageHeader } from "../components/ui/PageHeader";
import { StateBlock } from "../components/ui/StateBlock";
import { Pagination } from "../components/ui/Pagination";
import { FilterBadge } from "../components/ui/FilterBadge";
import { TerminalCard } from "../components/ui/TerminalCard";

const PAGE_SIZE = 20;

export function NewsPage() {
    const [keyword, setKeyword] = useState("");
    const [symbol, setSymbol] = useState("");

    const [submittedKeyword, setSubmittedKeyword] = useState("");
    const [submittedSymbol, setSubmittedSymbol] = useState("");

    const [offset, setOffset] = useState(0);

    const normalizedKeyword = submittedKeyword.trim();
    const normalizedSymbol = submittedSymbol.trim().toUpperCase();

    const { data, isLoading, isFetching, error } = useQuery({
        queryKey: ["news", normalizedKeyword, normalizedSymbol, offset],
        queryFn: () =>
            searchNews({
                keyword: normalizedKeyword,
                symbol: normalizedSymbol,
                limit: PAGE_SIZE,
                offset,
            }),
    });

    const articles = data?.data ?? [];
    const total = data?.meta?.total ?? 0;

    const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

    const canGoPrevious = offset > 0;
    const canGoNext = offset + PAGE_SIZE < total;

    const hasFilter = normalizedKeyword.length > 0 || normalizedSymbol.length > 0;

    const hasDraftFilter =
        keyword.length > 0 ||
        symbol.length > 0 ||
        submittedKeyword.length > 0 ||
        submittedSymbol.length > 0 ||
        offset > 0;

    function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();

        setSubmittedKeyword(keyword.trim());
        setSubmittedSymbol(symbol.trim().toUpperCase());
        setOffset(0);
    }

    function handleClear() {
        setKeyword("");
        setSymbol("");
        setSubmittedKeyword("");
        setSubmittedSymbol("");
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
                title="News"
                description="Browse latest financial news or search by keyword and ticker."
            />

            <form
                onSubmit={handleSubmit}
                className="terminal-panel grid gap-3 p-4 md:grid-cols-[1fr_180px_auto_auto]"
            >
                <input
                    value={keyword}
                    onChange={(event) => setKeyword(event.target.value)}
                    placeholder="Search keyword, e.g. earnings, AI, iPhone..."
                    className="terminal-input min-w-0"
                />

                <input
                    value={symbol}
                    onChange={(event) => setSymbol(event.target.value)}
                    placeholder="Ticker, e.g. AAPL"
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

            <div className="terminal-panel flex flex-col justify-between gap-2 p-4 text-sm text-slate-400 md:flex-row md:items-center">
                <div>
                    {hasFilter ? (
                        <span>
                            Filters:
                            {normalizedKeyword && (
                                <FilterBadge label="keyword" value={normalizedKeyword} />
                            )}
                            {normalizedSymbol && (
                                <FilterBadge label="symbol" value={normalizedSymbol} />
                            )}
                        </span>
                    ) : (
                        <span>Showing latest news</span>
                    )}
                </div>

                <div>
                    {total} result{total === 1 ? "" : "s"} · Page {currentPage} /{" "}
                    {totalPages}
                </div>
            </div>

            {isLoading && <StateBlock type="loading" message="Loading news..." />}

            {error && <StateBlock type="error" message="Failed to load news." />}

            {!isLoading && !error && articles.length === 0 && (
                <StateBlock type="empty" message="No news found." />
            )}

            {articles.length > 0 && (
                <section className="space-y-3">
                    {articles.map((article) => (
                        <NewsCard key={article.id} article={article} />
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

function NewsCard({ article }: { article: NewsArticle }) {
    return (
        <TerminalCard href={article.url}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                <div className="min-w-0">
                    <h2 className="text-base font-medium text-slate-100">
                        {article.title}
                    </h2>

                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <span>{article.source ?? "Unknown Source"}</span>
                        <span>·</span>
                        <span>
                            {article.published_at
                                ? formatDate(article.published_at)
                                : "Date unavailable"}
                        </span>

                        {article.authors && article.authors.length > 0 && (
                            <>
                                <span>·</span>
                                <span>{article.authors.join(", ")}</span>
                            </>
                        )}
                    </div>
                </div>

                {article.symbols && article.symbols.length > 0 && (
                    <div className="flex shrink-0 flex-wrap gap-2">
                        {article.symbols.map((symbol) => (
                            <span
                                key={symbol}
                                className="terminal-badge"
                            >
                                {symbol}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            <p className="mt-3 line-clamp-3 text-sm text-slate-400">
                {article.summary || article.body_text || "No summary available."}
            </p>

            {article.relevance != null && (
                <div className="mt-3 text-xs text-slate-500">
                    Relevance: {article.relevance.toFixed(4)}
                </div>
            )}
        </TerminalCard>
    );
}

function formatDate(value: string) {
    return new Date(value).toLocaleString();
}