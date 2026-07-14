export class ExternalEndpoints {
  static MAP_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
  static BaseUrl: string = import.meta.env.VITE_BACKEND_URL;
  static Port: string = import.meta.env.VITE_BACKEND_PORT;
  static upload_path = "/api/v1/upload";
  static async uploadFile(
    name: string,
    video: File,
    file: File
  ) {
    const form = new FormData();

    form.append("name", name);
    form.append("video", video);
    form.append("log", file);

    const response = await fetch(this.BaseUrl + ":" + this.Port + this.upload_path, {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return await response.json();
  }
}
