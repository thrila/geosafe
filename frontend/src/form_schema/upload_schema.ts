import { z } from "zod";

export const uploadSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Name is required.")
    .max(80, "Keep the name under 80 characters."),
  videoFile: z
    .instanceof(File, { message: "Choose a video file." })
    .refine(
      (file) =>
        file.type.startsWith("video/") ||
        /\.(mp4|mov|webm|mkv|avi|m4v)$/i.test(file.name),
      "Choose a valid video file."
    ),
  textFile: z
    .instanceof(File, { message: "Choose a .txt file." })
    .refine(
      (file) =>
        file.type === "text/plain" || file.name.toLowerCase().endsWith(".txt"),
      "Choose a valid .txt file."
    ),
});
