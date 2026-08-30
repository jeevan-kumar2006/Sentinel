export default function RiskBar({ score, decision }: { score: number; decision: string }) {
  const colorClass = decision === 'BLOCK' ? 'bg-rose-500' : decision === 'REVIEW' ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="flex items-center gap-2 w-32">
      <div className="h-2 w-full rounded-full bg-slate-700 overflow-hidden">
        <div
          className={`h-2 rounded-full ${colorClass}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-300">{score.toFixed(1)}</span>
    </div>
  );
}