import React from 'react';
import { motion } from 'framer-motion';
import { HiLogout } from 'react-icons/hi';
import { useAuthStore } from '@store/authStore';
import { useSocketStore } from '@store/socketStore';
import { cn } from '@utils/cn';
import { Button } from '@components/Button';

export const Header: React.FC = () => {
  const { logout } = useAuthStore();
  const { isAgentOnline } = useSocketStore();

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-black/80 backdrop-blur-xl border-b border-white/10 safe-top">
      <div className="flex items-center justify-between h-14 px-4">
        <div className="flex items-center space-x-3">
          <motion.h1 
            className="text-lg font-semibold gradient-text"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            RemScheduler
          </motion.h1>
          
          <div className="flex items-center space-x-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isAgentOnline ? "bg-green-500" : "bg-red-500"
            )} />
            <span className="text-xs text-neutral-400">
              {isAgentOnline ? 'Agent Online' : 'Agent Offline'}
            </span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={logout}
          className="text-neutral-400"
        >
          <HiLogout className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
};