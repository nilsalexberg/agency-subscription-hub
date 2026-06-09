import type { AxiosError } from 'axios'
import { apiClient } from './client'

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserRead {
  id: number
  email: string
  role: 'admin' | 'viewer'
  is_active: boolean
}

export type ApiError = AxiosError<{ detail?: string }>

export async function loginUser(
  email: string,
  password: string,
): Promise<{ token: TokenResponse; user: UserRead }> {
  const { data: token } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  const { data: user } = await apiClient.get<UserRead>('/users/me', {
    headers: { Authorization: `Bearer ${token.access_token}` },
  })
  return { token, user }
}

export async function registerUser(email: string, password: string): Promise<UserRead> {
  const { data } = await apiClient.post<UserRead>('/auth/register', { email, password })
  return data
}
