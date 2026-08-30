import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTransaction } from '../services/api';
import { TransactionDetail } from '../types/api';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import ReasonCodeList from '../components/transactions/ReasonCodeList';
import { formatDate } from '../utils/dates';
import { formatCurrency, formatNumber } from '../utils/format';
import { ArrowLeft, ShieldAlert, Activity, MapPin, Smartphone, Globe } from 'lucide-react';

export default function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [txn, setTxn] = useState<TransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      try {
        const data = await getTransaction(id);
        setTxn(data);
      } catch {
        setError("Transaction not found.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) return <LoadingState message="Loading transaction..." />;
  if (error || !txn) return <ErrorState message={error || "Unknown error"} />;

  const riskColor = txn.decision === 'BLOCK' ? 'bg-rose-500' : txn.decision === 'REVIEW' ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="space-y-6">
      <Link to="/transactions" className="inline-flex items-center text-sm text-slate-400 hover:text-emerald-400">
        <ArrowLeft size={16} className="mr-1" /> Back to Risk Activity
      </Link>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 font-mono">{txn.transaction_id}</h2>
          <p className="text-slate-500 mt-1">{formatDate(txn.timestamp)}</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-xs text-slate-500 uppercase">Risk Score</p>
            <p className="text-3xl font-bold text-slate-100">{txn.risk_score.toFixed(1)}<span className="text-lg text-slate-500">/100</span></p>
          </div>
          <div className="min-w-[100px] text-center">
            <Badge decision={txn.decision} />
          </div>
        </div>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-slate-400 uppercase">Risk Level</h3>
        </div>
        <div className="h-4 w-full rounded-full bg-slate-700 overflow-hidden">
          <div
            className={`h-4 rounded-full ${riskColor}`}
            style={{ width: `${txn.risk_score}%` }}
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Transaction Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><p className="text-slate-500">Amount</p><p className="text-slate-200 font-medium">{formatCurrency(txn.transaction_amount)}</p></div>
            <div><p className="text-slate-500">Status</p><p className="text-slate-200">{txn.transaction_status}</p></div>
            <div><p className="text-slate-500">User ID</p><p className="text-slate-200 font-mono">{txn.user_id}</p></div>
            <div><p className="text-slate-500">Merchant ID</p><p className="text-slate-200 font-mono">{txn.merchant_id}</p></div>
            <div className="flex items-center gap-2"><Smartphone size={14} className="text-slate-500" /><div><p className="text-slate-500">Device</p><p className="text-slate-200 font-mono">{txn.device_fingerprint}</p></div></div>
            <div className="flex items-center gap-2"><Globe size={14} className="text-slate-500" /><div><p className="text-slate-500">IP Address</p><p className="text-slate-200 font-mono">{txn.ip_address}</p></div></div>
          </div>
        </Card>

        <Card className="bg-slate-900/50 border-amber-500/30">
          <h3 className="text-sm font-semibold text-amber-400 mb-4 uppercase flex items-center gap-2"><ShieldAlert size={16} /> Why was this flagged?</h3>
          <ReasonCodeList reasons={txn.reasons} />
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase flex items-center gap-2"><Activity size={16} /> Behavioral Signals</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Velocity (5m)</p>
            <p className="text-slate-200 font-medium mt-1">{txn.transaction_velocity_5m} txns</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Velocity (1h)</p>
            <p className="text-slate-200 font-medium mt-1">{txn.transaction_velocity_1h} txns</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Hist. Avg Amount</p>
            <p className="text-slate-200 font-medium mt-1">{formatCurrency(txn.historical_avg_amount)}</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Amount Ratio</p>
            <p className="text-slate-200 font-medium mt-1">{txn.amount_ratio_to_history ? `${txn.amount_ratio_to_history.toFixed(2)}x` : 'N/A'}</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Device User Count</p>
            <p className="text-slate-200 font-medium mt-1">{txn.device_user_count} users</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">IP User Count</p>
            <p className="text-slate-200 font-medium mt-1">{txn.ip_user_count} users</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <p className="text-slate-500 text-xs">Failed Attempts (1h)</p>
            <p className="text-slate-200 font-medium mt-1">{txn.failed_attempt_velocity}</p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg flex items-start gap-2">
            <MapPin size={14} className="text-slate-500 mt-1" />
            <div>
              <p className="text-slate-500 text-xs">Geo Velocity</p>
              <p className="text-slate-200 font-medium mt-1">{txn.geographic_velocity ? `${txn.geographic_velocity.toFixed(0)} km/h` : 'N/A'}</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}