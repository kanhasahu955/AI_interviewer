const STORAGE_KEY = 'interviewer_ai_token'

export class TokenStorage {
  private static instance: TokenStorage | null = null

  static getInstance(): TokenStorage {
    TokenStorage.instance ??= new TokenStorage()
    return TokenStorage.instance
  }

  get(): string | null {
    return localStorage.getItem(STORAGE_KEY)
  }

  set(token: string): void {
    localStorage.setItem(STORAGE_KEY, token)
  }

  clear(): void {
    localStorage.removeItem(STORAGE_KEY)
  }
}
