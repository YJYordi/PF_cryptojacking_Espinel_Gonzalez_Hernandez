import { Link, useLocation } from 'react-router-dom';
import { Shield, AlertTriangle, Settings, Upload, Home, Activity } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Alertas', href: '/alerts', icon: AlertTriangle },
  { name: 'Reglas', href: '/rules', icon: Settings },
  { name: 'Ingest', href: '/ingest', icon: Upload },
  { name: 'Rendimiento', href: '/performance', icon: Activity },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-700">
            <Shield className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="text-xl font-bold text-white">IDS Cryptojacking</h1>
              <p className="text-xs text-slate-400">Sistema de Detección</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}

