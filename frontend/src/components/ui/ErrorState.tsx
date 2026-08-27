import { AlertTriangle } from 'lucide-react';

export default function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertTriangle className="text-rose-400 mb-3" size={32} />
      <h3 className="text-lg font-semibold text-slate-200 mb-1">Sentinel API unavailable</h3>
      <p className="text-slate-500 text-sm max-w-md">{message}</p>
    </div>
  );
}