import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';

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

    const API_BASE_URL = 'http://192.168.31.111:8099';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(false);
        setLoading(true);

        try 
        {
            if (!form.email || !form.password || !form.confirmPassword)
                throw new Error('Все поля обязательны для заполнения');
            
            if (!form.email.includes('@'))
                throw new Error('Введите корректный email адрес');
            
            if (form.password.length < 6)
                throw new Error('Пароль должен содержать минимум 6 символов');
            
            if (form.password !== form.confirmPassword)
                throw new Error('Пароли не совпадают');

            const registrationData = {
                email: form.email,
                password: form.password,
                role: form.role
            };

            console.log('Отправка запроса на регистрацию:', registrationData);

            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(registrationData)
            });

            const responseText = await response.text();
            console.log('Ответ сервера:', responseText);

            let data;
            try 
            {
                data = JSON.parse(responseText);
            } 
            catch (parseError) 
            {
                if (responseText.startsWith('<!DOCTYPE') || responseText.startsWith('<html>'))
                    throw new Error('Сервер вернул HTML страницу. Проверьте правильность URL API');
                throw new Error(`Некорректный ответ сервера: ${responseText.substring(0, 100)}`);
            }

            if (!response.ok) 
                throw new Error(data.message || data.error || `Ошибка сервера: ${response.status}`);

            setSuccess(true);
            
            if (data.token || data.accessToken || data.data?.token) 
            {
                const token = data.token || data.accessToken || data.data.token;
                if (auth && auth.setToken)
                    auth.setToken(token);
                else 
                    localStorage.setItem('auth_token', token);
                
                if (data.user?.emailVerified === false || data.emailVerified === false)
                    setTimeout(() => { navigate('/verify'); }, 2000);
                else
                    setTimeout(() => { navigate('/'); }, 2000);
            } 
            else 
            {
                setTimeout(() => { 
                    navigate('/authorization');
                }, 2000);
            }

        } 
        catch (err) 
        {
            console.error('Ошибка регистрации:', err);
            
            if (err.name === 'TypeError' && err.message.includes('Failed to fetch'))
                setError('Не удалось подключиться к серверу. Проверьте: 1) Запущен ли бекенд 2) Правильность URL: ' + API_BASE_URL);
            else if (err.message.includes('HTML страницу'))
                setError(err.message + '. Возможно, неправильный endpoint API или проблемы с CORS.');
            else
                setError(err.message || 'Произошла ошибка при регистрации');
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
                        disabled={loading}>
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Регистрация...
                            </>
                        ) : (
                            'Зарегистрироваться'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default RegistrationView;