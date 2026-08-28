import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  // Prevent vite from obscuring Rust errors
  clearScreen: false,
  server: {
    port: 5173,
    // Tauri needs a strict port
    strictPort: true,
    watch: {
      // Tell Vite to ignore watching src-tauri (Rust build target folder)
      ignored: ["**/src-tauri/**"],
    },
  },
  // To make use of TAURI_DEBUG and other env variables
  envPrefix: ['VITE_', 'TAURI_'],
})
