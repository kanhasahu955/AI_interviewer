import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'

import { API_PREFIX, env } from '@/core/config/env'
import { ApiError } from '@/core/errors/ApiError'
import { TokenStorage } from '@/core/http/TokenStorage'

type UnauthorizedHandler = () => void

export class ApiClient {
  private static instance: ApiClient | null = null
  private readonly client: AxiosInstance
  private unauthorizedHandler: UnauthorizedHandler | null = null

  private constructor() {
    this.client = axios.create({
      baseURL: `${env.apiBaseUrl}${API_PREFIX}`,
      timeout: 30_000,
      headers: { 'Content-Type': 'application/json' },
    })

    this.client.interceptors.request.use(this.attachAuthToken)
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const apiError = ApiError.fromAxios(error)
        this.handleUnauthorized(apiError)
        return Promise.reject(apiError)
      },
    )
  }

  static getInstance(): ApiClient {
    ApiClient.instance ??= new ApiClient()
    return ApiClient.instance
  }

  onUnauthorized(handler: UnauthorizedHandler): void {
    this.unauthorizedHandler = handler
  }

  get axios(): AxiosInstance {
    return this.client
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await this.client.get<T>(url, config)
    return data
  }

  async post<T>(
    url: string,
    body?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const { data } = await this.client.post<T>(url, body, config)
    return data
  }

  async patch<T>(
    url: string,
    body?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const { data } = await this.client.patch<T>(url, body, config)
    return data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await this.client.delete<T>(url, config)
    return data
  }

  async postForm<T>(
    url: string,
    formData: FormData,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const { data } = await this.client.post<T>(url, formData, {
      ...config,
      headers: { 'Content-Type': 'multipart/form-data', ...config?.headers },
    })
    return data
  }

  private attachAuthToken = (
    config: InternalAxiosRequestConfig,
  ): InternalAxiosRequestConfig => {
    const token = TokenStorage.getInstance().get()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }

  handleUnauthorized(error: ApiError): void {
    if (error.status !== 401 || !this.unauthorizedHandler) return
    if (!TokenStorage.getInstance().get()) return
    this.unauthorizedHandler()
  }
}
