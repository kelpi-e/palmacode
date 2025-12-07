import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';
import apiClient from '../api/client.js';

import logo from '../images/logo.png';

const AuthorizationView = () => {
  const navigate = useNavigate();
  const auth = useAuth();

  const [form, setForm] = useState({
    email: '',
    password: ''
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try 
    {
      // Client-side validation
      if (!form.email || !form.password)
        throw new Error('Все поля обязательны для заполнения');
      
      if (!form.email.includes('@'))
        throw new Error('Введите корректный email адрес');

      console.log('Отправка запроса на авторизацию:', { email: form.email });

      // Call API - token will be automatically saved by apiClient
      const data = await apiClient.login(form.email, form.password);

      console.log('Авторизация успешна');

      // Update auth hook
      if (data.access_token && auth && auth.setToken) {
        auth.setToken(data.access_token);
      }

      // Clear any previous errors
      setError('');

      // Navigate to main page
      navigate('/done');

    } 
    catch (err) 
    {
      console.error('Ошибка авторизации:', err);
      
      // Handle specific error types
      if (err.type === 'network') {
        setError(err.message);
      } else if (err.status === 401 || err.status === 422) {
        setError('Неверный email или пароль');
      } else if (err.type === 'validation') {
        setError(err.message || 'Ошибка валидации данных');
      } else {
        setError(err.message || 'Произошла ошибка при авторизации');
      }
    } 
    finally 
    {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="registration-wrapper">
      <div className="registration-card">
        <img className='logo' src={logo} alt="BrainTube Logo" />
        <h1 className="registration-title">Войти</h1>
        <div className="login-link">
          Нет в BrainTube? <Link className="link" to="/">Зарегистрироваться</Link>
        </div>
        <form className="registration-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <input 
              type="email" 
              name="email"
              value={form.email}
              onChange={handleChange}
              className="form-input"
              placeholder="Email"
              required
              disabled={loading}/>
          </div>
          <div className="form-group">
            <input 
              type="password" 
              name="password"
              value={form.password}
              onChange={handleChange}
              className="form-input"
              placeholder="Пароль"
              required
              disabled={loading}/>
          </div>
          {error && (
            <div className="error-message">
              <strong>Ошибка:</strong> {error}
            </div>
          )}
          <button 
            type="submit" 
            className="submit-button"
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Вход...
              </>
            ) : (
              <>
                Войти
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthorizationView;