import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';

import { useAuthStore } from '@store/authStore';
import { Layout } from '@components/Layout';
import { LoginScreen } from '@screens/LoginScreen';
import { ProtectedRoute } from '@components/ProtectedRoute';
import { AnimatedRoutes } from '@components/AnimatedRoutes';
import { OfflineIndicator } from '@components/OfflineIndicator';
import { AgentStatus } from '@components/AgentStatus';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0, // No caching
      gcTime: 0, // No caching (v5 uses gcTime instead of cacheTime)
      retry: 1,
    },
  },
});

function App() {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/login" element={<LoginScreen />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <AnimatedRoutes />
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AnimatePresence>
      </Router>
      <Toaster
        position="bottom-center"
        toastOptions={{
          className: 'toast',
          duration: 4000,
          style: {
            background: '#1a1a1a',
            color: '#fff',
            borderRadius: '16px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
          },
        }}
      />
      <OfflineIndicator />
      <AgentStatus />
    </QueryClientProvider>
  );
}

export default App;