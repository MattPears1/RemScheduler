import React from 'react';
import { motion } from 'framer-motion';
import { useLazyLoad } from '@hooks/useLazyLoad';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({ src, alt, className }) => {
  const { ref, isIntersecting } = useLazyLoad();

  return (
    <div ref={ref as React.RefObject<HTMLDivElement>} className={className}>
      {isIntersecting ? (
        <motion.img
          src={src}
          alt={alt}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full bg-neutral-800 animate-pulse" />
      )}
    </div>
  );
};