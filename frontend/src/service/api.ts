import axios from "axios";

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL });

export type UploadJob = {
  id: string;
  status: "queued" | "importing" | "processing" | "completed" | "failed";
  result?: unknown;
  error?: string | null;
};

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  const baseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
  return new URL(path, baseUrl).toString();
}

function withApiDetail(err: unknown): unknown {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: string } | undefined)?.detail;
    if (typeof detail === "string") return new Error(detail, { cause: err });
  }
  return err;
}

export class ExternalEndpoints {
  static MAP_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;

  static async createUploadJob(
    name: string,
    video: File,
    file: File,
    signal?: AbortSignal,
  ): Promise<UploadJob> {
    const form = new FormData();
    form.append("name", name);
    form.append("video", video);
    form.append("log", file);
    try {
      const { data } = await http.post<UploadJob>("/upload/jobs", form, {
        signal,
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    } catch (err) {
      throw withApiDetail(err);
    }
  }

  static async getUploadJob(id: string, signal?: AbortSignal): Promise<UploadJob> {
    try {
      const { data } = await http.get<UploadJob>(`/upload/jobs/${id}`, { signal });
      return data;
    } catch (err) {
      throw withApiDetail(err);
    }
  }

  static async getFlights() {
    const { data } = await http.get("/flights");
    return data;
  }

  static async getFlight(id: string) {
    const { data } = await http.get(`/flights/${id}`);
    return data;
  }

  static async classifyImage(
    file: File,
    signal?: AbortSignal,
  ) {
    const form = new FormData();
    form.append("file", file);

    try {
      const { data } = await http.post("/image", form, {
        signal,
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    } catch (err) {
      throw withApiDetail(err);
    }
  }
}
