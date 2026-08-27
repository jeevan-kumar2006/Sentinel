import { ReactNode } from 'react';
import Card from './Card';

export default function MetricCard({ title, value, icon, accent = 'slate' }: { title: string; value: ReactNode; icon?: ReactNode; accent?: string }) {
  const accentClasses: Record<string, string> = {
    emerald: 'text-emerald-400',
    rose: 'text-rose-400',
    amber: 'text-amber-400',
    slate: 'text-slate-400'
  };

  return (
    <Card>
      <div className="flex justify-between items-start mb-4">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
        {icon && <div className={accentClasses[accent]}>{icon}</div>}
      </div>
      <div className={`text-2xl font-bold ${accentClasses[accent]}`}>{value}</div>
    </Card>
  );
}