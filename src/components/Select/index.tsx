import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HiChevronDown, HiCheck } from 'react-icons/hi';
import { cn } from '@utils/cn';

interface Option {
  value: string | number;
  label: string;
  description?: string;
}

interface SelectProps {
  options: Option[];
  value?: string | number;
  onChange?: (value: string | number) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  name?: string;
  required?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  label,
  error,
  disabled,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<Option | null>(
    options.find(opt => opt.value === value) || null
  );
  const selectRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: Option) => {
    setSelectedOption(option);
    onChange?.(option.value);
    setIsOpen(false);
  };

  return (
    <div ref={selectRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-neutral-400 mb-2">
          {label}
        </label>
      )}
      
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={cn(
          'w-full h-14 px-4 bg-neutral-900 border border-white/10 rounded-xl',
          'text-white text-left',
          'flex items-center justify-between',
          'transition-all duration-200',
          'focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
          error && 'border-red-500',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        disabled={disabled}
      >
        <span className={cn(!selectedOption && 'text-neutral-400')}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <HiChevronDown
          className={cn(
            'w-5 h-5 text-neutral-400 transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute z-50 w-full mt-2 bg-neutral-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden"
          >
            <div className="max-h-60 overflow-y-auto scrollbar-none">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={cn(
                    'w-full px-4 py-3 text-left',
                    'hover:bg-white/5 transition-colors',
                    'flex items-center justify-between',
                    selectedOption?.value === option.value && 'bg-white/10'
                  )}
                >
                  <div>
                    <div className="text-white">{option.label}</div>
                    {option.description && (
                      <div className="text-sm text-neutral-400 mt-1">
                        {option.description}
                      </div>
                    )}
                  </div>
                  {selectedOption?.value === option.value && (
                    <HiCheck className="w-5 h-5 text-blue-500" />
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
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
};