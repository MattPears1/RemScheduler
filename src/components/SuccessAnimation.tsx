import React from 'react';
import { motion } from 'framer-motion';
import { HiCheck } from 'react-icons/hi';

interface SuccessAnimationProps {
  isVisible: boolean;
}

export const SuccessAnimation: React.FC<SuccessAnimationProps> = ({ isVisible }) => {
  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: [0, 1.2, 1] }}
        transition={{ duration: 0.5, times: [0, 0.6, 1] }}
        className="bg-green-500 rounded-full p-8"
      >
        <motion.div
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <HiCheck className="w-16 h-16 text-white" />
        </motion.div>
      </motion.div>
    </motion.div>
  );
};