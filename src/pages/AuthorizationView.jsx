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

  const getUsers = () => {
    const users = localStorage.getItem('mock_users');
    return users ? JSON.parse(users) : [];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try 
    {
        const users = getUsers();
        const user = users.find(u => u.email === form.email && u.password === form.password);
        
        if (!user)
            throw new Error('Неверный email или пароль');

        const token = btoa(JSON.stringify({ 
            id: user.id, 
            email: user.email 
        }));
        
        auth.setToken(token);
        navigate('/done');
    } 
    catch (err) 
    {
        setError(err.message);
    }
  };

  const handleChange = (e) => {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="registration-wrapper">
      <div className="registration-card">
        <img className='logo' src={logo} />
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
            />
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
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" className="submit-button">
            Войти
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthorizationView;