type PaginationProps = {
  currentPage: number;
  totalPages: number;
  total: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
  isLoading?: boolean;
  onPrevious: () => void;
  onNext: () => void;
};

export function Pagination({
  currentPage,
  totalPages,
  total,
  canGoPrevious,
  canGoNext,
  isLoading = false,
  onPrevious,
  onNext,
}: PaginationProps) {
  return (
    <div className="terminal-panel flex flex-col items-start justify-between gap-3 p-4 text-sm text-slate-400 md:flex-row md:items-center">
      <div>
        {total} result{total === 1 ? "" : "s"} · Page {currentPage} /{" "}
        {totalPages}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onPrevious}
            disabled={!canGoPrevious || isLoading}
            className="terminal-button-secondary"
          >
            Previous
          </button>

          <button
            type="button"
            onClick={onNext}
            disabled={!canGoNext || isLoading}
            className="terminal-button-secondary"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}