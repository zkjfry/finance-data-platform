import { useEffect, useRef, useState } from "react";
import type { SubmitEvent } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Navbar } from "./Navbar";

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    if (location.pathname === "/search") {
      const params = new URLSearchParams(location.search);
      setSearchText(params.get("q") ?? "");
    }
  }, [location.pathname, location.search]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const isSearchShortcut =
        (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";

      if (!isSearchShortcut) {
        return;
      }

      event.preventDefault();
      inputRef.current?.focus();
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  function handleSearchSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const keyword = searchText.trim();

    if (!keyword) {
      return;
    }

    navigate(`/search?q=${encodeURIComponent(keyword)}`);
  }

  return (
    <div className="terminal-shell">
      <div className="flex min-h-screen">
        <Navbar />

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="terminal-topbar sticky top-0 z-20">
            <div className="flex h-16 items-center justify-between gap-4 px-6">
              <div className="hidden min-w-0 flex-1 md:block">
                <div className="mx-auto max-w-3xl">
                  <form
                    onSubmit={handleSearchSubmit}
                    className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-slate-400 shadow-lg shadow-black/20 transition focus-within:border-cyan-400/50 focus-within:text-cyan-300"
                  >
                    <span className="text-slate-500">⌕</span>

                    <input
                      ref={inputRef}
                      value={searchText}
                      onChange={(event) => setSearchText(event.target.value)}
                      placeholder="Search companies, news, reports..."
                      className="min-w-0 flex-1 bg-transparent text-slate-200 outline-none placeholder:text-slate-500"
                    />

                    <button
                      type="submit"
                      className="hidden rounded-md border border-white/10 px-2 py-0.5 text-xs text-slate-500 transition hover:border-cyan-400/40 hover:text-cyan-300 lg:inline"
                    >
                      Enter
                    </button>

                    <span className="hidden rounded-md border border-white/10 px-2 py-0.5 text-xs text-slate-500 lg:inline">
                      Ctrl K
                    </span>
                  </form>
                </div>
              </div>

              <div className="ml-auto flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition hover:border-cyan-400/50 hover:text-cyan-300"
                  title="Refresh"
                >
                  ↻
                </button>

                <button
                  type="button"
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition hover:border-cyan-400/50 hover:text-cyan-300"
                  title="Settings"
                >
                  ⚙
                </button>

                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 text-sm font-bold text-slate-950">
                  F
                </div>
              </div>
            </div>
          </header>

          <main className="mx-auto w-full max-w-7xl px-6 py-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}