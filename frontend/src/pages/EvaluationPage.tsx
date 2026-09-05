import { useState, useEffect } from 'react';
import { getEvaluation } from '../services/api';
import { EvaluationResponse } from '../types/api';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import Card from '../components/ui/Card';
import ConfusionMatrixChart from '../components/charts/ConfusionMatrixChart';
import { formatPercent } from '../utils/format';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

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
      } finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Loading evaluation..." />;
  if (error || !data) return <ErrorState message={error || "Unknown error"} />;

  const metrics = data.test_results.metrics;
  const scenarioData = Object.entries(data.test_results.scenario_recall).map(([name, stats]) => ({
    name: name.replace('_', ' '),
    recall: stats.recall * 100
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">Model Performance</h2>
        <div className="mt-2 inline-block bg-amber-500/10 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-full text-xs font-semibold">HELD-OUT TEST SET EVALUATION</div>
        <p className="text-slate-400 mt-2 text-sm max-w-2xl">These metrics come from the chronological unseen TEST period and were not used to train or tune the final model.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><p className="text-xs text-slate-500 mb-1" title="How often Sentinel's fraud flags were correct.">Precision</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.precision)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1" title="How much of the fraud Sentinel successfully detected.">Recall</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.recall)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1" title="Balanced measure of precision and recall.">F1 Score</p><p className="text-xl font-bold text-slate-100">{formatPercent(metrics.f1)}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1" title="How consistently Sentinel ranks fraud above legitimate transactions.">PR-AUC</p><p className="text-xl font-bold text-slate-100">{metrics.pr_auc ? formatPercent(metrics.pr_auc) : 'N/A'}</p></Card>
        <Card><p className="text-xs text-slate-500 mb-1" title="How well Sentinel separates fraudulent and legitimate transactions.">ROC-AUC</p><p className="text-xl font-bold text-slate-100">{metrics.roc_auc ? formatPercent(metrics.roc_auc) : 'N/A'}</p></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase">Confusion Matrix</h3>
          <ConfusionMatrixChart data={metrics} />
        </Card>
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Scenario Breakdown</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: How effectively Sentinel detects each simulated fraud pattern in the held-out test set.</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scenarioData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" unit="%" />
                <YAxis type="category" dataKey="name" stroke="#94a3b8" width={100} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v) => `${v}%`} />
                <Bar dataKey="recall" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {data.test_results.pr_curve && (
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">Precision-Recall Curve</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: The tradeoff between precision and recall across different decision thresholds.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.test_results.pr_curve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="recall" type="number" domain={[0, 1]} stroke="#94a3b8" label={{ value: 'Recall', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
                <YAxis dataKey="precision" type="number" domain={[0, 1]} stroke="#94a3b8" label={{ value: 'Precision', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="precision" stroke="#10b981" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {data.test_results.roc_curve && (
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase">ROC Curve</h3>
          <p className="text-xs text-slate-500 mb-4">What this shows: The tradeoff between true positive rate and false positive rate.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.test_results.roc_curve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="fpr" type="number" domain={[0, 1]} stroke="#94a3b8" label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
                <YAxis dataKey="tpr" type="number" domain={[0, 1]} stroke="#94a3b8" label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="tpr" stroke="#f59e0b" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}