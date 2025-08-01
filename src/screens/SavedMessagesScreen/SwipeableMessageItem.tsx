import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, useAnimation } from 'framer-motion';
import { HiTrash, HiPaperAirplane, HiClock } from 'react-icons/hi';
import { format } from 'date-fns';
import { useGesture } from 'react-use-gesture';
import { SavedMessage } from '@types';

interface SwipeableMessageItemProps {
  message: SavedMessage;
  onDelete: () => void;
  onSchedule: () => void;
}

export const SwipeableMessageItem: React.FC<SwipeableMessageItemProps> = ({
  message,
  onDelete,
  onSchedule,
}) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const x = useMotionValue(0);
  const controls = useAnimation();
  
  const background = useTransform(
    x,
    [-100, 0, 100],
    ['rgb(239, 68, 68)', 'rgb(0, 0, 0)', 'rgb(34, 197, 94)']
  );

  const bind = useGesture({
    onDrag: ({ movement: [mx], velocity, direction: [dx] }) => {
      x.set(mx);
      
      if (velocity > 0.5 && Math.abs(mx) > 100) {
        if (dx > 0) {
          // Swipe right to schedule
          controls.start({ x: 300, opacity: 0 });
          setTimeout(onSchedule, 300);
        } else {
          // Swipe left to delete
          controls.start({ x: -300, opacity: 0 });
          setTimeout(onDelete, 300);
        }
      }
    },
    onDragEnd: () => {
      if (Math.abs(x.get()) < 100) {
        controls.start({ x: 0 });
      }
    },
  });

  return (
    <motion.div
      className="relative overflow-hidden rounded-xl"
      style={{ backgroundColor: background }}
      layout
    >
      {/* Background Actions */}
      <div className="absolute inset-0 flex items-center justify-between px-6">
        <span className="text-white font-medium flex items-center">
          <HiTrash className="w-5 h-5 mr-2" />
          Delete
        </span>
        <span className="text-white font-medium flex items-center">
          <HiPaperAirplane className="w-5 h-5 mr-2" />
          Schedule
        </span>
      </div>

      {/* Main Content */}
      <motion.div
        {...bind()}
        style={{ x }}
        animate={controls}
        className="relative bg-black p-4 cursor-grab active:cursor-grabbing rounded-xl"
        onClick={() => !isRevealed && setIsRevealed(true)}
      >
        <div className="space-y-2">
          <p className="text-sm line-clamp-2">{message.message_text || message.text}</p>
          
          <div className="flex items-center justify-between text-xs text-neutral-400">
            <div className="flex items-center space-x-1">
              <HiClock className="w-3 h-3" />
              <span>Created {format(new Date(message.created_at), 'MMM d, yyyy')}</span>
            </div>
            {message.use_count && message.use_count > 0 && (
              <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full">
                Used {message.use_count} time{message.use_count !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {isRevealed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-3 pt-3 border-t border-white/10 flex space-x-2"
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSchedule();
              }}
              className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-400 transition-colors"
            >
              <HiPaperAirplane className="w-4 h-4" />
              <span className="text-xs">Schedule</span>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
            >
              <HiTrash className="w-4 h-4" />
              <span className="text-xs">Delete</span>
            </button>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};