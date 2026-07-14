import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default defineConfig({
  assetsInclude: ["**/*.glb"],
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/cesium/Build/Cesium/**/*",
          dest: "cesium",
          rename: {
            stripBase: 4,
          },
        },
      ],
    }),
  ],

  define: {
    CESIUM_BASE_URL: JSON.stringify("/cesium/"),
  },
});
