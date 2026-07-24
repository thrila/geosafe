import axios from "axios";

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL });

export class ExternalEndpoints {
  static MAP_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;

  static async uploadFile(
    name: string,
    video: File,
    file: File,
    signal?: AbortSignal,
  ) {
    const form = new FormData();
    form.append("name", name);
    form.append("video", video);
    form.append("log", file);

    const { data } = await http.post("/upload", form, {
      signal,
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
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

    const { data } = await http.post("/image", form, {
      signal,
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }
}
