export default function Badge({ decision }: { decision: string }) {
  const colors: Record<string, string> = {
    ALLOW: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    REVIEW: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    BLOCK: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  };

  return (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${colors[decision] || colors.ALLOW}`}>
      {decision}
    </span>
  );
}