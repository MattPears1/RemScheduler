import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSocketStore } from '@store/socketStore';

export const AgentStatus: React.FC = () => {
  const { isAgentOnline, socket } = useSocketStore();
  const [isSocketConnected, setIsSocketConnected] = React.useState(false);

  React.useEffect(() => {
    if (socket) {
      setIsSocketConnected(socket.connected);
      
      const handleConnect = () => setIsSocketConnected(true);
      const handleDisconnect = () => setIsSocketConnected(false);
      
      socket.on('connect', handleConnect);
      socket.on('disconnect', handleDisconnect);
      
      return () => {
        socket.off('connect', handleConnect);
        socket.off('disconnect', handleDisconnect);
      };
    }
  }, [socket]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="fixed top-20 left-1/2 -translate-x-1/2 z-50"
      >
        {isSocketConnected && isAgentOnline ? (
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 backdrop-blur-lg rounded-full border border-green-500/30">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-400">
              Connected
            </span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 backdrop-blur-lg rounded-full border border-red-500/30">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-red-400">
              {!isSocketConnected ? 'Disconnected from Server' : 'Local Agent Offline'}
            </span>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};