import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, useAnimation } from 'framer-motion';
import { HiClock, HiCheck, HiX, HiPencil, HiTrash, HiCalendar } from 'react-icons/hi';
import { format } from 'date-fns';
import { useGesture } from 'react-use-gesture';
import type { ScheduledJob } from '@types';

interface SwipeableJobItemProps {
  job: ScheduledJob & { effectiveStatus?: string };
  onEdit: () => void;
  onReschedule: () => void;
  onCancel: () => void;
  onDelete: () => void;
}

export const SwipeableJobItem: React.FC<SwipeableJobItemProps> = ({
  job,
  onEdit,
  onReschedule,
  onCancel,
  onDelete,
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
        if (dx > 0 && job.status === 'SENT') {
          // Swipe right to delete sent messages
          controls.start({ x: 300, opacity: 0 });
          setTimeout(onDelete, 300);
        } else if (dx < 0 && (job.status === 'PENDING' || job.effectiveStatus === 'EXPIRED')) {
          // Swipe left to cancel pending/expired jobs
          controls.start({ x: -300, opacity: 0 });
          setTimeout(onCancel, 300);
        }
      }
    },
    onDragEnd: () => {
      if (Math.abs(x.get()) < 100) {
        controls.start({ x: 0 });
      }
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'text-yellow-500 bg-yellow-500/10';
      case 'EXPIRED': return 'text-orange-500 bg-orange-500/10';
      case 'SENT': return 'text-green-500 bg-green-500/10';
      case 'FAILED': return 'text-red-500 bg-red-500/10';
      default: return '';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING': return <HiClock className="w-4 h-4" />;
      case 'EXPIRED': return <HiX className="w-4 h-4" />;
      case 'SENT': return <HiCheck className="w-4 h-4" />;
      case 'FAILED': return <HiX className="w-4 h-4" />;
      default: return null;
    }
  };

  return (
    <motion.div
      className="relative overflow-hidden"
      style={{ backgroundColor: background }}
    >
      {/* Background Actions */}
      <div className="absolute inset-0 flex items-center justify-between px-6">
        <span className="text-white font-medium">
          {(job.status === 'PENDING' || job.effectiveStatus === 'EXPIRED') ? 'Cancel' : ''}
        </span>
        <span className="text-white font-medium">
          {job.status === 'SENT' ? 'Delete' : ''}
        </span>
      </div>

      {/* Main Content */}
      <motion.div
        {...bind()}
        style={{ x }}
        animate={controls}
        className="relative bg-black p-4 cursor-grab active:cursor-grabbing"
        onClick={() => !isRevealed && setIsRevealed(true)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 mr-4">
            <p className="text-sm line-clamp-2">{job.message_text}</p>
            <p className="text-xs text-neutral-400 mt-1">
              {format(new Date(job.scheduled_time), 'MMM d, h:mm a')}
            </p>
          </div>
          
          <div className={`px-2 py-1 rounded-full flex items-center space-x-1 ${getStatusColor(job.effectiveStatus || job.status)}`}>
            {getStatusIcon(job.effectiveStatus || job.status)}
            <span className="text-xs font-medium">{job.effectiveStatus || job.status}</span>
          </div>
        </div>

        {/* Action Buttons */}
        {isRevealed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-3 pt-3 border-t border-white/10 flex space-x-2"
          >
            {(job.status === 'PENDING' || job.effectiveStatus === 'EXPIRED') && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit();
                  }}
                  className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <HiPencil className="w-4 h-4" />
                  <span className="text-xs">Edit</span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onReschedule();
                  }}
                  className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <HiCalendar className="w-4 h-4" />
                  <span className="text-xs">Reschedule</span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onCancel();
                  }}
                  className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                >
                  <HiX className="w-4 h-4" />
                  <span className="text-xs">Cancel</span>
                </button>
              </>
            )}
            {job.status === 'SENT' && (
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
            )}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};