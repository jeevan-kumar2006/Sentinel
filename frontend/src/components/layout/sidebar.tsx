import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ArrowLeftRight, FileBarChart, IndianRupee } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/evaluation', label: 'Evaluation', icon: FileBarChart },
  { to: '/economics', label: 'Economics', icon: IndianRupee },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-64 h-screen bg-slate-950 border-r border-slate-800 fixed">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold tracking-wider text-emerald-400">SENTINEL</h1>
        <p className="text-xs text-slate-500 mt-1">Risk Control Center</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-slate-800 text-emerald-400'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 text-xs text-slate-600 border-t border-slate-800">
        Razorpay Buildathon · Track 02
      </div>
    </aside>
  );
}