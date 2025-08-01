import { User } from '@types';

class AuthService {
  private baseUrl = '/auth';

  async login(username: string, password: string): Promise<{ user: User }> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    return response.json();
  }

  async logout(): Promise<void> {
    await fetch(`${this.baseUrl}/logout`, {
      method: 'POST',
    });
  }

  async checkAuth(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/me`);
    
    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  }

  async getAgents(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/agents`);
    return response.json();
  }
}

export const authService = new AuthService();