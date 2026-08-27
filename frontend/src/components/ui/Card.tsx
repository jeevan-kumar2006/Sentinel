import { ReactNode } from 'react';

export default function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg ${className}`}>
      {children}
    </div>
  );
}