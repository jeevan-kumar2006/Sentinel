import { useState, useEffect } from 'react';
import { getEvaluation } from '../services/api';
import { EvaluationResponse } from '../types/api';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';
import ConfusionMatrixChart from '../components/charts/ConfusionMatrixChart';
import { formatPercent } from '../utils/format';

export default function EvaluationPage() {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const evalData = await getEvaluation();
        setData(evalData);
      } catch {
        setError("Failed to load evaluation data.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Loading evaluation..." />;
  if (error || !data) return <ErrorState message={error || "Unknown error"} />;

  const metrics = data.test_results.metrics;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Model Performance</h2>
        <div className="mt-2 inline-block bg-amber-500/10 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-full text-xs font-semibold">
          HELD-OUT TEST SET EVALUATION
        </div>
        <p className="text-slate-400 mt-2 text-sm max-w-2xl">
          These metrics come from the chronological unseen TEST period and were not used to train or tune the final model.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><p className="text-xs text-slate-500 mb-1">Precision</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.precision)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1">Recall</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.recall)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1">F1 Score</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.f1)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1">PR-AUC</p><p className="text-xl font-bold text-slate-100">{metrics.pr_auc ? formatPercent(metrics.pr_auc) : 'N/A'}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1">ROC-AUC</p><p className="text-xl font-bold text-slate-100">{metrics.roc_auc ? formatPercent(metrics.roc_auc) : 'N/A'}</p></Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase">Confusion Matrix</h3>
        <ConfusionMatrixChart data={metrics} />
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Scenario Breakdown</h3>
        <div className="space-y-3">
          {Object.entries(data.test_results.scenario_recall).map(([scenario, stats]) => (
            <div key={scenario} className="flex justify-between items-center border-b border-slate-700 pb-2">
              <span className="text-slate-300">{scenario}</span>
              <div className="flex gap-6 text-sm">
                <span className="text-slate-500">Count: {stats.count}</span>
                <span className="text-emerald-400 font-medium">Recall: {formatPercent(stats.recall)}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}