import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';

const VerifyView = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { token, removeToken } = useAuth();
    
    const [step, setStep] = useState(1); // 1: форма ввода email, 2: проверка почты, 3: успех
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [timeLeft, setTimeLeft] = useState(600);
    const [resendCooldown, setResendCooldown] = useState(60);
    
    useEffect(() => {
        const tokenParam = searchParams.get('token');
        const emailParam = searchParams.get('email');
        
        if (tokenParam && emailParam) 
        {
            setEmail(emailParam);
            handleVerifyToken(tokenParam, emailParam);
        }
    }, [searchParams]);
    
    useEffect(() => {
        if (step === 2 && timeLeft > 0) 
        {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [timeLeft, step]);
    
    useEffect(() => {
        if (step === 2 && resendCooldown > 0) 
        {
            const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCooldown, step]);
    
    const handleVerifyToken = async (token, email) => {
        setIsLoading(true);
        setError('');
        
        try 
        {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            setSuccess('Email успешно подтверждён!');
            setStep(3);
        } 
        catch (err) 
        {
            setError(err.message || 'Ошибка подтверждения. Попробуйте отправить письмо снова.');
            setStep(1);
        } 
        finally 
        {
            setIsLoading(false);
        }
    };
    
    const handleSubmitEmail = async (e) => {
        e.preventDefault();
        setError('');
        
        if (!validateEmail(email)) 
        {
            setError('Пожалуйста, введите корректный email адрес');
            return;
        }
        
        setIsLoading(true);
        
        try 
        {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            setSuccess('Письмо с подтверждением отправлено! Проверьте вашу почту.');
            setStep(2);
            setTimeLeft(600);
            setResendCooldown(60);
        } 
        catch (err)
        {
            setError(err.message || 'Ошибка отправки письма. Попробуйте еще раз.');
        } 
        finally 
        {
            setIsLoading(false);
        }
    };
    
    const handleResendEmail = async () => {
        if (resendCooldown > 0) 
            return;
        
        setIsLoading(true);
        setError('');
        
        try 
        {
            await new Promise(resolve => setTimeout(resolve, 1000));
            setSuccess('Письмо отправлено повторно!');
            setResendCooldown(60);
        }
        catch (err) 
        {
            setError(err.message || 'Ошибка отправки письма.');
        } 
        finally 
        {
            setIsLoading(false);
        };
    };
    
    const handleLogout = () => {
        removeToken();
        navigate('/authorization');
    };
    
    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };
    
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };
    
    const renderStepIndicator = () => {
        return (
            <div className="step-indicator">
                <div className={`step ${step >= 1 ? 'active' : ''}`}>1</div>
                <div className={`step-line ${step >= 2 ? 'active' : ''}`}></div>
                <div className={`step ${step >= 2 ? 'active' : ''}`}>2</div>
                <div className={`step-line ${step >= 3 ? 'active' : ''}`}></div>
                <div className={`step ${step >= 3 ? 'active' : ''}`}>3</div>
            </div>
        );
    };
    
    if (step === 1)
    {
        return (
            <div className="verify-container">
                <div className="verify-card">
                    <div className="verify-logo">
                        <div className="logo-icon">✓</div>
                        <h1>Подтвердите email</h1>
                        <p className="subtitle">
                            Мы отправим ссылку для подтверждения на ваш адрес электронной почты
                        </p>
                    </div>
                    {renderStepIndicator()}
                    {error && (
                        <div className="status-message error">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="status-message success">
                            {success}
                        </div>
                    )}
                    <div className="status-message info">
                        Пожалуйста, введите ваш email адрес
                    </div>
                    <form onSubmit={handleSubmitEmail}>
                        <div className="input-group">
                            <label htmlFor="email">Email адрес</label>
                            <input
                                type="email"
                                id="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="example@mail.com"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <button
                            type="submit"
                            className="btn"
                            disabled={isLoading || !email}>
                            {isLoading ? 'Отправка...' : 'Отправить ссылку подтверждения'}
                        </button>
                    </form>
                    <div className="resend-link">
                        Уже есть ссылка?{' '}
                        <Link to="/verify" onClick={() => email && setStep(2)}>
                            Перейти к подтверждению
                        </Link>
                    </div>
                    <div className="auth-links">
                        <Link to="/authorization">Войти в аккаунт</Link>
                        <Link to="/">Зарегистрироваться</Link>
                    </div>
                </div>
            </div>
        );
    }
    
    if (step === 2) 
    {
        return (
            <div className="verify-container">
                <div className="verify-card">
                    <div className="verify-logo">
                        <h1>Проверьте почту</h1>
                        <p className="subtitle">
                            Мы отправили ссылку для подтверждения на{' '}
                            <span className="email-highlight">{email}</span>
                        </p>
                    </div>
                    {renderStepIndicator()}
                    {error && (
                        <div className="status-message error">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="status-message success">
                            {success}
                        </div>
                    )}
                    <div className="status-message info">
                        Перейдите по ссылке в письме для подтверждения вашего email.
                        Если письма нет, проверьте папку "Спам".
                    </div>
                    <div className="timer">
                        Ссылка действительна в течение:{' '}
                        <span className="time-highlight">{formatTime(timeLeft)}</span>
                    </div>
                    <button
                        className="btn"
                        onClick={handleResendEmail}
                        disabled={resendCooldown > 0 || isLoading}>
                        {isLoading ? 'Отправка...' : resendCooldown > 0 ? `Отправить повторно (${resendCooldown})` : 'Отправить повторно'}
                    </button>
                    <div className="resend-link">
                        <Link to="#" onClick={() => setStep(1)}>Указать другой email</Link>
                    </div>
                    {token && (
                        <div className="auth-links">
                            <button 
                                className="logout-btn"
                                onClick={handleLogout}>
                                Выйти из аккаунта
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }
    
    return (
        <div className="verify-container">
            <div className="verify-card">
                <div className="verify-logo">
                    <div className="logo-icon">🎉</div>
                    <h1>Почта подтверждена!</h1>
                    <p className="subtitle">
                        Ваш адрес электронной почты{' '}
                        <span className="email-highlight">{email}</span>{' '}
                        успешно подтверждён
                    </p>
                </div>
                {renderStepIndicator()}
                <div className="status-message success">
                    Поздравляем! Теперь вы можете пользоваться всеми функциями приложения.
                </div>
                <button
                    className="btn"
                    onClick={() => token ? navigate('/done') : navigate('/authorization')}>
                    {token ? 'Перейти в личный кабинет' : 'Войти в аккаунт'}
                </button>
                <div className="resend-link">
                    Нужно подтвердить другой email?{' '}
                    <Link to="#" onClick={() => {
                        setStep(1)
                        setEmail('')
                        setError('')
                        setSuccess('')
                    }}>Начать заново</Link>
                </div>
            </div>
        </div>
    );
}

export default VerifyView