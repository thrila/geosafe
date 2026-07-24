import { z } from "zod";

export const imageUploadSchema = z.object({
  imageFile: z
    .instanceof(File, { message: "Choose an image file." })
    .refine(
      (file) =>
        file.type.startsWith("image/") ||
        /\.(jpg|jpeg|png|webp)$/i.test(file.name),
      "Choose a valid image file (.jpg, .png, .webp)."
    ),
});
