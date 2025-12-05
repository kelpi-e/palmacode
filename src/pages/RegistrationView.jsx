import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';

const RegistrationView = () => {
    const navigate = useNavigate();
    const auth = useAuth();

    const [form, setForm] = useState({
        email: '',
        password: '',
        confirmPassword: ''
    });

    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const getUsers = () => {
        const users = localStorage.getItem('mock_users');
        return users ? JSON.parse(users) : [];
    };

    const saveUser = (userData) => {
        const users = getUsers();
        users.push(userData);
        localStorage.setItem('mock_users', JSON.stringify(users));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(false);

        try
        {
            if (form.password.length < 6)
                throw new Error('Пароль должен содержать минимум 6 символов');
            if (form.password !== form.confirmPassword)
                throw new Error('Пароли не совпадают');

            const users = getUsers();
            const existingUser = users.find(u => u.email === form.email);
            if (existingUser)
                throw new Error('Пользователь с таким email уже существует');

            const mockUser = {
                id: Date.now(),
                email: form.email,
                password: form.password, 
                createdAt: new Date().toISOString(),
                emailVerified: false
            };

            saveUser(mockUser);

            const token = btoa(JSON.stringify({ 
                id: mockUser.id, 
                email: mockUser.email 
            }));
            
            auth.setToken(token);
            setSuccess(true);

            setTimeout(() => { 
                navigate('/verify');
            }, 2000);
        }
        catch (err)
        {
            setError(err.message);
        }
    };

    const handleChange = (e) => {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value}));
    };

    return (
        <div className="registration-wrapper">
            <div className="registration-card">
                <h1 className="registration-title">Регистрация в BrainTube</h1>
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
                        minLength="6"
                        required
                    />
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
                    />
                </div>
                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">Регистрация успешна! Перенаправляем на страницу подтверждения почты...</div>}
                <button type="submit" className="submit-button">
                    Зарегистрироваться
                </button>
                </form>
            </div>
        </div>
    );
}

export default RegistrationView;