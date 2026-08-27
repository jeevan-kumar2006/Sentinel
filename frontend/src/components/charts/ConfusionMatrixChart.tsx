export default function ConfusionMatrixChart({ data }: { data: { tn: number; fp: number; fn: number; tp: number } }) {
  return (
    <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
      <div className="bg-slate-900 p-4 rounded-lg text-center border border-slate-700">
        <p className="text-xs text-slate-500 mb-1">True Negative</p>
        <p className="text-2xl font-bold text-emerald-400">{data.tn}</p>
      </div>
      <div className="bg-slate-900 p-4 rounded-lg text-center border border-slate-700">
        <p className="text-xs text-slate-500 mb-1">False Positive</p>
        <p className="text-2xl font-bold text-amber-400">{data.fp}</p>
      </div>
      <div className="bg-slate-900 p-4 rounded-lg text-center border border-slate-700">
        <p className="text-xs text-slate-500 mb-1">False Negative</p>
        <p className="text-2xl font-bold text-rose-400">{data.fn}</p>
      </div>
      <div className="bg-slate-900 p-4 rounded-lg text-center border border-slate-700">
        <p className="text-xs text-slate-500 mb-1">True Positive</p>
        <p className="text-2xl font-bold text-emerald-400">{data.tp}</p>
      </div>
    </div>
  );
}