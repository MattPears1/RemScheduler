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
    const { socket: existingSocket } = get();
    if (existingSocket?.connected) return;
    
    const socket = io(window.location.origin, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
    });
    
    socket.on('connect', () => {
      console.log('Connected to server');
      socket.emit('web_connect');
      toast.success('Connected to server');
      
      // Request fresh data after connection
      setTimeout(() => {
        socket.emit('get_jobs');
        socket.emit('get_transcripts');
        console.log('Requested fresh data from server');
      }, 500);
    });

    socket.on('windows_updated', (data: { windows: Window[] }) => {
      set({ windows: data.windows });
    });

    socket.on('jobs_updated', (data: { job_groups: JobGroup[] }) => {
      console.log('Received jobs update:', data);
      set({ jobs: data.job_groups });
    });

    socket.on('transcripts_updated', (data: { transcripts: SavedMessage[] }) => {
      console.log('Received transcripts update:', data);
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

    socket.on('agent_disconnected', (data: any) => {
      set({ isAgentOnline: false });
      toast.error('Local Agent disconnected');
      console.log('Agent disconnected:', data);
    });
    
    socket.on('disconnect', (reason) => {
      console.log('Disconnected from server:', reason);
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, try to reconnect
        socket.connect();
      }
    });
    
    socket.on('connect_error', (error) => {
      console.error('Connection error:', error.message);
    });

    socket.on('schedule_confirmed', (data: any) => {
      toast.success(`Scheduled ${data.jobs_created || 1} message${(data.jobs_created || 1) > 1 ? 's' : ''}`);
      // Request updated jobs
      socket.emit('get_jobs');
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