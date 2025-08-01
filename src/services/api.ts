import { CreateTaskData, JobGroup, SavedMessage } from '@types';

class ApiService {
  private baseUrl = '/api';

  async scheduleTask(data: CreateTaskData): Promise<{ job_group_id: string }> {
    const response = await fetch(`${this.baseUrl}/schedule`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to schedule task');
    }

    return response.json();
  }

  async getJobs(): Promise<JobGroup[]> {
    const response = await fetch(`${this.baseUrl}/jobs`);
    return response.json();
  }

  async updateJob(jobId: number, data: any): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to update job');
    }
  }

  async cancelJob(jobId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to cancel job');
    }
  }

  async deleteJobHistory(jobId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/delete-history`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete job history');
    }
  }

  async rescheduleJob(jobId: number, newTime: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/reschedule`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_scheduled_time: newTime }),
    });

    if (!response.ok) {
      throw new Error('Failed to reschedule job');
    }
  }

  async getSavedMessages(): Promise<SavedMessage[]> {
    const response = await fetch(`${this.baseUrl}/tasks`);
    return response.json();
  }

  async deleteSavedMessage(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/tasks/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete message');
    }
  }

  async saveMessage(text: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/save-message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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