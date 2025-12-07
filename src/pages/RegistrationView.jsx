import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';
import apiClient from '../api/client.js';

import logo from '../images/logo.png';

const RegistrationView = () => {
    const navigate = useNavigate();
    const auth = useAuth();

    const [form, setForm] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        role: 'user'
    });

    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(false);
        setLoading(true);

        try 
        {
            // Client-side validation
            if (!form.email || !form.password || !form.confirmPassword)
                throw new Error('Все поля обязательны для заполнения');
            
            if (!form.email.includes('@'))
                throw new Error('Введите корректный email адрес');
            
            if (form.password.length < 6)
                throw new Error('Пароль должен содержать минимум 6 символов');
            
            if (form.password !== form.confirmPassword)
                throw new Error('Пароли не совпадают');

            console.log('Отправка запроса на регистрацию:', { email: form.email, role: form.role });

            // Call API
            const data = await apiClient.register(form.email, form.password, form.role);

            console.log('Регистрация успешна:', data);

            setSuccess(true);
            setError('');
            
            // Registration doesn't return token, user needs to login
            setTimeout(() => { 
                navigate('/authorization');
            }, 2000);

        } 
        catch (err) 
        {
            console.error('Ошибка регистрации:', err);
            console.error('Детали ошибки:', {
                status: err.status,
                type: err.type,
                message: err.message,
                details: err.details
            });
            
            // Handle API errors
            if (err.status === 422 || err.status === 400 || err.type === 'validation') {
                setError(err.message || 'Ошибка валидации данных. Проверьте правильность введенных данных.');
            } else if (err.type === 'network') {
                setError(err.message);
            } else {
                setError(err.message || 'Произошла ошибка при регистрации');
            }
        } 
        finally 
        {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        setForm(prev => ({ 
            ...prev, 
            [e.target.name]: e.target.value 
        }));
    };

    return (
        <div className="registration-wrapper">
            <div className="registration-card">
                <img className='logo' src={logo} alt="BrainTube Logo" />
                <h1 className="registration-title">Регистрация</h1>
                <div className="login-link">
                    Уже есть в BrainTube? <Link className="link" to="/authorization">Авторизоваться</Link>
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
                            minLength="6"
                            required
                            disabled={loading}/>
                    </div>
                    <div className="form-group">
                        <input 
                            type="password" 
                            name="confirmPassword"
                            value={form.confirmPassword}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="Подтвердите пароль"
                            required
                            disabled={loading}/>
                    </div>
                    <input 
                        type="hidden" 
                        name="role" 
                        value={form.role}/>
                    {error && (
                        <div className="error-message">
                            <strong>Ошибка:</strong> {error}
                        </div>
                    )}
                    {success && (
                        <div className="success-message">
                            Регистрация успешна! Перенаправляем...
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
                                Регистрация...
                            </>
                        ) : (
                            <>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                </svg>
                                Зарегистрироваться
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default RegistrationView;