type FilterBadgeProps = {
  label: string;
  value: string;
};

export function FilterBadge({ label, value }: FilterBadgeProps) {
  return (
    <span className="ml-2 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-slate-200">
      <span className="text-slate-500">{label}: </span>
      <span className="text-cyan-300">{value}</span>
    </span>
  );
}