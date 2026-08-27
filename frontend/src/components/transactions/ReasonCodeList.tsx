import { ReasonCode } from '../../types/api';
import { ShieldAlert } from 'lucide-react';

export default function ReasonCodeList({ reasons }: { reasons: ReasonCode[] }) {
  return (
    <div className="space-y-3">
      {reasons.map((reason, idx) => (
        <div key={idx} className="flex items-start gap-3 bg-slate-900 p-3 rounded-lg border border-slate-700">
          <ShieldAlert size={18} className="text-amber-400 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-slate-200">{reason.code}</p>
            <p className="text-xs text-slate-400">{reason.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}