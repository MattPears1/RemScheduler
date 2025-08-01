import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HiPlus } from 'react-icons/hi';

interface FloatingActionButtonProps {
  onClick: () => void;
  isVisible?: boolean;
}

export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({ 
  onClick, 
  isVisible = true 
}) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.button
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          exit={{ scale: 0, rotate: 180 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onClick}
          className="fixed bottom-24 right-6 w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full shadow-lg flex items-center justify-center z-40"
          style={{
            boxShadow: '0 4px 20px rgba(59, 130, 246, 0.5)',
          }}
        >
          <HiPlus className="w-6 h-6 text-white" />
        </motion.button>
      )}
    </AnimatePresence>
  );
};