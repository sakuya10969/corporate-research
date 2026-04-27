import axios, { type AxiosInstance } from "axios";

/**
 * Clerk JWT を Authorization ヘッダーに付与する認証済み Axios インスタンスを生成する。
 *
 * @param getToken - Clerk の getToken() 関数（呼び出し時に最新 JWT を取得）
 * @returns 認証済み AxiosInstance
 *
 * Requirements: 3.1, 3.2
 */
export function createAuthenticatedClient(
  getToken: () => Promise<string | null>
): AxiosInstance {
  const instance = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  });

  instance.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return instance;
}
