import request from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
}

export function loginApi(data: LoginParams) {
  return request.post('/auth/login', data)
}

export function registerApi(data: RegisterParams) {
  return request.post('/auth/register', data)
}

export function getMeApi() {
  return request.get('/auth/me')
}
