import React from 'react';
import { cn } from '@utils/cn';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'text',
  width,
  height,
  count = 1,
}) => {
  const baseClasses = 'animate-pulse bg-neutral-800';
  
  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {
    width: width || (variant === 'circular' ? 40 : '100%'),
    height: height || (variant === 'circular' ? 40 : variant === 'rectangular' ? 100 : 16),
  };

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={cn(
            baseClasses,
            variantClasses[variant],
            className,
            count > 1 && index < count - 1 && 'mb-2'
          )}
          style={style}
        />
      ))}
    </>
  );
};

export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-6 bg-neutral-900 rounded-2xl', className)}>
    <Skeleton variant="rectangular" height={200} className="mb-4" />
    <Skeleton count={2} className="mb-2" />
    <Skeleton width="60%" />
  </div>
);

export const SkeletonList: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="flex items-center space-x-4 p-4 bg-neutral-900 rounded-xl">
        <Skeleton variant="circular" />
        <div className="flex-1">
          <Skeleton className="mb-2" />
          <Skeleton width="70%" />
        </div>
      </div>
    ))}
  </div>
);