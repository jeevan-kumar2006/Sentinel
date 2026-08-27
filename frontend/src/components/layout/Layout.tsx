import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-900">
      <Sidebar />
      <div className="md:ml-64">
        <Header />
        <main className="p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}