import { createApp } from 'vue';
import { createPinia } from 'pinia';
import axios from 'axios';
import App from './App.vue';
import router from './router';
import './assets/main.css';
import './assets/colors.css';
import './assets/tailwind-custom.css';

// Configuración de Markdown Editor
import { MdPreview, config } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

// Configuración global de axios
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.timeout = 120000; // 2 minutos
axios.interceptors.response.use(
    response => response,
    error => {
        console.error('Error de API:', error);
        return Promise.reject(error);
    }
);

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.component('MdPreview', MdPreview);

// Configurar md-editor-v3
config({
    editorConfig: {
        markdownItConfig: (mdit) => {
            // Añadir configuración para mejorar la compatibilidad
            return mdit;
        },
        markdownItPlugins: [],
        codeTheme: 'github-dark',
        mdHeadingOffset: 0
    }
});

app.mount('#app'); 