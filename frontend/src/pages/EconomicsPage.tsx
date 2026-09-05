import { useState, useEffect } from 'react';
import { getEconomics } from '../services/api';
import { EconomicsResponse } from '../types/api';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';
import { formatCurrency } from '../utils/format';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';

export default function EconomicsPage() {
  const [data, setData] = useState<EconomicsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const econData = await getEconomics();
        setData(econData);
      } catch {
        setError("Failed to load economics data.");
      } finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Loading economics..." />;
  if (error || !data) return <ErrorState message={error || "Unknown error"} />;

  const econ = data?.final_test_economic_result ?? {};
  const assumptions = data?.economic_assumptions ?? {};
  
  // Safely map threshold sweep to prevent Recharts crashes on nested objects
  const sweepData = (data?.threshold_sweep ?? []).map((s: any) => ({
    threshold: s.threshold ?? 0,
    net_economic_benefit: s.net_economic_benefit ?? 0,
    recall: s.recall ?? 0
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Economic Impact</h2>
        <p className="text-slate-400 mt-1">Threshold optimization and financial outcomes · Held-out Test Set</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Frozen Thresholds (Risk Score Scale 0-100)</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Review Threshold</span>
              <span className="text-amber-400 font-bold">{((data?.review_threshold ?? 0) * 100).toFixed(1)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Block Threshold</span>
              <span className="text-rose-400 font-bold">{((data?.block_threshold ?? 0) * 100).toFixed(1)}</span>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Economic Assumptions</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Chargeback Fee</span>
              <span className="text-slate-200">{formatCurrency(assumptions.chargeback_fee ?? 0)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Customer LTV</span>
              <span className="text-slate-200">{formatCurrency(assumptions.customer_ltv ?? 0)}</span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase">Final Test Economic Results</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Baseline Fraud Loss</span>
            <span className="text-rose-400 font-semibold">{formatCurrency(econ.baseline_fraud_loss ?? 0)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Residual Fraud Loss</span>
            <span className="text-amber-400 font-semibold">{formatCurrency(econ.residual_fraud_loss ?? 0)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Fraud Loss Prevented</span>
            <span className="text-emerald-400 font-semibold">{formatCurrency(econ.fraud_loss_prevented ?? 0)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">False Positive Cost</span>
            <span className="text-rose-400 font-semibold">{formatCurrency(econ.false_positive_cost ?? 0)}</span>
          </div>
          <div className="flex justify-between items-center pt-2">
            <span className="text-slate-300 font-bold">Net Economic Benefit</span>
            <span className="text-emerald-400 font-bold text-lg">{formatCurrency(econ.net_economic_benefit ?? 0)}</span>
          </div>
        </div>
      </Card>

      {sweepData.length > 0 ? (
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Threshold Tradeoff Curve</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: The tradeoff between catching more fraud and increasing legitimate-customer impact as the block threshold changes (derived from validation data).</p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sweepData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="threshold" type="number" domain={[0, 1]} stroke="#94a3b8" label={{ value: 'Block Threshold', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
                <YAxis yAxisId="left" stroke="#10b981" label={{ value: 'Net Benefit (INR)', angle: -90, position: 'insideLeft', fill: '#10b981' }} />
                <YAxis yAxisId="right" orientation="right" domain={[0, 1]} stroke="#f59e0b" label={{ value: 'Recall', angle: 90, position: 'insideRight', fill: '#f59e0b' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Legend />
                <ReferenceLine x={data?.block_threshold ?? 0} stroke="#f43f5e" strokeDasharray="5 5" label={{ value: 'Selected Block Threshold', fill: '#f43f5e', position: 'top' }} />
                <Line yAxisId="left" type="monotone" dataKey="net_economic_benefit" stroke="#10b981" dot={false} strokeWidth={2} name="Net Economic Benefit" />
                <Line yAxisId="right" type="monotone" dataKey="recall" stroke="#f59e0b" dot={false} strokeWidth={2} name="Recall" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : (
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-2 uppercase">Threshold Tradeoff Curve</h3>
          <p className="text-slate-500 text-sm">
            Threshold tradeoff curve data is not available. Please run `scripts/4_generate_curves.py` to generate validation sweep data.
          </p>
        </Card>
      )}
    </div>
  );
}