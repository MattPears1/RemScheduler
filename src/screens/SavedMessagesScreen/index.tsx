import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { HiSearch, HiPaperAirplane, HiArchive } from 'react-icons/hi';
import toast from 'react-hot-toast';

import { apiService } from '@services/api';
import { SavedMessage } from '@types';
import { Input } from '@components/Input';
import { Button } from '@components/Button';
import { Modal } from '@components/Modal';
import { Select } from '@components/Select';
import { Skeleton } from '@components/Skeleton';
import { SwipeableMessageItem } from './SwipeableMessageItem';
import { useSocketStore } from '@store/socketStore';
import { useNavigate } from 'react-router-dom';

export const SavedMessagesScreen: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { windows } = useSocketStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMessage, setSelectedMessage] = useState<SavedMessage | null>(null);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);

  const { savedMessages } = useSocketStore();
  
  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['saved-messages'],
    queryFn: apiService.getSavedMessages,
    // Use socket data if available, otherwise fetch from API
    initialData: savedMessages,
  });
  
  // Debug logging
  React.useEffect(() => {
    console.log('Socket savedMessages:', savedMessages);
    console.log('Query messages:', messages);
  }, [savedMessages, messages]);

  const deleteMutation = useMutation({
    mutationFn: apiService.deleteSavedMessage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-messages'] });
      toast.success('Message deleted');
    },
    onError: () => {
      toast.error('Failed to delete message');
    },
  });

  const scheduleMutation = useMutation({
    mutationFn: (data: any) => apiService.scheduleTask(data),
    onSuccess: () => {
      toast.success('Message scheduled!');
      setIsScheduleModalOpen(false);
      navigate('/mission-control');
    },
    onError: () => {
      toast.error('Failed to schedule message');
    },
  });

  const filteredMessages = messages.filter(msg =>
    (msg.message_text || msg.text).toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleQuickSchedule = (message: SavedMessage) => {
    setSelectedMessage(message);
    setIsScheduleModalOpen(true);
  };

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMessage) return;

    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    
    const scheduleData = {
      message: selectedMessage.message_text || selectedMessage.text,
      target_hwnd: Number(formData.get('target_hwnd')),
      target_title: windows.find(w => w.hwnd === Number(formData.get('target_hwnd')))?.title || '',
      start_time: new Date(formData.get('start_time') as string).toISOString(),
      repetitions: 1,
      interval_seconds: 0,
      use_different_messages: false,
    };

    scheduleMutation.mutate(scheduleData);
  };

  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto pb-20 pt-20">
        <div className="px-4 py-6">
          <h1 className="text-2xl font-bold mb-6">Saved Messages</h1>
          <Skeleton className="h-12 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto pb-20 pt-20">
      <div className="px-4 py-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold mb-2">Saved Messages</h1>
          <p className="text-neutral-400">
            {messages.length} saved message{messages.length !== 1 ? 's' : ''}
          </p>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6"
        >
          <div className="relative">
            <HiSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-neutral-800 rounded-xl border border-white/10 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </motion.div>

        {/* Messages List */}
        <AnimatePresence mode="popLayout">
          {filteredMessages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <HiArchive className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
              <p className="text-neutral-400">
                {searchQuery ? 'No messages found' : 'No saved messages yet'}
              </p>
            </motion.div>
          ) : (
            <motion.div className="space-y-3">
              {filteredMessages.map((message, index) => (
                <motion.div
                  key={message.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <SwipeableMessageItem
                    message={message}
                    onDelete={() => deleteMutation.mutate(message.id)}
                    onSchedule={() => handleQuickSchedule(message)}
                  />
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Schedule Modal */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        title="Schedule Message"
      >
        {selectedMessage && (
          <form onSubmit={handleSchedule} className="p-6 space-y-4">
            <div className="p-4 bg-neutral-800 rounded-lg">
              <p className="text-sm text-neutral-400 mb-1">Message:</p>
              <p className="line-clamp-3">{selectedMessage.message_text || selectedMessage.text}</p>
            </div>

            <Select
              name="target_hwnd"
              label="Target Window"
              options={windows.map(w => ({
                value: w.hwnd,
                label: w.title || `Window ${w.hwnd}`,
              }))}
              required
            />

            <Input
              name="start_time"
              type="datetime-local"
              label="Schedule Time"
              defaultValue={new Date(Date.now() + 300000).toISOString().slice(0, 16)}
              required
            />

            <div className="flex space-x-3">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsScheduleModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={scheduleMutation.isPending}
              >
                <HiPaperAirplane className="w-4 h-4 mr-2" />
                Schedule Now
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};