import { useState, useEffect } from 'react';
import { getEconomics } from '../services/api';
import { EconomicsResponse } from '../types/api';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';
import { formatCurrency } from '../utils/format';

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
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Loading economics..." />;
  if (error || !data) return <ErrorState message={error || "Unknown error"} />;

  const econ = data.final_test_economic_result;

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
              <span className="text-amber-400 font-bold">{(data.review_threshold * 100).toFixed(1)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Block Threshold</span>
              <span className="text-rose-400 font-bold">{(data.block_threshold * 100).toFixed(1)}</span>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Economic Assumptions</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Chargeback Fee</span>
              <span className="text-slate-200">{formatCurrency(data.economic_assumptions.chargeback_fee)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Customer LTV</span>
              <span className="text-slate-200">{formatCurrency(data.economic_assumptions.customer_ltv)}</span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase">Final Test Economic Results</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Baseline Fraud Loss</span>
            <span className="text-rose-400 font-semibold">{formatCurrency(econ.baseline_fraud_loss)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Residual Fraud Loss</span>
            <span className="text-amber-400 font-semibold">{formatCurrency(econ.residual_fraud_loss)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">Fraud Loss Prevented</span>
            <span className="text-emerald-400 font-semibold">{formatCurrency(econ.fraud_loss_prevented)}</span>
          </div>
          <div className="flex justify-between items-center border-b border-slate-700 pb-3">
            <span className="text-slate-400">False Positive Cost</span>
            <span className="text-rose-400 font-semibold">{formatCurrency(econ.false_positive_cost)}</span>
          </div>
          <div className="flex justify-between items-center pt-2">
            <span className="text-slate-300 font-bold">Net Economic Benefit</span>
            <span className="text-emerald-400 font-bold text-lg">{formatCurrency(econ.net_economic_benefit)}</span>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-2 uppercase">Threshold Tradeoff Curve</h3>
        <p className="text-slate-500 text-sm">
          Threshold tradeoff curve data is not available from the current evaluation artifact.
        </p>
      </Card>
    </div>
  );
}