import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1867C0',
          secondary: '#5CBBF6',
          accent: '#005CAF',
          success: '#4CAF50',
          warning: '#FB8C00',
          error: '#FF5252',
          info: '#2196F3',
        }
      }
    }
  }
})

// 创建Pinia存储
const pinia = createPinia()

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)

app.mount('#app')
