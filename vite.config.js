import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
    plugins: [react()],
    root: 'src/frontend',
    build: {
        outDir: '../../dist/frontend',
        emptyOutDir: true,
        rollupOptions: {
            output: {
                manualChunks: undefined,
            },
        },
    },
    server: {
        port: 3000,
        host: true,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            },
            '/ws': {
                target: 'ws://localhost:8000',
                ws: true,
                changeOrigin: true
            }
        }
    },
    preview: {
        port: 3000,
        host: true
    },
    define: {
        'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000')
    }
}) 