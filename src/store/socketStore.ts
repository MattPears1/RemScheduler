import { create } from 'zustand';
import { io, Socket } from 'socket.io-client';
import { Window, JobGroup, SavedMessage } from '@types';
import toast from 'react-hot-toast';

interface SocketState {
  socket: Socket | null;
  isAgentOnline: boolean;
  windows: Window[];
  jobs: JobGroup[];
  savedMessages: SavedMessage[];
  connectSocket: () => void;
  disconnectSocket: () => void;
}

export const useSocketStore = create<SocketState>((set, get) => ({
  socket: null,
  isAgentOnline: false,
  windows: [],
  jobs: [],
  savedMessages: [],

  connectSocket: () => {
    const socket = io(window.location.origin);
    
    socket.on('connect', () => {
      console.log('Connected to server');
      socket.emit('web_connect');
    });

    socket.on('windows_updated', (data: { windows: Window[] }) => {
      set({ windows: data.windows });
    });

    socket.on('jobs_updated', (data: { job_groups: JobGroup[] }) => {
      set({ jobs: data.job_groups });
    });

    socket.on('transcripts_updated', (data: { transcripts: SavedMessage[] }) => {
      set({ savedMessages: data.transcripts });
    });

    socket.on('job_status_updated', (data: any) => {
      if (data.status === 'SENT') {
        toast.success('Message sent successfully!');
      }
      // Refresh jobs
      socket.emit('get_jobs');
    });

    socket.on('agent_connected', () => {
      set({ isAgentOnline: true });
      toast.success('Agent connected');
    });

    socket.on('agent_disconnected', () => {
      set({ isAgentOnline: false });
      toast.error('Agent disconnected');
    });

    socket.on('schedule_confirmed', (data: any) => {
      toast.success(`Scheduled ${data.jobs_created} message${data.jobs_created > 1 ? 's' : ''}`);
    });

    socket.on('rate_limit_active', (data: { reset_time: string }) => {
      toast.error(`Rate limited until ${new Date(data.reset_time).toLocaleTimeString()}`);
    });

    set({ socket });
  },

  disconnectSocket: () => {
    const { socket } = get();
    if (socket) {
      socket.disconnect();
      set({ socket: null, isAgentOnline: false });
    }
  },
}));