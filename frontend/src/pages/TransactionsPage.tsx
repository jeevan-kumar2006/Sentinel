import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getTransactions } from '../services/api';
import { PaginatedTransactions } from '../types/api';
import TransactionTable from '../components/transactions/TransactionTable';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';

export default function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<PaginatedTransactions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  
  const page = parseInt(searchParams.get('page') || '1', 10);
  const limit = parseInt(searchParams.get('limit') || '20', 10);
  const decision = searchParams.get('risk_decision') || '';
  
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);

  useEffect(() => {
    const fetchData = async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;
      
      setLoading(true);
      setError(null);
      
      try {
        const result = await getTransactions({
          page,
          limit,
          risk_decision: decision || undefined,
          search: debouncedSearch || undefined
        }, controller.signal);
        setData(result);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError("Failed to fetch transactions.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [page, limit, decision, debouncedSearch]);

  const handleDecisionChange = (dec: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (dec) next.set('risk_decision', dec);
      else next.delete('risk_decision');
      next.set('page', '1');
      return next;
    });
  };

  const handleLimitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('limit', e.target.value);
      next.set('page', '1');
      return next;
    });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (e.target.value) next.set('search', e.target.value);
      else next.delete('search');
      next.set('page', '1');
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Risk Activity</h2>
        <p className="text-slate-400 mt-1">Explore transaction-level risk decisions · Held-out Test Set</p>
      </div>

      <Card>
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <input
            type="text"
            placeholder="Search by Transaction ID or User ID..."
            value={search}
            onChange={handleSearchChange}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500"
          />
          <div className="flex gap-2">
            <button onClick={() => handleDecisionChange('')} className={`px-4 py-2 rounded-lg text-sm border ${decision === '' ? 'bg-slate-700 border-slate-600 text-white' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'}`}>All</button>
            <button onClick={() => handleDecisionChange('ALLOW')} className={`px-4 py-2 rounded-lg text-sm border ${decision === 'ALLOW' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-emerald-400'}`}>Allow</button>
            <button onClick={() => handleDecisionChange('REVIEW')} className={`px-4 py-2 rounded-lg text-sm border ${decision === 'REVIEW' ? 'bg-amber-500/20 border-amber-500 text-amber-400' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-amber-400'}`}>Review</button>
            <button onClick={() => handleDecisionChange('BLOCK')} className={`px-4 py-2 rounded-lg text-sm border ${decision === 'BLOCK' ? 'bg-rose-500/20 border-rose-500 text-rose-400' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-rose-400'}`}>Block</button>
          </div>
          <select 
            value={limit} 
            onChange={handleLimitChange}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500"
          >
            <option value={10}>10 / page</option>
            <option value={20}>20 / page</option>
            <option value={50}>50 / page</option>
          </select>
        </div>

        {loading ? <LoadingState message="Loading transactions..." /> : 
         error ? <ErrorState message={error} /> : 
         data && data.items.length > 0 ? <TransactionTable transactions={data.items} /> : 
         <div className="py-12 text-center text-slate-500">No transactions match these filters.</div>}
      </Card>

      {data && !loading && (
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-400">
            Page {data.page} of {data.total_pages} (Total: {data.total})
          </span>
          <div className="flex gap-2">
            <button 
              onClick={() => setSearchParams(prev => { prev.set('page', String(Math.max(1, page - 1))); return prev; })} 
              disabled={page === 1}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700"
            >
              Previous
            </button>
            <button 
              onClick={() => setSearchParams(prev => { prev.set('page', String(page + 1)); return prev; })} 
              disabled={page === data.total_pages}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}