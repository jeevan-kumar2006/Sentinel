import { useNavigate } from 'react-router-dom';
import { TransactionBase } from '../../types/api';
import Badge from '../ui/Badge';
import { formatCurrency } from '../../utils/format';
import { formatDate } from '../../utils/dates';

export default function TransactionTable({ transactions }: { transactions: TransactionBase[] }) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-slate-400 uppercase border-b border-slate-700">
          <tr>
            <th className="px-4 py-3">Timestamp</th>
            <th className="px-4 py-3">Transaction ID</th>
            <th className="px-4 py-3">Amount</th>
            <th className="px-4 py-3">Risk Score</th>
            <th className="px-4 py-3">Decision</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr 
              key={txn.transaction_id} 
              onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
              className="border-b border-slate-800 hover:bg-slate-700/50 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3 text-slate-400">{formatDate(txn.timestamp)}</td>
              <td className="px-4 py-3 font-mono text-slate-300">{txn.transaction_id.slice(0, 8)}...</td>
              <td className="px-4 py-3 text-slate-300">{formatCurrency(txn.transaction_amount)}</td>
              <td className="px-4 py-3 text-slate-300">{txn.risk_score.toFixed(1)}</td>
              <td className="px-4 py-3"><Badge decision={txn.decision} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}