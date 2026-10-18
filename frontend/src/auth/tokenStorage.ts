const TOKEN_STORAGE_KEY = "pcfps_jwt";
const USERNAME_STORAGE_KEY = "pcfps_username";

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getStoredUsername(): string | null {
  return sessionStorage.getItem(USERNAME_STORAGE_KEY);
}

export function setStoredUsername(username: string): void {
  sessionStorage.setItem(USERNAME_STORAGE_KEY, username);
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  sessionStorage.removeItem(USERNAME_STORAGE_KEY);
}
