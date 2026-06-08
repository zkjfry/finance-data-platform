import { Link, NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: "⌘" },
  { to: "/markets", label: "Markets", icon: "▦" },
  { to: "/companies", label: "Companies", icon: "◇" },
  { to: "/news", label: "News", icon: "▤" },
  { to: "/reports", label: "Reports", icon: "□" },
];

export function Navbar() {
  return (
    <aside className="terminal-sidebar sticky top-0 hidden h-screen w-64 shrink-0 flex-col px-4 py-5 lg:flex">
      <Link to="/" className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20">
          FT
        </div>

        <div>
          <div className="text-sm font-semibold tracking-wide text-slate-100">
            Finance Terminal
          </div>
          <div className="text-xs text-slate-500">
            Market Intelligence
          </div>
        </div>
      </Link>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              [
                "group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition",
                isActive
                  ? "bg-gradient-to-r from-cyan-500/20 to-violet-500/20 text-cyan-300 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-400/30"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100",
              ].join(" ")
            }
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-xs text-slate-300 group-hover:border-cyan-400/40 group-hover:text-cyan-300">
              {item.icon}
            </span>

            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-2xl border border-white/10 bg-white/[0.03] p-4">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Platform Status
        </div>

        <div className="mt-3 flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50" />
          <span className="text-sm text-slate-300">API Connected</span>
        </div>

        <div className="mt-3 text-xs leading-5 text-slate-500">
          Research data, prices, news and reports are available.
        </div>
      </div>
    </aside>
  );
}