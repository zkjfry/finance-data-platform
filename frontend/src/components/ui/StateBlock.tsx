type StateBlockProps = {
  type?: "loading" | "error" | "empty" | "info";
  message: string;
};

export function StateBlock({ type = "info", message }: StateBlockProps) {
  if (type === "error") {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-950/30 p-4 text-sm text-red-300 shadow-xl shadow-black/20 backdrop-blur-xl">
        {message}
      </div>
    );
  }

  return (
    <div className="terminal-panel p-4 text-sm text-slate-400">
      {message}
    </div>
  );
}