// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  CHAT: {
    MESSAGE: `${API_BASE_URL}/api/v1/chat/message`,
    FRAMEWORKS: `${API_BASE_URL}/api/v1/chat/frameworks`,
    SESSIONS: `${API_BASE_URL}/api/v1/chat/sessions`,
  },
  DASHBOARD: `${API_BASE_URL}/api/v1/dashboard`,
  DOCUMENTS: `${API_BASE_URL}/api/v1/documents`,
  REPORTS: `${API_BASE_URL}/api/v1/reports`,
  COMPLIANCE: `${API_BASE_URL}/api/v1/compliance`,
};

export default API_BASE_URL;
