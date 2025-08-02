import { CreateTaskData, JobGroup, SavedMessage } from '@types';

class ApiService {
  private baseUrl: string;
  
  constructor() {
    this.baseUrl = '/api';
  }
  
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
      const url = `${this.baseUrl || '/api'}/jobs`;
      const response = await fetch(url, {
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
    const url = `${this.baseUrl || '/api'}/jobs/${jobId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      credentials: 'include',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Cancel job failed:', response.status, errorText);
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

  async deleteAllByStatus(status: 'PENDING' | 'EXPIRED' | 'SENT'): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/delete-all/${status}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Delete all ${status} jobs failed:`, response.status, errorText);
      throw new Error(`Failed to delete all ${status} jobs`);
    }
  }

  async purgeAllJobs(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/jobs/purge-all`, {
      method: 'DELETE',
      credentials: 'include',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Purge all jobs failed:', response.status, errorText);
      throw new Error('Failed to purge all jobs');
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
    // Try the standard multipart endpoint first
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await fetch(`${this.baseUrl}/speech-to-task`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (response.ok) {
        return await response.json();
      }

      // If 503 or timeout, try base64 endpoint
      if (response.status === 503 || response.status === 504) {
        console.log('Multipart upload failed, trying base64 encoding...');
        return await this.transcribeAudioBase64(audioBlob);
      }

      const error = await response.json();
      throw new Error(error.error || 'Failed to transcribe audio');
    } catch (error) {
      // If network error, try base64 as fallback
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.log('Network error, trying base64 encoding...');
        return await this.transcribeAudioBase64(audioBlob);
      }
      throw error;
    }
  }

  private async transcribeAudioBase64(audioBlob: Blob): Promise<{ transcribed_text: string }> {
    // Convert blob to base64
    const reader = new FileReader();
    const base64Promise = new Promise<string>((resolve, reject) => {
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert audio to base64'));
        }
      };
      reader.onerror = reject;
    });
    
    reader.readAsDataURL(audioBlob);
    const base64Data = await base64Promise;

    const response = await fetch(`${this.baseUrl}/speech-to-task-base64`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ audio: base64Data }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to transcribe audio');
    }

    return response.json();
  }
}

const apiService = new ApiService();

export { apiService };
export default apiService;