import React, { useState } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { 
  LayoutDashboard, 
  Play, 
  Settings, 
  TrendingUp, 
  BarChart3, 
  List, 
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { toast } from 'sonner';

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success('تم تسجيل الخروج بنجاح');
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'لوحة التحكم' },
    { path: '/create', icon: Play, label: 'إنشاء فيديو' },
    { path: '/videos', icon: List, label: 'قائمة النشر' },
    { path: '/analytics', icon: BarChart3, label: 'التحليلات' },
    { path: '/trends', icon: TrendingUp, label: 'الترندات' },
    { path: '/settings', icon: Settings, label: 'الإعدادات' }
  ];

  return (
    <div dir="rtl" className="min-h-screen bg-[#09090b] font-tajawal">
      <div className="flex">
        <aside className={`fixed right-0 top-0 h-screen w-64 bg-zinc-900/80 backdrop-blur-xl border-l border-zinc-800/50 z-50 transform transition-transform duration-300 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : 'translate-x-full'}`}>
          <div className="flex flex-col h-full">
            <div className="p-6 border-b border-zinc-800/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 flex items-center justify-center">
                  <Play className="w-5 h-5 text-orange-500" fill="currentColor" />
                </div>
                <div>
                  <h1 className="text-xl font-cairo font-bold text-white">يو.آي</h1>
                  <p className="text-xs text-zinc-500 font-tajawal">أتمتة يوتيوب</p>
                </div>
              </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                      isActive
                        ? 'bg-orange-500/10 text-orange-500 border border-orange-500/30 shadow-lg shadow-orange-500/10'
                        : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white border border-transparent'
                    }`}
                    data-testid={`menu-${item.path.replace('/', '')}`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-tajawal font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="p-4 border-t border-zinc-800/50">
              <Button
                onClick={handleLogout}
                variant="outline"
                className="w-full justify-start gap-3 border-zinc-800 text-zinc-400 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/30 font-tajawal transition-all duration-300"
                data-testid="logout-button"
              >
                <LogOut className="h-5 w-5" />
                تسجيل الخروج
              </Button>
            </div>
          </div>
        </aside>

        <div className="flex-1 lg:mr-64">
          <header className="sticky top-0 z-40 bg-zinc-900/60 backdrop-blur-lg border-b border-zinc-800/50">
            <div className="flex items-center justify-between px-6 py-4">
              <Button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                variant="ghost"
                size="icon"
                className="lg:hidden text-white"
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </Button>
              <div className="flex-1 lg:hidden"></div>
            </div>
          </header>

          <main className="p-6 lg:p-10">
            <Outlet />
          </main>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
