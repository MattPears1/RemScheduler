import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

import { DashboardScreen } from '@screens/DashboardScreen';
import { CreateTaskScreen } from '@screens/CreateTaskScreen';
import { MissionControlScreen } from '@screens/MissionControlScreen';
import { SavedMessagesScreen } from '@screens/SavedMessagesScreen';
import { AnimatedPage } from '@components/AnimatedPage';

export const AnimatedRoutes: React.FC = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={
          <AnimatedPage>
            <DashboardScreen />
          </AnimatedPage>
        } />
        <Route path="create" element={
          <AnimatedPage>
            <CreateTaskScreen />
          </AnimatedPage>
        } />
        <Route path="mission-control" element={
          <AnimatedPage>
            <MissionControlScreen />
          </AnimatedPage>
        } />
        <Route path="messages" element={
          <AnimatedPage>
            <SavedMessagesScreen />
          </AnimatedPage>
        } />
      </Routes>
    </AnimatePresence>
  );
};