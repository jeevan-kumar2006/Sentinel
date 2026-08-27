import { useState, useEffect } from 'react';
import { getHealth } from '../../services/api';
import { Activity, Wifi, WifiOff } from 'lucide-react';

export default function Header() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await getHealth();
        setIsHealthy(true);
      } catch {
        setIsHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 p-4 flex justify-between items-center">
      <div className="md:hidden">
        <h1 className="text-lg font-bold text-emerald-400">SENTINEL</h1>
      </div>
      <div className="hidden md:block">
        <p className="text-sm text-slate-400">Cost-Aware AI Risk Intelligence</p>
      </div>
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
        {isHealthy === null ? (
          <Activity className="text-slate-400 animate-pulse" size={16} />
        ) : isHealthy ? (
          <Wifi className="text-emerald-400" size={16} />
        ) : (
          <WifiOff className="text-rose-400" size={16} />
        )}
        <span className={`text-xs font-medium ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isHealthy === null ? 'Checking' : isHealthy ? 'API Online' : 'API Offline'}
        </span>
      </div>
    </header>
  );
}