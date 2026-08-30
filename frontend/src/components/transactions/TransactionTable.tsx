import { useNavigate } from 'react-router-dom';
import { TransactionBase } from '../../types/api';
import Badge from '../ui/Badge';
import RiskBar from '../ui/RiskBar';
import { formatCurrency } from '../../utils/format';
import { formatDate } from '../../utils/dates';
import { ChevronRight } from 'lucide-react';

export default function TransactionTable({ transactions }: { transactions: TransactionBase[] }) {
  const navigate = useNavigate();

  const rowBorderClass = (decision: string) => {
    if (decision === 'BLOCK') return 'border-l-4 border-rose-500';
    if (decision === 'REVIEW') return 'border-l-4 border-amber-500';
    return 'border-l-4 border-transparent';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-slate-400 uppercase border-b border-slate-700">
          <tr>
            <th className="px-4 py-3">Timestamp</th>
            <th className="px-4 py-3">Transaction ID</th>
            <th className="px-4 py-3">Amount</th>
            <th className="px-4 py-3 min-w-[150px]">Risk Score</th>
            <th className="px-4 py-3">Decision</th>
            <th className="px-4 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr 
              key={txn.transaction_id} 
              onClick={() => navigate(`/transactions/${txn.transaction_id}`)}
              className={`border-b border-slate-800 hover:bg-slate-700/50 cursor-pointer transition-colors ${rowBorderClass(txn.decision)}`}
            >
              <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{formatDate(txn.timestamp)}</td>
              <td className="px-4 py-3 font-mono text-slate-300">{txn.transaction_id.slice(0, 8)}...</td>
              <td className="px-4 py-3 text-slate-300 font-medium">{formatCurrency(txn.transaction_amount)}</td>
              <td className="px-4 py-3"><RiskBar score={txn.risk_score} decision={txn.decision} /></td>
              <td className="px-4 py-3"><Badge decision={txn.decision} /></td>
              <td className="px-4 py-3 text-right text-slate-500">
                <span className="flex items-center justify-end gap-1 text-xs">Investigate <ChevronRight size={14} /></span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}