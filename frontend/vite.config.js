import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        proxy: {
            // Redirigir todas las rutas API
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            // Redirigir rutas de estado y otras rutas
            '/health': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/mcp': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            // Ruta raíz para mensaje de bienvenida
            '^/$': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        },
    },
}) 