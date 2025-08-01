import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@utils/cn';

interface CardProps extends HTMLMotionProps<'div'> {
  variant?: 'default' | 'glass' | 'elevated';
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
  className,
  variant = 'default',
  noPadding = false,
  children,
  ...props
}) => {
  const variants = {
    default: 'bg-neutral-900 border border-white/10',
    glass: 'glass',
    elevated: 'bg-neutral-900 border border-white/10 shadow-xl',
  };

  return (
    <motion.div
      className={cn(
        'rounded-2xl overflow-hidden',
        variants[variant],
        !noPadding && 'p-6',
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};