import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, ".") },
  },
  publicDir: "public",
  build: {
    outDir: "../frontend_dist",
    emptyOutDir: true,
    target: "es2020",
    sourcemap: true,
  },
});
