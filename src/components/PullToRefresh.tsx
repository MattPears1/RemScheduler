import React, { useState, useRef } from 'react';
import { motion, useMotionValue, useTransform, useAnimation } from 'framer-motion';
import { HiRefresh } from 'react-icons/hi';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: React.ReactNode;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({ onRefresh, children }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const y = useMotionValue(0);
  const controls = useAnimation();

  const pullOpacity = useTransform(y, [0, 50, 100], [0, 1, 1]);
  const pullScale = useTransform(y, [0, 100], [0.5, 1]);

  const handleDragEnd = async () => {
    if (y.get() > 80) {
      setIsRefreshing(true);
      controls.start({ y: 60 });
      
      // Haptic feedback
      if ('vibrate' in navigator) {
        navigator.vibrate(10);
      }
      
      await onRefresh();
      
      setIsRefreshing(false);
      controls.start({ y: 0 });
    } else {
      controls.start({ y: 0 });
    }
  };

  return (
    <div ref={containerRef} className="relative h-full overflow-hidden">
      {/* Pull indicator */}
      <motion.div
        className="absolute top-0 left-0 right-0 flex items-center justify-center pointer-events-none"
        style={{
          opacity: pullOpacity,
          y,
        }}
      >
        <motion.div
          className="bg-white/10 backdrop-blur-sm rounded-full p-3"
          style={{ scale: pullScale }}
        >
          <motion.div
            animate={isRefreshing ? { rotate: 360 } : {}}
            transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
          >
            <HiRefresh className="w-6 h-6 text-white" />
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Content */}
      <motion.div
        drag="y"
        dragConstraints={{ top: 0, bottom: 100 }}
        dragElastic={0.5}
        onDragEnd={handleDragEnd}
        animate={controls}
        style={{ y }}
        className="h-full"
      >
        {children}
      </motion.div>
    </div>
  );
};