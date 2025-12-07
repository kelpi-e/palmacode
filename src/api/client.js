import { API_CONFIG, STORAGE_KEYS } from './config';

/**
 * Centralized API Client for FastAPI Backend
 * Handles all API requests with authentication and error handling
 */
class ApiClient {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
    this.retryAttempts = 2;
    this.retryDelay = 1000; // 1 second
  }

  /**
   * Get authentication token from storage
   */
  getToken() {
    return (
      localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) ||
      localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) ||
      localStorage.getItem(STORAGE_KEYS.TOKEN) ||
      sessionStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) ||
      ''
    );
  }

  /**
   * Set authentication token in storage
   */
  setToken(token) {
    if (token) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
      // Keep backward compatibility
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    } else {
      this.removeToken();
    }
  }

  /**
   * Remove authentication token from storage
   */
  removeToken() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    sessionStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  /**
   * Build request headers
   */
  getHeaders(includeAuth = true, customHeaders = {}, body = null) {
    const headers = {
      'Accept': 'application/json',
      ...customHeaders,
    };

    // Don't set Content-Type for FormData (browser will set it automatically with boundary)
    // Only set Content-Type if it's not already set and body is not FormData
    if (!headers['Content-Type']) {
      if (!(body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }
    }

    if (includeAuth) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * Handle API response
   */
  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    
    // Handle empty responses (like 204 No Content)
    if (response.status === 204) {
      return null;
    }

    // Handle file downloads
    if (contentType && contentType.includes('application/octet-stream')) {
      return response.blob();
    }

    const text = await response.text();
    
    if (!text) {
      return null;
    }

    try {
      return JSON.parse(text);
    } catch (e) {
      // If response is HTML (error page), throw meaningful error
      if (text.startsWith('<!DOCTYPE') || text.startsWith('<html>')) {
        throw new Error('Сервер вернул HTML страницу. Проверьте правильность URL API');
      }
      throw new Error(`Некорректный ответ сервера: ${text.substring(0, 100)}`);
    }
  }

  /**
   * Handle API errors
   */
  handleError(error, response, responseData) {
    // Network errors (only if no response)
    if (error && error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      return {
        message: `Не удалось подключиться к серверу. Проверьте: 1) Запущен ли бекенд 2) Правильность URL: ${this.baseURL}`,
        status: 0,
        type: 'network',
      };
    }

    // HTTP errors
    if (response) {
      // Handle 401 Unauthorized
      if (response.status === 401) {
        this.removeToken();
        return {
          message: 'Сессия истекла. Пожалуйста, войдите снова.',
          status: 401,
          type: 'unauthorized',
        };
      }

      // Handle validation errors (422 and 400)
      if ((response.status === 422 || response.status === 400) && responseData) {
        let validationMessage = 'Ошибка валидации данных';
        
        if (responseData.detail) {
          if (Array.isArray(responseData.detail)) {
            // FastAPI validation error format
            validationMessage = responseData.detail
              .map(err => {
                const field = err.loc ? err.loc.slice(1).join('.') : 'unknown';
                return `${field}: ${err.msg}`;
              })
              .join(', ');
          } else if (typeof responseData.detail === 'string') {
            validationMessage = responseData.detail;
          } else if (typeof responseData.detail === 'object') {
            // Try to extract meaningful message
            validationMessage = responseData.detail.message || 
                               responseData.detail.msg || 
                               JSON.stringify(responseData.detail);
          }
        } else if (responseData.message) {
          validationMessage = responseData.message;
        } else if (typeof responseData === 'string') {
          validationMessage = responseData;
        }

        return {
          message: validationMessage,
          status: response.status,
          type: 'validation',
          details: responseData.detail || responseData,
        };
      }

      // Generic HTTP error
      let errorMessage = `Ошибка сервера: ${response.status}`;
      
      if (responseData) {
        if (responseData.message) {
          errorMessage = responseData.message;
        } else if (responseData.error) {
          errorMessage = responseData.error;
        } else if (responseData.detail) {
          if (typeof responseData.detail === 'string') {
            errorMessage = responseData.detail;
          } else if (Array.isArray(responseData.detail)) {
            errorMessage = responseData.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
          }
        } else if (typeof responseData === 'string') {
          errorMessage = responseData;
        }
      }

      return {
        message: errorMessage,
        status: response.status,
        type: 'http',
      };
    }

    // Other errors
    return {
      message: error?.message || 'Произошла неизвестная ошибка',
      status: 0,
      type: 'unknown',
    };
  }

  /**
   * Sleep helper for retry mechanism
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Make API request with retry mechanism
   */
  async request(endpoint, options = {}, attempt = 0) {
    const {
      method = 'GET',
      body = null,
      headers: customHeaders = {},
      includeAuth = true,
      timeout = this.timeout,
      retry = true,
    } = options;

    const url = `${this.baseURL}${endpoint}`;
    const headers = this.getHeaders(includeAuth, { ...customHeaders }, body);

    const config = {
      method,
      headers,
      ...(body && { body: body instanceof FormData ? body : JSON.stringify(body) }),
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      // Log request details in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Request [${attempt + 1}]:`, {
          url,
          method,
          headers: { ...headers, Authorization: headers.Authorization ? 'Bearer ***' : undefined },
          body: body instanceof FormData ? '[FormData]' : body,
        });
      }

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Log response details in development
      if (process.env.NODE_ENV === 'development') {
        console.log('API Response:', {
          status: response.status,
          statusText: response.statusText,
        });
      }

      const data = await this.handleResponse(response);

      if (process.env.NODE_ENV === 'development' && data) {
        console.log('API Response Data:', data);
      }

      if (!response.ok) {
        // Don't retry on client errors (4xx) except 401
        if (response.status >= 400 && response.status < 500 && response.status !== 401) {
          const error = this.handleError(null, response, data);
          if (process.env.NODE_ENV === 'development') {
            console.error('API Error:', error);
          }
          throw error;
        }
        
        // Retry on server errors (5xx) and 401
        if (retry && attempt < this.retryAttempts && (response.status >= 500 || response.status === 401)) {
          await this.sleep(this.retryDelay * (attempt + 1));
          return this.request(endpoint, options, attempt + 1);
        }
        
        const error = this.handleError(null, response, data);
        if (process.env.NODE_ENV === 'development') {
          console.error('API Error:', error);
        }
        throw error;
      }

      return { data, response };
    } catch (error) {
      // Retry on network errors
      if (retry && attempt < this.retryAttempts && error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        await this.sleep(this.retryDelay * (attempt + 1));
        return this.request(endpoint, options, attempt + 1);
      }
      
      if (error.status) {
        // Already handled error
        throw error;
      }
      const handledError = this.handleError(error);
      if (process.env.NODE_ENV === 'development') {
        console.error('API Request Error:', handledError);
      }
      throw handledError;
    }
  }

  // ==================== AUTH ENDPOINTS ====================

  /**
   * Register new user
   * POST /auth/register
   */
  async register(email, password, role = 'user') {
    const requestBody = {
      email: email.trim(),
      password: password,
      ...(role && { role }),
    };
    
    const { data } = await this.request('/auth/register', {
      method: 'POST',
      body: requestBody,
      includeAuth: false,
    });
    return data;
  }

  /**
   * Login user
   * POST /auth/login
   */
  async login(email, password) {
    const { data } = await this.request('/auth/login', {
      method: 'POST',
      body: { email, password },
      includeAuth: false,
    });
    
    // Save token if received
    if (data.access_token) {
      this.setToken(data.access_token);
    }
    
    return data;
  }

  // ==================== USER ENDPOINTS ====================

  /**
   * Get all users
   * GET /users/
   */
  async getAllUsers() {
    const { data } = await this.request('/users/');
    return data;
  }

  /**
   * Get current user info
   * GET /users/me
   */
  async getCurrentUser() {
    const { data } = await this.request('/users/me');
    return data;
  }

  /**
   * Get user by ID
   * GET /users/{user_id}
   */
  async getUserById(userId) {
    const { data } = await this.request(`/users/${userId}`);
    return data;
  }

  /**
   * Update user
   * PUT /users/{user_id}
   */
  async updateUser(userId, updates) {
    const { data } = await this.request(`/users/${userId}`, {
      method: 'PUT',
      body: updates,
    });
    return data;
  }

  /**
   * Delete user
   * DELETE /users/{user_id}
   */
  async deleteUser(userId) {
    await this.request(`/users/${userId}`, {
      method: 'DELETE',
    });
    return true;
  }

  // ==================== VIDEO ENDPOINTS ====================

  /**
   * Get all videos
   * GET /video/
   */
  async getAllVideos() {
    const { data } = await this.request('/video/');
    return data;
  }

  /**
   * Create new video
   * POST /video/
   */
  async createVideo(file, name) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);

    const { data } = await this.request('/video/', {
      method: 'POST',
      body: formData,
    });
    return data;
  }

  /**
   * Get video by ID
   * GET /video/{video_id}
   */
  async getVideoById(videoId) {
    const { data } = await this.request(`/video/${videoId}`);
    return data;
  }

  /**
   * Update video
   * PUT /video/{video_id}
   */
  async updateVideo(videoId, updates) {
    const { data } = await this.request(`/video/${videoId}`, {
      method: 'PUT',
      body: updates,
    });
    return data;
  }

  /**
   * Delete video
   * DELETE /video/{video_id}
   */
  async deleteVideo(videoId) {
    await this.request(`/video/${videoId}`, {
      method: 'DELETE',
    });
    return true;
  }

  /**
   * Download video file
   * GET /video/file/{video_id}
   */
  async downloadVideoFile(videoId) {
    const { data } = await this.request(`/video/file/${videoId}`);
    return data;
  }

  // ==================== ADMIN USER ENDPOINTS ====================

  /**
   * Create invitation code
   * POST /adminuser/invitation
   */
  async createInvitation() {
    const { data } = await this.request('/adminuser/invitation', {
      method: 'POST',
    });
    return data;
  }

  /**
   * Join admin by invitation code
   * POST /adminuser/join
   */
  async joinAdmin(code) {
    const { data } = await this.request('/adminuser/join', {
      method: 'POST',
      body: { code },
    });
    return data;
  }

  /**
   * Get my admins
   * GET /adminuser/my-admins
   */
  async getMyAdmins() {
    const { data } = await this.request('/adminuser/my-admins');
    return data;
  }

  /**
   * Get my users
   * GET /adminuser/my-users
   */
  async getMyUsers() {
    const { data } = await this.request('/adminuser/my-users');
    return data;
  }

  /**
   * Remove user from admin
   * DELETE /adminuser/{user_id}
   */
  async removeUserFromAdmin(userId) {
    await this.request(`/adminuser/${userId}`, {
      method: 'DELETE',
    });
    return true;
  }

  /**
   * Leave admin
   * DELETE /adminuser/leave/{admin_id}
   */
  async leaveAdmin(adminId) {
    await this.request(`/adminuser/leave/${adminId}`, {
      method: 'DELETE',
    });
    return true;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;

