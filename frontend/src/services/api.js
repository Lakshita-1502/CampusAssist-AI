import axios from 'axios'
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api', timeout: 30000 })
export const getHealth = () => api.get('/health').then(r => r.data)
export const ask = query => api.post('/query', { query }).then(r => r.data)
export const getDocuments = () => api.get('/documents').then(r => r.data)
export const uploadDocument = file => { const data = new FormData(); data.append('file', file); return api.post('/documents/upload', data).then(r => r.data) }
export const deleteDocument = id => api.delete(`/documents/${encodeURIComponent(id)}`).then(r => r.data)
export const reindex = () => api.post('/documents/reindex').then(r => r.data)
export const getAnalytics = () => api.get('/analytics').then(r => r.data)
export const getHistory = () => api.get('/history').then(r => r.data)
