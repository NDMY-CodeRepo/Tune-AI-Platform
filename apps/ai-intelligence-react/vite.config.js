import {defineConfig} from 'vite';
export default defineConfig({build:{rollupOptions:{input:{intelligence:'index.html',desk:'desk.html'}}},server:{port:5173,strictPort:true,proxy:{'/api':'http://127.0.0.1:8000','/tune-logo.png':'http://127.0.0.1:8000'}}});
