import Axios from "axios";
import type { AxiosRequestConfig } from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const axiosInstance = Axios.create({
  baseURL: BACKEND_URL,
});

export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> =>
  axiosInstance(config).then((response) => response.data);
