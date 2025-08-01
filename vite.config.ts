import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [
    react()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@screens': path.resolve(__dirname, './src/screens'),
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://remscheduler-ca6ac87d3a1a.herokuapp.com',
        changeOrigin: true,
      },
      '/auth': {
        target: 'https://remscheduler-ca6ac87d3a1a.herokuapp.com',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'https://remscheduler-ca6ac87d3a1a.herokuapp.com',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})