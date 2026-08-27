import { useState, useEffect, useRef } from 'react';
import { getTransactions } from '../services/api';
import { PaginatedTransactions } from '../types/api';
import TransactionTable from '../components/transactions/TransactionTable';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';

export default function TransactionsPage() {
  const [data, setData] = useState<PaginatedTransactions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [decision, setDecision] = useState<string>('');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  
  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset page on new search
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);

  // Fetch data
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

  const handleDecisionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDecision(e.target.value);
    setPage(1);
  };

  const handleLimitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLimit(Number(e.target.value));
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Risk Activity</h2>
        <p className="text-slate-400 mt-1">Explore transaction-level risk decisions</p>
      </div>

      <Card>
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <input
            type="text"
            placeholder="Search by Transaction ID or User ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500"
          />
          <select 
            value={decision} 
            onChange={handleDecisionChange}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Decisions</option>
            <option value="ALLOW">ALLOW</option>
            <option value="REVIEW">REVIEW</option>
            <option value="BLOCK">BLOCK</option>
          </select>
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
         <div className="py-12 text-center text-slate-500">No transactions found.</div>}
      </Card>

      {data && !loading && (
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-400">
            Page {data.page} of {data.total_pages} (Total: {data.total})
          </span>
          <div className="flex gap-2">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))} 
              disabled={page === 1}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700"
            >
              Previous
            </button>
            <button 
              onClick={() => setPage(p => p + 1)} 
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