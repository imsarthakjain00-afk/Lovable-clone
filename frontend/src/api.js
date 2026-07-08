import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');
// Create a shared axios instance that all API calls use
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically attach the JWT token to every request that needs authentication
api.interceptors.request.use(
  (config) => {
    const authToken = localStorage.getItem('auth_token');
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);


// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authAPI = {
  register: async (userData) => {
    const response = await api.post('/users/register', userData);
    return response.data;
  },

  login: async (username, password) => {
    const response = await api.post('/users/login', { username, password });
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
  },

  getCurrentUser: async () => {
    const response = await api.get('/users/is_auth');
    return response.data;
  },

  googleLogin: async (idToken) => {
    const response = await api.post('/users/google-login', { id_token: idToken });
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    return response.data;
  },
};


// ─── Projects API ─────────────────────────────────────────────────────────────

export const projectsAPI = {
  getAllProjects: async () => {
    const response = await api.get('/projects/');
    return response.data;
  },

  getProjectWithChatHistory: async (projectId) => {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  createProject: async (title, description = '') => {
    const response = await api.post('/projects/', { title, description });
    return response.data;
  },

  updateProject: async (projectId, title) => {
    const response = await api.patch(`/projects/${projectId}`, { title });
    return response.data;
  },

  deleteProject: async (projectId) => {
    const response = await api.delete(`/projects/${projectId}`);
    return response.data;
  },

  deployProject: async (projectId) => {
    const response = await api.post(`/projects/${projectId}/deploy`);
    return response.data;
  },
};


// ─── AI Code Generation API ───────────────────────────────────────────────────

export const aiAPI = {
  generateWebsiteFromPrompt: async (projectId, userPrompt) => {
    const response = await api.post('/ai/generate', {
      project_id: projectId,
      user_prompt: userPrompt,
    });
    return response.data;
  },

  deepBuildWebsite: async (projectId, userPrompt) => {
    const response = await api.post('/ai/deep-build', {
      project_id: projectId,
      user_prompt: userPrompt,
    });
    return response.data;
  },
};


// ─── Templates API ────────────────────────────────────────────────────────────

export const templatesAPI = {
  getAllTemplates: async () => {
    const response = await api.get('/templates/');
    return response.data;
  },

  getTemplateById: async (templateId) => {
    const response = await api.get(`/templates/${templateId}`);
    return response.data;
  },
};


export default api;
