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
import { ArrowLeft } from 'lucide-react';

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

  return (
    <div className="space-y-6">
      <Link to="/transactions" className="inline-flex items-center text-sm text-slate-400 hover:text-emerald-400">
        <ArrowLeft size={16} className="mr-1" /> Back to Transactions
      </Link>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 font-mono">{txn.transaction_id}</h2>
          <p className="text-slate-500 mt-1">{formatDate(txn.timestamp)}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-slate-500 uppercase">Risk Score</p>
            <p className="text-2xl font-bold text-slate-100">{txn.risk_score.toFixed(1)}</p>
          </div>
          <Badge decision={txn.decision} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Transaction Metadata</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><p className="text-slate-500">Amount</p><p className="text-slate-200">{formatCurrency(txn.transaction_amount)}</p></div>
            <div><p className="text-slate-500">User ID</p><p className="text-slate-200 font-mono">{txn.user_id}</p></div>
            <div><p className="text-slate-500">Merchant ID</p><p className="text-slate-200 font-mono">{txn.merchant_id}</p></div>
            <div><p className="text-slate-500">Device</p><p className="text-slate-200 font-mono">{txn.device_fingerprint}</p></div>
            <div><p className="text-slate-500">IP Address</p><p className="text-slate-200 font-mono">{txn.ip_address}</p></div>
            <div><p className="text-slate-500">Status</p><p className="text-slate-200">{txn.transaction_status}</p></div>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Risk Reasons</h3>
          <ReasonCodeList reasons={txn.reasons} />
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Engineered Features</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><p className="text-slate-500">Velocity (5m)</p><p className="text-slate-200">{txn.transaction_velocity_5m}</p></div>
          <div><p className="text-slate-500">Velocity (1h)</p><p className="text-slate-200">{txn.transaction_velocity_1h}</p></div>
          <div><p className="text-slate-500">Hist. Avg Amount</p><p className="text-slate-200">{formatCurrency(txn.historical_avg_amount)}</p></div>
          <div><p className="text-slate-500">Amount Ratio</p><p className="text-slate-200">{txn.amount_ratio_to_history?.toFixed(2) || 'N/A'}</p></div>
          <div><p className="text-slate-500">Device User Count</p><p className="text-slate-200">{txn.device_user_count}</p></div>
          <div><p className="text-slate-500">IP User Count</p><p className="text-slate-200">{txn.ip_user_count}</p></div>
          <div><p className="text-slate-500">Failed Attempts</p><p className="text-slate-200">{txn.failed_attempt_velocity}</p></div>
          <div><p className="text-slate-500">Geo Velocity</p><p className="text-slate-200">{txn.geographic_velocity?.toFixed(0) || 'N/A'} km/h</p></div>
        </div>
      </Card>
    </div>
  );
}