import { defineConfig } from "vite";

export default defineConfig({
  root: "apps/miniapp",
  envDir: "../..",
  build: { outDir: "../../dist/miniapp", emptyOutDir: true },
});
