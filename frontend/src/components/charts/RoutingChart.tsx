import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

export default function RoutingChart({ data }: { data: Record<string, number> }) {
  const chartData = [
    { name: 'ALLOW', value: data.ALLOW || 0, color: '#10b981' },
    { name: 'REVIEW', value: data.REVIEW || 0, color: '#f59e0b' },
    { name: 'BLOCK', value: data.BLOCK || 0, color: '#f43f5e' },
  ];

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}