import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { apiService } from '@services/api';
import { Card } from '@components/Card';
import { Modal } from '@components/Modal';
import { Button } from '@components/Button';
import { Input } from '@components/Input';
import { Select } from '@components/Select';
import { SkeletonList } from '@components/Skeleton';
import { useSocketStore } from '@store/socketStore';
import { SwipeableJobItem } from './SwipeableJobItem';
import { PullToRefresh } from '@components/PullToRefresh';
import { useHaptic } from '@hooks/useHaptic';

export const MissionControlScreen: React.FC = () => {
  const queryClient = useQueryClient();
  const haptic = useHaptic();
  const { socket, windows, jobs } = useSocketStore();
  const [editingJob, setEditingJob] = useState<any>(null);
  const [rescheduleJob, setRescheduleJob] = useState<any>(null);

  const { data: jobGroups = [], isLoading, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: apiService.getJobs,
    refetchInterval: 5000,
    // Use socket data if available
    initialData: jobs,
  });
  
  // Debug logging
  React.useEffect(() => {
    console.log('Socket jobs:', jobs);
    console.log('Query jobGroups:', jobGroups);
  }, [jobs, jobGroups]);
  
  const handleRefresh = async () => {
    haptic.success();
    await refetch();
  };

  useEffect(() => {
    if (socket) {
      socket.emit('get_jobs');
    }
  }, [socket]);

  const cancelMutation = useMutation({
    mutationFn: apiService.cancelJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success('Job cancelled');
    },
    onError: () => {
      toast.error('Failed to cancel job');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: apiService.deleteJobHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success('Deleted from history');
    },
    onError: () => {
      toast.error('Failed to delete');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ jobId, data }: any) => apiService.updateJob(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success('Job updated');
      setEditingJob(null);
    },
    onError: () => {
      toast.error('Failed to update job');
    },
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ jobId, newTime }: any) => apiService.rescheduleJob(jobId, newTime),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success('Job rescheduled');
      setRescheduleJob(null);
    },
    onError: () => {
      toast.error('Failed to reschedule job');
    },
  });


  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto pb-20 pt-20">
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold mb-6">Mission Control</h1>
          <SkeletonList count={3} />
        </div>
      </div>
    );
  }

  const totalJobs = jobGroups.reduce((sum, group) => sum + group.jobs.length, 0);
  const pendingJobs = jobGroups.reduce((sum, group) => 
    sum + group.jobs.filter((job: any) => job.status === 'PENDING').length, 0
  );

  return (
    <PullToRefresh onRefresh={handleRefresh}>
      <div className="h-full overflow-y-auto pb-20 pt-20">
        <div className="px-4 py-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold mb-2">Mission Control</h1>
          <p className="text-neutral-400">
            {totalJobs} total jobs • {pendingJobs} pending
          </p>
        </motion.div>

        {/* Job Groups */}
        <AnimatePresence>
          {jobGroups.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <p className="text-neutral-400">No scheduled jobs</p>
            </motion.div>
          ) : (
            <motion.div className="space-y-4">
              {jobGroups.map((group, groupIndex) => (
                <motion.div
                  key={group.job_group_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: groupIndex * 0.1 }}
                >
                  <Card noPadding>
                    <div className="p-4 border-b border-white/10">
                      <h3 className="font-medium">
                        {group.target_title || `Window ${group.target_hwnd}`}
                      </h3>
                      <p className="text-sm text-neutral-400 mt-1">
                        {group.jobs.filter((j: any) => j.status === 'PENDING').length} of {group.jobs.length} pending
                      </p>
                    </div>
                    
                    <div className="divide-y divide-white/5">
                      {group.jobs.map((job: any) => (
                        <SwipeableJobItem
                          key={job.id}
                          job={job}
                          onEdit={() => setEditingJob(job)}
                          onReschedule={() => setRescheduleJob(job)}
                          onCancel={() => cancelMutation.mutate(job.id)}
                          onDelete={() => deleteMutation.mutate(job.id)}
                        />
                      ))}
                    </div>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Edit Modal */}
        <Modal
          isOpen={!!editingJob}
          onClose={() => setEditingJob(null)}
          title="Edit Job"
        >
          {editingJob && (
            <div className="p-6 space-y-4">
              <textarea
                defaultValue={editingJob.message_text}
                className="w-full min-h-[100px] p-4 bg-neutral-800 rounded-xl border border-white/10"
                id="edit-message"
              />
              
              <Select
                label="Target Window"
                options={windows.map(w => ({
                  value: w.hwnd,
                  label: w.title || `Window ${w.hwnd}`,
                }))}
                value={editingJob.target_hwnd}
                onChange={() => {}}
              />
              
              <div className="flex space-x-3">
                <Button
                  variant="ghost"
                  onClick={() => setEditingJob(null)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    const message = (document.getElementById('edit-message') as HTMLTextAreaElement).value;
                    updateMutation.mutate({
                      jobId: editingJob.id,
                      data: { message_text: message },
                    });
                  }}
                  isLoading={updateMutation.isPending}
                >
                  Save Changes
                </Button>
              </div>
            </div>
          )}
        </Modal>

        {/* Reschedule Modal */}
        <Modal
          isOpen={!!rescheduleJob}
          onClose={() => setRescheduleJob(null)}
          title="Reschedule Job"
        >
          {rescheduleJob && (
            <div className="p-6 space-y-4">
              <Input
                type="datetime-local"
                label="New Time"
                defaultValue={rescheduleJob.scheduled_time.slice(0, 16)}
                id="reschedule-time"
              />
              
              <div className="flex space-x-3">
                <Button
                  variant="ghost"
                  onClick={() => setRescheduleJob(null)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    const newTime = (document.getElementById('reschedule-time') as HTMLInputElement).value;
                    rescheduleMutation.mutate({
                      jobId: rescheduleJob.id,
                      newTime: new Date(newTime).toISOString(),
                    });
                  }}
                  isLoading={rescheduleMutation.isPending}
                >
                  Reschedule
                </Button>
              </div>
            </div>
          )}
        </Modal>
        </div>
      </div>
    </PullToRefresh>
  );
};