import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HiWifi } from 'react-icons/hi';
import { useOnlineStatus } from '@hooks/useOnlineStatus';

export const OfflineIndicator: React.FC = () => {
  const isOnline = useOnlineStatus();

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          className="fixed top-16 left-0 right-0 z-50 flex justify-center px-4"
        >
          <div className="bg-orange-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
            <HiWifi className="w-5 h-5" />
            <span className="text-sm font-medium">You're offline</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};