import { User } from '../types';
import { api } from './api';


const TOKEN_KEY = 'auth_token';

export const authService = {
  async login(username: string, password: string): Promise<{ access_token: string; user: User }> {
    const response = await api.post('/auth/login', { username, password });
    const { access_token, user } = response.data;

    this.setToken(access_token);
    return { access_token, user };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      this.removeToken();
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async refreshToken(): Promise<{ access_token: string; user: User }> {
    const response = await api.post('/auth/refresh');
    const { access_token, user } = response.data;

    this.setToken(access_token);
    return { access_token, user };
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },

  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.post('/auth/reset-password', {
      token,
      new_password: newPassword
    });
    return response.data;
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
