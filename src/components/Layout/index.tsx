import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { BottomNavigation } from './BottomNavigation';
import { Header } from './Header';
import { FAB } from './FAB';
import { useLocation } from 'react-router-dom';
import { useSocketStore } from '@store/socketStore';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const showFAB = location.pathname !== '/create';
  const { connectSocket, socket } = useSocketStore();

  useEffect(() => {
    if (!socket) {
      connectSocket();
    }
  }, [socket, connectSocket]);

  return (
    <div className="flex flex-col h-screen bg-black">
      <Header />
      
      <main className="flex-1 overflow-hidden relative">
        {children || <Outlet />}
      </main>

      <BottomNavigation />
      
      {showFAB && <FAB />}
    </div>
  );
};