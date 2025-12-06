import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';

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
  
  const API_BASE_URL = 'http://192.168.31.111:8099';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try 
    {
      if (!form.email || !form.password)
        throw new Error('Все поля обязательны для заполнения');
      
      if (!form.email.includes('@'))
        throw new Error('Введите корректный email адрес');

      const loginData = {
        email: form.email,
        password: form.password
      };

      console.log('Отправка запроса на авторизацию:', loginData);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(loginData)
      });

      const responseText = await response.text();
      console.log('Ответ сервера при авторизации:', responseText);

      let data;
      try 
      {
        data = JSON.parse(responseText);
      } 
      catch (parseError) 
      {
        throw new Error(`Некорректный ответ сервера: ${responseText.substring(0, 100)}`);
      }

      if (!response.ok)
        throw new Error(data.message || data.error || data.detail || `Ошибка авторизации: ${response.status}`);

      if (data.token || data.access_token || data.accessToken) 
      {
        const token = data.token || data.access_token || data.accessToken;
        
        localStorage.setItem('authToken', token);
        
        if (auth && auth.setToken) 
        {
          auth.setToken(token);
          console.log('Токен сохранен в useAuth:', token.substring(0, 20) + '...');
        }
        
        console.log('Токен успешно сохранен в localStorage');
      } 
      else 
      {
        console.warn('Токен не найден в ответе сервера, но авторизация прошла успешно');
        console.log('Полный ответ сервера:', data);
        
        if (data.data && data.data.token) 
        {
          const token = data.data.token;
          localStorage.setItem('authToken', token);
          if (auth && auth.setToken)
            auth.setToken(token);
        }
      }

      navigate('/done');

    } 
    catch (err) 
    {
      console.error('Ошибка авторизации:', err);
      
      if (err.name === 'TypeError' && err.message.includes('Failed to fetch'))
        setError('Не удалось подключиться к серверу. Проверьте: 1) Запущен ли бекенд 2) Правильность URL: ' + API_BASE_URL);
      else if (err.message.includes('HTML страницу'))
        setError(err.message + '. Возможно, неправильный endpoint API или проблемы с CORS.');
      else if (err.message.includes('401') || err.message.includes('неверный'))
        setError('Неверный email или пароль');
      else
        setError(err.message || 'Произошла ошибка при авторизации');
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
            disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthorizationView;