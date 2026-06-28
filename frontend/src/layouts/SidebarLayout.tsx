import React, { useState, useEffect } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  MessageSquare,
  FolderOpen,
  FileText,
  Settings,
  ShieldCheck,
  LogOut,
  Sun,
  Moon,
  Menu,
  ChevronLeft,
  ChevronRight,
  BrainCircuit,
  User
} from 'lucide-react';

const SidebarLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'dark'
  );

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'RAG Chat', path: '/chat', icon: MessageSquare },
    { name: 'Collections', path: '/collections', icon: FolderOpen },
    { name: 'Documents', path: '/documents', icon: FileText },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  if (user?.role === 'ADMIN') {
    menuItems.push({ name: 'Admin Dashboard', path: '/admin', icon: ShieldCheck });
  }

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground transition-colors duration-300">
      {/* Sidebar Container */}
      <aside
        className={`flex flex-col border-r border-border bg-card/50 backdrop-blur-lg transition-all duration-300 ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          <Link to="/" className="flex items-center space-x-2">
            <BrainCircuit className="h-8 w-8 text-primary animate-pulse-slow" />
            {!collapsed && (
              <span className="font-outfit text-lg font-bold tracking-tight bg-gradient-to-r from-primary to-violet-500 bg-clip-text text-transparent">
                KnowledgeOS
              </span>
            )}
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:block rounded-lg p-1.5 hover:bg-muted/80 text-muted-foreground"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 ${
                  active
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-[1.02]'
                    : 'hover:bg-muted/80 text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className={`h-5 w-5 shrink-0 ${active ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'}`} />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer Controls */}
        <div className="border-t border-border p-3 space-y-2">
          {/* Theme Toggler */}
          <button
            onClick={toggleTheme}
            className="flex w-full items-center space-x-3 rounded-xl px-3 py-3 text-sm font-medium text-muted-foreground hover:bg-muted/80 hover:text-foreground transition-all duration-200"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="h-5 w-5 text-amber-500" />
                {!collapsed && <span>Light Mode</span>}
              </>
            ) : (
              <>
                <Moon className="h-5 w-5 text-indigo-500" />
                {!collapsed && <span>Dark Mode</span>}
              </>
            )}
          </button>

          {/* User Profile Info */}
          {!collapsed && (
            <div className="flex items-center space-x-3 px-3 py-2 bg-muted/30 rounded-xl border border-border/50">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                {user?.full_name ? user.full_name[0].toUpperCase() : user?.email[0].toUpperCase()}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-xs font-semibold text-foreground">
                  {user?.full_name || 'User Profile'}
                </p>
                <span className="inline-flex items-center rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-medium text-primary">
                  {user?.role}
                </span>
              </div>
            </div>
          )}

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="flex w-full items-center space-x-3 rounded-xl px-3 py-3 text-sm font-medium text-destructive hover:bg-destructive/10 transition-all duration-200"
          >
            <LogOut className="h-5 w-5 shrink-0" />
            {!collapsed && <span>Log Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col overflow-hidden bg-background">
        <header className="flex h-16 items-center justify-between border-b border-border bg-card/30 px-6 backdrop-blur-md md:hidden">
          <span className="font-outfit text-lg font-bold tracking-tight bg-gradient-to-r from-primary to-violet-500 bg-clip-text text-transparent">
            KnowledgeOS
          </span>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="rounded-lg p-2 hover:bg-muted text-muted-foreground"
          >
            <Menu className="h-6 w-6" />
          </button>
        </header>

        {/* Central View Outlet */}
        <div className="flex-1 overflow-y-auto px-6 py-6 md:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default SidebarLayout;
