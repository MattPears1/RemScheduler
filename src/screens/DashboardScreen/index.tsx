import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { HiMicrophone, HiChartBar, HiArchive, HiSparkles } from 'react-icons/hi';
import { useSocketStore } from '@store/socketStore';
import { Card } from '@components/Card';
import { FloatingActionButton } from '@components/FloatingActionButton';
import { useHaptic } from '@hooks/useHaptic';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

interface ActionCard {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  gradient: string;
}

const actionCards: ActionCard[] = [
  {
    id: 'create',
    title: 'Create New Task',
    description: 'Voice or type your command',
    icon: <HiMicrophone className="w-8 h-8" />,
    path: '/create',
    gradient: 'from-blue-500 to-purple-600',
  },
  {
    id: 'control',
    title: 'Mission Control',
    description: 'Manage scheduled tasks',
    icon: <HiChartBar className="w-8 h-8" />,
    path: '/mission-control',
    gradient: 'from-green-500 to-teal-600',
  },
  {
    id: 'messages',
    title: 'Saved Messages',
    description: 'Your message library',
    icon: <HiArchive className="w-8 h-8" />,
    path: '/messages',
    gradient: 'from-orange-500 to-red-600',
  },
];

export const DashboardScreen: React.FC = () => {
  const navigate = useNavigate();
  const haptic = useHaptic();
  const { connectSocket, isAgentOnline, jobs } = useSocketStore();

  useEffect(() => {
    connectSocket();
  }, [connectSocket]);

  const pendingJobs = jobs.reduce((count, group) => {
    return count + group.jobs.filter((job: any) => job.status === 'PENDING').length;
  }, 0);
  
  const handleCardClick = (path: string) => {
    haptic.light();
    navigate(path);
  };

  return (
    <div className="h-full overflow-y-auto pb-20 pt-20">
      <div className="px-4 py-6">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
          <p className="text-neutral-400">
            {isAgentOnline ? 'Agent is online and ready' : 'Waiting for agent connection'}
          </p>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-2 gap-4 mb-8"
        >
          <Card className="p-4 text-center">
            <p className="text-3xl font-bold gradient-text">{pendingJobs}</p>
            <p className="text-sm text-neutral-400 mt-1">Pending Tasks</p>
          </Card>
          <Card className="p-4 text-center">
            <p className="text-3xl font-bold text-green-500">
              {isAgentOnline ? 'Online' : 'Offline'}
            </p>
            <p className="text-sm text-neutral-400 mt-1">Agent Status</p>
          </Card>
        </motion.div>

        {/* Action Cards */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid gap-4"
        >
          {actionCards.map((card) => (
            <motion.div
              key={card.id}
              variants={item}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Card
                onClick={() => handleCardClick(card.path)}
                className="cursor-pointer overflow-hidden group"
                noPadding
              >
                <div className="relative p-6">
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-10 group-hover:opacity-20 transition-opacity`}
                  />
                  <div className="relative flex items-center space-x-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${card.gradient} text-white`}>
                      {card.icon}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-1">{card.title}</h3>
                      <p className="text-sm text-neutral-400">{card.description}</p>
                    </div>
                    <motion.div
                      initial={{ x: -10, opacity: 0 }}
                      whileHover={{ x: 0, opacity: 1 }}
                      className="text-neutral-400"
                    >
                      →
                    </motion.div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Tips */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl border border-white/10"
        >
          <div className="flex items-center space-x-2 mb-2">
            <HiSparkles className="w-5 h-5 text-blue-400" />
            <h3 className="font-medium">Pro Tip</h3>
          </div>
          <p className="text-sm text-neutral-300">
            Use voice commands for faster task creation. Just tap the microphone and speak naturally!
          </p>
        </motion.div>
      </div>
      
      {/* Floating Action Button */}
      <FloatingActionButton onClick={() => handleCardClick('/create')} />
    </div>
  );
};