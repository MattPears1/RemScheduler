import React from 'react';
import { Outlet } from 'react-router-dom';
import { BottomNavigation } from './BottomNavigation';
import { Header } from './Header';
import { FAB } from './FAB';
import { useLocation } from 'react-router-dom';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const showFAB = location.pathname !== '/create';

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