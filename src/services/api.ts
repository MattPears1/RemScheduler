import { CreateTaskData, JobGroup, SavedMessage } from '@types';

class ApiService {
  private baseUrl = '/api';
  
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  async scheduleTask(data: CreateTaskData): Promise<{ job_group_id: string }> {
    const response = await fetch(`${this.baseUrl}/schedule`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to schedule task');
    }

    return response.json();
  }

  async getJobs(): Promise<JobGroup[]> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs`, {
        credentials: 'include',
        headers: this.getHeaders(),
      });
      if (!response.ok) {
        console.error('Failed to fetch jobs:', response.status, response.statusText);
        return [];
      }
      const data = await response.json();
      console.log('Fetched jobs:', data);
      return data;
    } catch (error) {
      console.error('Error fetching jobs:', error);
      return [];
    }
  }

  async updateJob(jobId: number, data: any): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to update job');
    }
  }

  async cancelJob(jobId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to cancel job');
    }
  }

  async deleteJobHistory(jobId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/delete-history`, {
      method: 'DELETE',
      credentials: 'include',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to delete job history');
    }
  }

  async rescheduleJob(jobId: number, newTime: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/reschedule`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ new_scheduled_time: newTime }),
    });

    if (!response.ok) {
      throw new Error('Failed to reschedule job');
    }
  }

  async getSavedMessages(): Promise<SavedMessage[]> {
    try {
      const response = await fetch(`${this.baseUrl}/tasks`, {
        credentials: 'include',
      });
      if (!response.ok) {
        console.error('Failed to fetch saved messages:', response.status, response.statusText);
        return [];
      }
      const data = await response.json();
      console.log('Fetched saved messages:', data);
      return data;
    } catch (error) {
      console.error('Error fetching saved messages:', error);
      return [];
    }
  }

  async deleteSavedMessage(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/tasks/${id}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to delete message');
    }
  }

  async saveMessage(text: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/save-message`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error('Failed to save message');
    }
  }

  async transcribeAudio(audioBlob: Blob): Promise<{ transcribed_text: string }> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch(`${this.baseUrl}/speech-to-task`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to transcribe audio');
    }

    return response.json();
  }
}

export const apiService = new ApiService();