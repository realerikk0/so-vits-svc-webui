import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import axios from "axios";

import './assets/main.css'


axios.defaults.baseURL = 'http://127.0.0.1:7870' // 这里填写服务器的地址
axios.defaults.timeout = 10 * 60 * 1000

const app = createApp(App)

let name, comp;
for ([name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp);
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
