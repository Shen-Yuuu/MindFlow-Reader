import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: 'localhost', // 或者 'localhost' 如果你想让局域网内其他设备访问
    port: 5173,       // 确认这是你前端运行的端口

    // 配置代理规则
    proxy: {
      // 匹配以 '/definition' 开头的请求
      '/definition': {
        target: 'http://localhost:8000', // !!! 重要：确认这是你 FastAPI 后端运行的地址和端口 !!!
        changeOrigin: true, // 必须设置为 true，欺骗后端服务器，以为请求来自同源
        // rewrite: (path) => path.replace(/^\/api/, '') // 如果后端API路径没有/definition前缀，则需要重写路径，但这里看起来不需要
        
        // 可选：打印代理日志，方便调试
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`[Vite Proxy] Forwarding request: ${req.method} ${req.url} -> ${options.target}${proxyReq.path}`);
          });
           proxy.on('error', (err, req, res) => {
             console.error('[Vite Proxy] Proxy error:', err);
           });
        }
      },
      '/global-graph': {
            target: 'http://localhost:8000', // 你的后端服务器地址和端口
            changeOrigin: true, // 必须设置为 true

          },
    },
  }
})
