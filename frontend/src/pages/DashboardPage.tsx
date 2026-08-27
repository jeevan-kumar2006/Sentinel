import { useState, useEffect } from 'react';
import { getDashboardSummary, getHealth } from '../services/api';
import { SummaryResponse, HealthResponse } from '../types/api';
import MetricCard from '../components/ui/MetricCard';
import Card from '../components/ui/Card';
import RoutingChart from '../components/charts/RoutingChart';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import { ShieldCheck, TrendingUp, Target, IndianRupee } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercent } from '../utils/format';

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumData, healthData] = await Promise.all([getDashboardSummary(), getHealth()]);
        setSummary(sumData);
        setHealth(healthData);
      } catch (err) {
        setError("Failed to load dashboard data. Check that FastAPI is running on http://127.0.0.1:8000");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Fetching risk intelligence..." />;
  if (error || !summary || !health) return <ErrorState message={error || "Unknown error"} />;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Sentinel Risk Control Center</h2>
        <p className="text-slate-400 mt-1">Cost-Aware AI Risk Intelligence</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Net Economic Impact" 
          value={formatCurrency(summary.net_economic_impact_inr)} 
          icon={<IndianRupee size={20} />} 
          accent="emerald" 
        />
        <MetricCard 
          title="Precision" 
          value={formatPercent(summary.precision)} 
          icon={<Target size={20} />} 
          accent="slate" 
        />
        <MetricCard 
          title="Recall" 
          value={formatPercent(summary.recall)} 
          icon={<TrendingUp size={20} />} 
          accent="slate" 
        />
        <MetricCard 
          title="Fraud Detected" 
          value={formatNumber(summary.fraud_detected)} 
          icon={<ShieldCheck size={20} />} 
          accent="rose" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Routing Distribution</h3>
          <RoutingChart data={summary.routing_counts} />
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Economic Story (Held-out Test)</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b border-slate-700 pb-3">
              <span className="text-slate-400">Baseline Fraud Loss</span>
              <span className="text-rose-400 font-semibold">{formatCurrency(summary.baseline_fraud_loss_inr)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-700 pb-3">
              <span className="text-slate-400">Sentinel Protection (Prevented)</span>
              <span className="text-emerald-400 font-semibold">{formatCurrency(summary.fraud_loss_prevented_inr)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-700 pb-3">
              <span className="text-slate-400">Residual Fraud Loss</span>
              <span className="text-amber-400 font-semibold">{formatCurrency(summary.residual_fraud_loss_inr)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-700 pb-3">
              <span className="text-slate-400">False Positive Cost</span>
              <span className="text-rose-400 font-semibold">{formatCurrency(summary.false_positive_cost_inr)}</span>
            </div>
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-300 font-bold">Net Economic Impact</span>
              <span className="text-emerald-400 font-bold text-lg">{formatCurrency(summary.net_economic_impact_inr)}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}