import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, onFocus, onBlur, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const hasValue = props.value && String(props.value).length > 0;

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    return (
      <div className="relative">
        <div className="relative">
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {icon}
            </div>
          )}
          
          <input
            ref={ref}
            className={cn(
              'w-full h-14 px-4 bg-neutral-900 border border-white/10 rounded-xl',
              'text-white placeholder-transparent',
              'transition-all duration-200',
              'focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
              icon && 'pl-12',
              label && 'pt-5',
              className
            )}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={label || props.placeholder}
            {...props}
          />
          
          {label && (
            <motion.label
              className={cn(
                'absolute left-4 text-neutral-400 pointer-events-none',
                'transition-all duration-200',
                icon && 'left-12'
              )}
              animate={{
                top: isFocused || hasValue ? '8px' : '50%',
                fontSize: isFocused || hasValue ? '12px' : '16px',
                y: isFocused || hasValue ? 0 : '-50%',
              }}
            >
              {label}
            </motion.label>
          )}
        </div>
        
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-1 text-sm text-red-500 px-4"
          >
            {error}
          </motion.p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';