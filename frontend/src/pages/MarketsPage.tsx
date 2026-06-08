import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getMarketSecurities,
  type MarketSecuritiesParams,
  type MarketSecurity,
} from "../api/markets";
import { PageHeader } from "../components/ui/PageHeader";
import { StateBlock } from "../components/ui/StateBlock";

const PAGE_SIZE = 100;

type SortBy = NonNullable<MarketSecuritiesParams["sort_by"]>;
type SortDir = NonNullable<MarketSecuritiesParams["sort_dir"]>;

export function MarketsPage() {
  const [keyword, setKeyword] = useState("");
  const [sector, setSector] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("ticker");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const queryParams = useMemo<MarketSecuritiesParams>(
    () => ({
      keyword: keyword.trim() || undefined,
      sector: sector.trim() || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      limit: PAGE_SIZE,
      offset: 0,
    }),
    [keyword, sector, sortBy, sortDir]
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["market-securities", queryParams],
    queryFn: () => getMarketSecurities(queryParams),
  });

  const rows = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  const sectors = useMemo(() => {
    const unique = new Set<string>();

    rows.forEach((row) => {
      if (row.sector) {
        unique.add(row.sector);
      }
    });

    return Array.from(unique).sort();
  }, [rows]);

  function toggleSort(nextSortBy: SortBy) {
    if (sortBy === nextSortBy) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setSortBy(nextSortBy);
    setSortDir(nextSortBy === "ticker" || nextSortBy === "company_name" ? "asc" : "desc");
  }

  function clearFilters() {
    setKeyword("");
    setSector("");
    setSortBy("ticker");
    setSortDir("asc");
  }

  const gainers = rows.filter((row) => (row.change_pct ?? 0) > 0).length;
  const decliners = rows.filter((row) => (row.change_pct ?? 0) < 0).length;
  const flat = rows.length - gainers - decliners;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Markets"
        description="Tracked securities with latest close, daily movement, sector and exchange data."
      />

      <section className="grid gap-4 md:grid-cols-4">
        <SummaryCard title="Tracked" value={total} helper="Primary securities" />
        <SummaryCard title="Gainers" value={gainers} helper="Positive daily move" tone="positive" />
        <SummaryCard title="Decliners" value={decliners} helper="Negative daily move" tone="negative" />
        <SummaryCard title="Flat / N.A." value={flat} helper="No movement data" />
      </section>

      <section className="terminal-panel p-5">
        <div className="mb-5 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h2 className="terminal-section-title">Security Universe</h2>
            <p className="terminal-section-subtitle">
              Browse all tracked tickers and open company detail pages.
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-[minmax(220px,1fr)_180px_180px_auto]">
            <label className="block">
              <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-500">
                Search
              </span>
              <input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="Ticker or company..."
                className="terminal-input w-full"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-500">
                Sector
              </span>
              <select
                value={sector}
                onChange={(event) => setSector(event.target.value)}
                className="terminal-input w-full"
              >
                <option value="">All sectors</option>
                {sectors.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-500">
                Sort
              </span>
              <select
                value={`${sortBy}:${sortDir}`}
                onChange={(event) => {
                  const [nextSortBy, nextSortDir] = event.target.value.split(":");
                  setSortBy(nextSortBy as SortBy);
                  setSortDir(nextSortDir as SortDir);
                }}
                className="terminal-input w-full"
              >
                <option value="ticker:asc">Ticker A-Z</option>
                <option value="company_name:asc">Company A-Z</option>
                <option value="change_pct:desc">Top Gainers</option>
                <option value="change_pct:asc">Top Decliners</option>
                <option value="close:desc">Price High-Low</option>
                <option value="volume:desc">Volume High-Low</option>
              </select>
            </label>

            <button
              type="button"
              onClick={clearFilters}
              className="terminal-button-secondary self-end"
            >
              Clear
            </button>
          </div>
        </div>

        {isLoading ? (
          <StateBlock type="loading" message="Loading market securities..." />
        ) : error ? (
          <StateBlock type="error" message="Failed to load market securities." />
        ) : rows.length === 0 ? (
          <StateBlock type="empty" message="No securities matched your filters." />
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-white/10">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="bg-slate-950/60 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <SortableHeader
                    label="Ticker"
                    active={sortBy === "ticker"}
                    dir={sortDir}
                    onClick={() => toggleSort("ticker")}
                  />
                  <SortableHeader
                    label="Company"
                    active={sortBy === "company_name"}
                    dir={sortDir}
                    onClick={() => toggleSort("company_name")}
                  />
                  <th className="px-4 py-3">Sector</th>
                  <th className="px-4 py-3">Exchange</th>
                  <th className="px-4 py-3">Currency</th>
                  <SortableHeader
                    label="Close"
                    active={sortBy === "close"}
                    dir={sortDir}
                    onClick={() => toggleSort("close")}
                    align="right"
                  />
                  <th className="px-4 py-3 text-right">Change</th>
                  <SortableHeader
                    label="% Change"
                    active={sortBy === "change_pct"}
                    dir={sortDir}
                    onClick={() => toggleSort("change_pct")}
                    align="right"
                  />
                  <SortableHeader
                    label="Volume"
                    active={sortBy === "volume"}
                    dir={sortDir}
                    onClick={() => toggleSort("volume")}
                    align="right"
                  />
                  <th className="px-4 py-3 text-right">Date</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-white/10">
                {rows.map((row) => (
                  <MarketRow key={row.ticker} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  helper,
  tone = "neutral",
}: {
  title: string;
  value: number;
  helper: string;
  tone?: "neutral" | "positive" | "negative";
}) {
  const dotClass =
    tone === "positive"
      ? "bg-emerald-300 shadow-emerald-300/60"
      : tone === "negative"
        ? "bg-red-300 shadow-red-300/60"
        : "bg-cyan-300 shadow-cyan-300/60";

  return (
    <div className="terminal-card p-5">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {title}
      </div>

      <div className="mt-4 text-3xl font-semibold tracking-tight text-slate-100">
        {value}
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
        <span className={`h-1.5 w-1.5 rounded-full shadow ${dotClass}`} />
        <span>{helper}</span>
      </div>
    </div>
  );
}

function MarketRow({ row }: { row: MarketSecurity }) {
  const positive = (row.change_pct ?? 0) >= 0;

  return (
    <tr className="bg-slate-900/20 transition hover:bg-white/[0.03]">
      <td className="px-4 py-3">
        <Link
          to={`/companies/${row.ticker}`}
          className="font-semibold text-cyan-300 hover:text-cyan-200"
        >
          {row.ticker}
        </Link>
      </td>

      <td className="px-4 py-3">
        <div className="font-medium text-slate-200">{row.company_name}</div>
        <div className="mt-1 text-xs text-slate-500">
          {row.industry ?? "No industry"}
        </div>
      </td>

      <td className="px-4 py-3 text-slate-300">
        {row.sector ?? "-"}
      </td>

      <td className="px-4 py-3 text-slate-300">
        {row.exchange ?? "-"}
      </td>

      <td className="px-4 py-3 text-slate-300">
        {row.currency ?? "-"}
      </td>

      <td className="px-4 py-3 text-right text-slate-200">
        {formatMoney(row.close, row.currency)}
      </td>

      <td className={positive ? "px-4 py-3 text-right text-emerald-300" : "px-4 py-3 text-right text-red-300"}>
        {formatSignedNumber(row.change)}
      </td>

      <td className={positive ? "px-4 py-3 text-right font-medium text-emerald-300" : "px-4 py-3 text-right font-medium text-red-300"}>
        {formatPercent(row.change_pct)}
      </td>

      <td className="px-4 py-3 text-right text-slate-300">
        {formatVolume(row.volume)}
      </td>

      <td className="px-4 py-3 text-right text-slate-400">
        {formatDate(row.price_date)}
      </td>
    </tr>
  );
}

function SortableHeader({
  label,
  active,
  dir,
  onClick,
  align = "left",
}: {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  align?: "left" | "right";
}) {
  return (
    <th className={align === "right" ? "px-4 py-3 text-right" : "px-4 py-3"}>
      <button
        type="button"
        onClick={onClick}
        className={
          active
            ? "inline-flex items-center gap-1 text-cyan-300"
            : "inline-flex items-center gap-1 text-slate-500 hover:text-slate-300"
        }
      >
        {label}
        <span className="text-[10px]">
          {active ? (dir === "asc" ? "▲" : "▼") : "↕"}
        </span>
      </button>
    </th>
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

function formatVolume(value?: number | null) {
  if (value == null) {
    return "-";
  }

  return Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleDateString();
}