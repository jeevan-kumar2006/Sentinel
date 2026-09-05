import { useState, useEffect } from 'react';
import { getDashboardSummary, getHealth, getTransactions } from '../services/api';
import { SummaryResponse, HealthResponse, PaginatedTransactions } from '../types/api';
import MetricCard from '../components/ui/MetricCard';
import Card from '../components/ui/Card';
import RoutingChart from '../components/charts/RoutingChart';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Badge from '../components/ui/Badge';
import { ShieldCheck, TrendingDown, AlertTriangle, IndianRupee, ArrowRight } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercent } from '../utils/format';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [blockTxns, setBlockTxns] = useState<PaginatedTransactions | null>(null);
  const [reviewTxns, setReviewTxns] = useState<PaginatedTransactions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumData, healthData, blockData, reviewData] = await Promise.all([
          getDashboardSummary(), getHealth(),
          getTransactions({ page: 1, limit: 5, risk_decision: 'BLOCK' }),
          getTransactions({ page: 1, limit: 5, risk_decision: 'REVIEW' })
        ]);
        setSummary(sumData); setHealth(healthData);
        setBlockTxns(blockData); setReviewTxns(reviewData);
      } catch (err) {
        setError("Failed to load dashboard data. Check that FastAPI is running on http://127.0.0.1:8000");
      } finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Fetching risk intelligence..." />;
  if (error || !summary || !health) return <ErrorState message={error || "Unknown error"} />;

  const econData = [
    { name: 'Baseline Loss', value: summary.baseline_fraud_loss_inr, fill: '#f43f5e' },
    { name: 'Prevented', value: summary.fraud_loss_prevented_inr, fill: '#10b981' },
    { name: 'Residual Loss', value: summary.residual_fraud_loss_inr, fill: '#f59e0b' }
  ];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Sentinel Risk Control Center</h2>
          <p className="text-slate-400 mt-1">Cost-Aware AI Risk Intelligence · <span className="inline-block bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-xs font-semibold ml-2">HELD-OUT TEST SET</span></p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
          <ShieldCheck className="text-emerald-400" size={16} />
          <span className="text-xs font-medium text-emerald-400">Protection Active</span>
        </div>
      </div>

      {/* Operational Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Blocked Transactions" value={formatNumber(summary.routing_counts.BLOCK || 0)} icon={<AlertTriangle size={20} />} accent="rose" />
        <MetricCard title="Requires Review" value={formatNumber(summary.routing_counts.REVIEW || 0)} icon={<AlertTriangle size={20} />} accent="amber" />
        <MetricCard title="Fraud Prevented (Value)" value={formatCurrency(summary.fraud_loss_prevented_inr)} icon={<IndianRupee size={20} />} accent="emerald" />
        <MetricCard title="Residual Fraud Exposure" value={formatCurrency(summary.residual_fraud_loss_inr)} icon={<TrendingDown size={20} />} accent="slate" />
      </div>

      {/* Risk Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-rose-400 uppercase">High Risk (Blocked)</h3>
            <button onClick={() => navigate('/transactions?risk_decision=BLOCK')} className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1">View All <ArrowRight size={12} /></button>
          </div>
          <div className="space-y-3">
            {blockTxns?.items.map(txn => (
              <div key={txn.transaction_id} onClick={() => navigate(`/transactions/${txn.transaction_id}`)} className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-rose-500/30 cursor-pointer hover:bg-slate-800 transition-colors">
                <div><p className="text-sm font-semibold text-slate-200">{formatCurrency(txn.transaction_amount)}</p><p className="text-xs text-slate-500 font-mono">{txn.transaction_id.slice(0, 8)}...</p></div>
                <div className="text-right"><p className="text-sm font-bold text-rose-400">{txn.risk_score.toFixed(1)}</p><Badge decision={txn.decision} /></div>
              </div>
            ))}
            {blockTxns?.items.length === 0 && <p className="text-sm text-slate-500 text-center py-4">No blocked transactions in test set.</p>}
          </div>
        </Card>
        
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-amber-400 uppercase">Requires Review</h3>
            <button onClick={() => navigate('/transactions?risk_decision=REVIEW')} className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1">View All <ArrowRight size={12} /></button>
          </div>
          <div className="space-y-3">
            {reviewTxns?.items.map(txn => (
              <div key={txn.transaction_id} onClick={() => navigate(`/transactions/${txn.transaction_id}`)} className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-amber-500/30 cursor-pointer hover:bg-slate-800 transition-colors">
                <div><p className="text-sm font-semibold text-slate-200">{formatCurrency(txn.transaction_amount)}</p><p className="text-xs text-slate-500 font-mono">{txn.transaction_id.slice(0, 8)}...</p></div>
                <div className="text-right"><p className="text-sm font-bold text-amber-400">{txn.risk_score.toFixed(1)}</p><Badge decision={txn.decision} /></div>
              </div>
            ))}
            {reviewTxns?.items.length === 0 && <p className="text-sm text-slate-500 text-center py-4">No transactions require review.</p>}
          </div>
        </Card>
      </div>

      {/* Secondary Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">How Sentinel Handled Transactions</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: The proportion of transactions Sentinel allowed, routed for review, or blocked.</p>
          <RoutingChart data={summary.routing_counts} />
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Fraud Exposure Before vs After Sentinel</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: Estimated fraud exposure before protection compared with exposure remaining after Sentinel's decisions.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={econData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" tickFormatter={(v) => `₹${v/1000}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  formatter={(v) => formatCurrency(Number(v))}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}