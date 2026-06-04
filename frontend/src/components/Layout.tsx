import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function Layout() {
    return (
        <div className="terminal-shell">
            <div className="flex min-h-screen">
                <Navbar />

                <div className="flex min-w-0 flex-1 flex-col">
                    <header className="terminal-topbar sticky top-0 z-20">
                        <div className="flex h-16 items-center justify-between gap-4 px-6">
                            <div className="hidden min-w-0 flex-1 md:block">
                                <div className="mx-auto max-w-3xl">
                                    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-slate-400 shadow-lg shadow-black/20">
                                        <span className="text-slate-500">⌕</span>
                                        <input
                                            readOnly
                                            placeholder="Global search coming soon..."
                                            className="min-w-0 flex-1 bg-transparent text-slate-200 outline-none placeholder:text-slate-500"
                                        />
                                        <span className="hidden rounded-md border border-white/10 px-2 py-0.5 text-xs text-slate-500 lg:inline">
                                            Ctrl K
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="ml-auto flex items-center gap-3">
                                <button
                                    type="button"
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