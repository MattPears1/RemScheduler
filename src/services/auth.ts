import { User } from '@types';

class AuthService {
  private baseUrl = '/auth';

  async login(username: string, password: string): Promise<{ user: User }> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
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
      credentials: 'include',
    });
  }

  async checkAuth(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/me`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  }

  async getAgents(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/agents`, {
      credentials: 'include',
    });
    return response.json();
  }
}

export const authService = new AuthService();