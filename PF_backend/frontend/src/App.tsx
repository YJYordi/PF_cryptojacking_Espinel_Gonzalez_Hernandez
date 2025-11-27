import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AlertsPage from './pages/Alerts';
import RulesPage from './pages/Rules';
import IngestPage from './pages/Ingest';
import PerformancePage from './pages/Performance';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/performance" element={<PerformancePage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

