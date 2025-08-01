import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { HiPlus } from 'react-icons/hi';

export const FAB: React.FC = () => {
  return (
    <Link to="/create">
      <motion.button
        className="fixed bottom-20 right-4 w-14 h-14 bg-blue-600 rounded-full shadow-lg flex items-center justify-center z-50"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        <HiPlus className="w-6 h-6 text-white" />
      </motion.button>
    </Link>
  );
};