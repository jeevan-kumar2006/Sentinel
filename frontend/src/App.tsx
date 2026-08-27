import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import TransactionsPage from './pages/TransactionsPage'
import TransactionDetailPage from './pages/TransactionDetailPage'
import EvaluationPage from './pages/EvaluationPage'
import EconomicsPage from './pages/EconomicsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/transactions/:id" element={<TransactionDetailPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
        <Route path="/economics" element={<EconomicsPage />} />
        <Route path="*" element={<DashboardPage />} />
      </Route>
    </Routes>
  )
}