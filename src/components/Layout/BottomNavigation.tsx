import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  HiHome, 
  HiPlus, 
  HiChartBar, 
  HiArchive 
} from 'react-icons/hi';
import { cn } from '@utils/cn';

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  {
    path: '/dashboard',
    icon: <HiHome className="w-6 h-6" />,
    label: 'Home',
  },
  {
    path: '/create',
    icon: <HiPlus className="w-6 h-6" />,
    label: 'Create',
  },
  {
    path: '/mission-control',
    icon: <HiChartBar className="w-6 h-6" />,
    label: 'Control',
  },
  {
    path: '/messages',
    icon: <HiArchive className="w-6 h-6" />,
    label: 'Messages',
  },
];

export const BottomNavigation: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-neutral-950/80 backdrop-blur-xl border-t border-white/10 safe-bottom">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'relative flex flex-col items-center justify-center w-full h-full px-3 py-2 transition-colors',
                'touch-manipulation active:scale-95 transition-transform',
                isActive ? 'text-blue-500' : 'text-neutral-400'
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="bottomNavIndicator"
                  className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-blue-500 rounded-full"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
              
              <motion.div
                whileTap={{ scale: 0.9 }}
                className="relative"
              >
                {item.icon}
              </motion.div>
              
              <span className="text-xs mt-1 font-medium">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};