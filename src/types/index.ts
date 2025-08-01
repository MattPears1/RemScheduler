export interface User {
  id: string;
  username: string;
}

export interface ScheduledJob {
  id: number;
  job_group_id: string;
  message_text: string;
  target_hwnd: number;
  target_title: string;
  scheduled_time: string;
  status: 'PENDING' | 'SENT' | 'FAILED';
  error_message?: string;
  executed_at?: string;
}

export interface JobGroup {
  job_group_id: string;
  target_hwnd: number;
  target_title: string;
  jobs: ScheduledJob[];
}

export interface Window {
  hwnd: number;
  title: string;
  process: string;
  pid: number;
}

export interface SavedMessage {
  id: number;
  text: string;
  message_text?: string; // alias for compatibility
  created_at: string;
  use_count?: number;
}

export interface CreateTaskData {
  message: string;
  target_hwnd: number;
  target_title: string;
  start_time: string;
  repetitions: number;
  interval_seconds: number;
  use_different_messages: boolean;
  messages?: string[];
}

export interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  windows: Window[];
  jobs: JobGroup[];
  savedMessages: SavedMessage[];
  isLoading: boolean;
  error: string | null;
  agentOnline: boolean;
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
}