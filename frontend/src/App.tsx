import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages list (Will create files shortly)
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ChatWorkspace from './pages/ChatWorkspace';
import Collections from './pages/Collections';
import Documents from './pages/Documents';
import Settings from './pages/Settings';
import AdminDashboard from './pages/AdminDashboard';

// Layout shell
import SidebarLayout from './layouts/SidebarLayout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm font-medium text-muted-foreground animate-pulse">Initializing KnowledgeOS...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

const AdminRoute: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return user?.role === 'ADMIN' ? <Outlet /> : <Navigate to="/" replace />;
};

const SessionExpiredDialog: React.FC = () => {
  const { showExpiredAlert, clearExpiredAlert } = useAuth();

  if (!showExpiredAlert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md rounded-xl bg-card p-6 shadow-2xl border border-border">
        <h3 className="text-xl font-bold text-foreground font-outfit">Session Expired</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Your active login session has expired or been terminated. Please log in again to restore access.
        </p>
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => {
              clearExpiredAlert();
              window.location.href = '/login';
            }}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all shadow-md shadow-primary/20"
          >
            Go to Login
          </button>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected dashboard workspace routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<SidebarLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<ChatWorkspace />} />
                <Route path="/collections" element={<Collections />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/settings" element={<Settings />} />
                
                {/* Admin-only routes */}
                <Route element={<AdminRoute />}>
                  <Route path="/admin" element={<AdminDashboard />} />
                </Route>
              </Route>
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <SessionExpiredDialog />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
