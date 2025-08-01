import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@utils/cn';
import { cva, type VariantProps } from 'class-variance-authority';
import { TouchRipple } from '../TouchRipple';
import { LoadingDots } from '../LoadingDots';
import { useHaptic } from '@hooks/useHaptic';

const buttonVariants = cva(
  'relative inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 touch-manipulation active:scale-95 disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-black overflow-hidden',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-600/20',
        secondary: 'bg-neutral-800 text-white hover:bg-neutral-700 border border-white/10',
        ghost: 'bg-transparent hover:bg-white/5 text-white',
        danger: 'bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-600/20',
        glass: 'glass text-white hover:bg-white/10',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-11 px-6 text-base',
        lg: 'h-14 px-8 text-lg',
        icon: 'h-10 w-10',
      },
      fullWidth: {
        true: 'w-full',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends Omit<HTMLMotionProps<'button'>, 'size' | 'children'>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  children?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, fullWidth, isLoading, children, onClick, ...props }, ref) => {
    const haptic = useHaptic();
    
    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      haptic.light();
      onClick?.(e);
    };
    
    return (
      <motion.button
        ref={ref}
        className={cn(buttonVariants({ variant, size, fullWidth, className }))}
        whileTap={{ scale: 0.95 }}
        disabled={isLoading || props.disabled}
        onClick={handleClick}
        {...props}
      >
        <TouchRipple className="absolute inset-0">
          <div className="relative z-10 flex items-center justify-center w-full h-full">
            {isLoading ? <LoadingDots /> : children}
          </div>
        </TouchRipple>
      </motion.button>
    );
  }
);

Button.displayName = 'Button';