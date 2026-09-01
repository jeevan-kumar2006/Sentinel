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
          getDashboardSummary(),
          getHealth(),
          getTransactions({ page: 1, limit: 5, risk_decision: 'BLOCK' }),
          getTransactions({ page: 1, limit: 5, risk_decision: 'REVIEW' })
        ]);
        setSummary(sumData);
        setHealth(healthData);
        setBlockTxns(blockData);
        setReviewTxns(reviewData);
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
        <MetricCard 
          title="Blocked Transactions" 
          value={formatNumber(summary.routing_counts.BLOCK || 0)} 
          icon={<AlertTriangle size={20} />} 
          accent="rose" 
        />
        <MetricCard 
          title="Requires Review" 
          value={formatNumber(summary.routing_counts.REVIEW || 0)} 
          icon={<AlertTriangle size={20} />} 
          accent="amber" 
        />
        <MetricCard 
          title="Fraud Prevented (Value)" 
          value={formatCurrency(summary.fraud_loss_prevented_inr)} 
          icon={<IndianRupee size={20} />} 
          accent="emerald" 
        />
        <MetricCard 
          title="Residual Fraud Exposure" 
          value={formatCurrency(summary.residual_fraud_loss_inr)} 
          icon={<TrendingDown size={20} />} 
          accent="slate" 
        />
      </div>

      {/* Risk Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-rose-400 uppercase">High Risk (Blocked)</h3>
            <button onClick={() => navigate('/transactions?risk_decision=BLOCK')} className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1">
              View All <ArrowRight size={12} />
            </button>
          </div>
          <div className="space-y-3">
            {blockTxns?.items.map(txn => (
              <div key={txn.transaction_id} onClick={() => navigate(`/transactions/${txn.transaction_id}`)} className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-rose-500/30 cursor-pointer hover:bg-slate-800 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-slate-200">{formatCurrency(txn.transaction_amount)}</p>
                  <p className="text-xs text-slate-500 font-mono">{txn.transaction_id.slice(0, 8)}...</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-rose-400">{txn.risk_score.toFixed(1)}</p>
                  <Badge decision={txn.decision} />
                </div>
              </div>
            ))}
            {blockTxns?.items.length === 0 && <p className="text-sm text-slate-500 text-center py-4">No blocked transactions in test set.</p>}
          </div>
        </Card>
        
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-amber-400 uppercase">Requires Review</h3>
            <button onClick={() => navigate('/transactions?risk_decision=REVIEW')} className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1">
              View All <ArrowRight size={12} />
            </button>
          </div>
          <div className="space-y-3">
            {reviewTxns?.items.map(txn => (
              <div key={txn.transaction_id} onClick={() => navigate(`/transactions/${txn.transaction_id}`)} className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-amber-500/30 cursor-pointer hover:bg-slate-800 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-slate-200">{formatCurrency(txn.transaction_amount)}</p>
                  <p className="text-xs text-slate-500 font-mono">{txn.transaction_id.slice(0, 8)}...</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-amber-400">{txn.risk_score.toFixed(1)}</p>
                  <Badge decision={txn.decision} />
                </div>
              </div>
            ))}
            {reviewTxns?.items.length === 0 && <p className="text-sm text-slate-500 text-center py-4">No transactions require review.</p>}
          </div>
        </Card>
      </div>

      {/* Secondary Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Routing Distribution</h3>
          <p className="text-xs text-slate-500 mb-3">From held-out test data</p>
          <RoutingChart data={summary.routing_counts} />
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Economic Summary (Held-out Test)</h3>
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
