import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { HiMicrophone, HiStop, HiSave } from 'react-icons/hi';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';

import { useSocketStore } from '@store/socketStore';
import { apiService } from '@services/api';
import { Button } from '@components/Button';
import { Input } from '@components/Input';
import { Select } from '@components/Select';
import { Card } from '@components/Card';
import { useRecording } from '@hooks/useRecording';
import { SuccessAnimation } from '@components/SuccessAnimation';
import { useHaptic } from '@hooks/useHaptic';

const taskSchema = z.object({
  message: z.string().min(1, 'Message is required'),
  target_hwnd: z.number().min(1, 'Please select a window'),
  start_time: z.string().min(1, 'Start time is required'),
  repetitions: z.number().min(1).max(100),
  interval_value: z.number().min(1),
  interval_unit: z.enum(['seconds', 'minutes', 'hours']),
  use_sequence: z.boolean(),
});

type TaskForm = z.infer<typeof taskSchema>;

export const CreateTaskScreen: React.FC = () => {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const { windows } = useSocketStore();
  const [isSaving, setIsSaving] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [sequences, setSequences] = useState<string[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  
  const { isRecording, startRecording, stopRecording, transcript } = useRecording();

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TaskForm>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      message: '',
      repetitions: 1,
      interval_value: 60,
      interval_unit: 'minutes',
      use_sequence: false,
    },
  });

  const message = watch('message');
  const useSequence = watch('use_sequence');
  const repetitions = watch('repetitions');

  useEffect(() => {
    if (transcript) {
      setValue('message', transcript);
    }
  }, [transcript, setValue]);

  useEffect(() => {
    if (useSequence && repetitions > 0) {
      setSequences(new Array(repetitions).fill(''));
    }
  }, [useSequence, repetitions]);

  const handleSaveMessage = async () => {
    if (!message) {
      toast.error('Please enter a message to save');
      return;
    }

    setIsSaving(true);
    try {
      await apiService.saveMessage(message);
      haptic.success();
      toast.success('Message saved!');
    } catch (error) {
      haptic.error();
      toast.error('Failed to save message');
    } finally {
      setIsSaving(false);
    }
  };

  const onSubmit = async (data: TaskForm) => {
    setIsScheduling(true);
    try {
      const intervalSeconds = 
        data.interval_value * 
        (data.interval_unit === 'minutes' ? 60 : data.interval_unit === 'hours' ? 3600 : 1);

      const scheduleData = {
        message: data.message,
        target_hwnd: data.target_hwnd,
        target_title: windows.find(w => w.hwnd === data.target_hwnd)?.title || '',
        start_time: new Date(data.start_time).toISOString(),
        repetitions: data.repetitions,
        interval_seconds: intervalSeconds,
        use_different_messages: data.use_sequence,
        messages: data.use_sequence ? sequences.filter(s => s) : undefined,
      };

      await apiService.scheduleTask(scheduleData);
      haptic.success();
      setShowSuccess(true);
      toast.success('Task scheduled successfully!');
      setTimeout(() => {
        navigate('/mission-control');
      }, 1000);
    } catch (error) {
      haptic.error();
      toast.error('Failed to schedule task');
    } finally {
      setIsScheduling(false);
    }
  };

  const windowOptions = windows.map(w => ({
    value: w.hwnd,
    label: w.title || `Window ${w.hwnd}`,
    description: w.process,
  }));

  return (
    <div className="h-full overflow-y-auto pb-20 pt-20">
      <form onSubmit={handleSubmit(onSubmit)} className="px-4 py-6 space-y-6">
        {/* Message Section */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Your Message</h2>
          
          {/* Voice Recording */}
          <div className="mb-4">
            <motion.button
              type="button"
              whileTap={{ scale: 0.95 }}
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-full h-24 rounded-2xl flex flex-col items-center justify-center space-y-2 transition-all ${
                isRecording 
                  ? 'bg-red-500/20 border-2 border-red-500' 
                  : 'bg-neutral-800 border-2 border-white/10'
              }`}
            >
              <motion.div
                animate={isRecording ? { scale: [1, 1.2, 1] } : {}}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                {isRecording ? (
                  <HiStop className="w-8 h-8 text-red-500" />
                ) : (
                  <HiMicrophone className="w-8 h-8 text-white" />
                )}
              </motion.div>
              <span className="text-sm">
                {isRecording ? 'Stop Recording' : 'Tap to Record'}
              </span>
            </motion.button>
          </div>

          {/* Text Input */}
          <div className="space-y-4">
            <textarea
              {...register('message')}
              placeholder="Or type your message here..."
              className="w-full min-h-[100px] p-4 bg-neutral-800 rounded-xl border border-white/10 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
            />
            {errors.message && (
              <p className="text-sm text-red-500">{errors.message.message}</p>
            )}

            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleSaveMessage}
              isLoading={isSaving}
              disabled={!message}
            >
              <HiSave className="w-4 h-4 mr-2" />
              Save Message
            </Button>
          </div>
        </Card>

        {/* Schedule Section */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Schedule Details</h2>
          
          <div className="space-y-4">
            {/* Target Window */}
            <Controller
              name="target_hwnd"
              control={control}
              render={({ field }) => (
                <Select
                  label="Target Window"
                  options={windowOptions}
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Select a window..."
                  error={errors.target_hwnd?.message}
                />
              )}
            />

            {/* Start Time */}
            <Input
              {...register('start_time')}
              type="datetime-local"
              label="Start Time"
              error={errors.start_time?.message}
            />

            {/* Repetitions & Interval */}
            <div className="grid grid-cols-2 gap-4">
              <Input
                {...register('repetitions', { valueAsNumber: true })}
                type="number"
                label="Repetitions"
                min={1}
                max={100}
                error={errors.repetitions?.message}
              />

              <div className="flex space-x-2">
                <div className="flex-1">
                  <Input
                    {...register('interval_value', { valueAsNumber: true })}
                    type="number"
                    label="Interval"
                    min={1}
                    error={errors.interval_value?.message}
                  />
                </div>
                <Controller
                  name="interval_unit"
                  control={control}
                  render={({ field }) => (
                    <Select
                      options={[
                        { value: 'seconds', label: 'Sec' },
                        { value: 'minutes', label: 'Min' },
                        { value: 'hours', label: 'Hr' },
                      ]}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
            </div>

            {/* Use Sequence */}
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                {...register('use_sequence')}
                type="checkbox"
                className="w-5 h-5 rounded bg-neutral-800 border-white/10 text-blue-500 focus:ring-blue-500/20"
              />
              <span>Use different messages for each repetition</span>
            </label>
          </div>
        </Card>

        {/* Sequence Builder */}
        <AnimatePresence>
          {useSequence && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <Card>
                <h3 className="text-lg font-medium mb-4">Message Sequence</h3>
                <div className="space-y-3">
                  {sequences.map((seq, index) => (
                    <Input
                      key={index}
                      value={seq}
                      onChange={(e) => {
                        const newSequences = [...sequences];
                        newSequences[index] = e.target.value;
                        setSequences(newSequences);
                      }}
                      placeholder={`Message ${index + 1}`}
                    />
                  ))}
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Submit Button */}
        <Button
          type="submit"
          fullWidth
          size="lg"
          isLoading={isScheduling}
          disabled={!message || !watch('target_hwnd')}
        >
          Schedule Task
        </Button>
      </form>
      
      {/* Success Animation */}
      <SuccessAnimation isVisible={showSuccess} />
    </div>
  );
};