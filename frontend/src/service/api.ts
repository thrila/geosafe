export class ExternalEndpoints {
  static MAP_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
  static API_BASE = import.meta.env.VITE_API_BASE_URL;

  static async uploadFile(name: string, video: File, file: File) {
    const form = new FormData();
    form.append("name", name);
    form.append("video", video);
    form.append("log", file);

    const response = await fetch(`${this.API_BASE}/upload`, {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return await response.json();
  }

  static async getFlights() {
    const response = await fetch(`${this.API_BASE}/flights`);
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return await response.json();
  }

  static async getFlight(id: string) {
    const response = await fetch(`${this.API_BASE}/flights/${id}`);
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return await response.json();
  }
}
