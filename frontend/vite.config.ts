import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // Важно для Docker
    port: 5100,
    allowedHosts: ["stud-match.mooo.com", "localhost"],
    open: true,
    watch: { usePolling: true }, // Для корректного отслеживания изменений в контейнере
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./app"),
    },
  },
});
