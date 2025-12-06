import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import logo from '../images/logo.png';
import Profile from '../images/Profile.png';

const Header = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const checkAuth = () => {
            try 
            {
                const token = localStorage.getItem('authToken');
                if (!token)
                    console.warn('Пользователь не авторизован');
            } 
            catch (err) 
            {
                console.error('Ошибка при проверке авторизации:', err);
            }
        };
        
        checkAuth();
    }, []);

    const handleProfileClick = async () => {
        setIsLoading(true);
        setError(null);
        
        try 
        {
            const token = localStorage.getItem('authToken');
            
            if (!token) 
            {
                navigate('/authorization');
                return;
            }

            const isValid = await validateToken(token);
            
            if (!isValid) 
            {
                localStorage.removeItem('authToken');
                navigate('/authorization');
                return;
            }

            await new Promise(resolve => setTimeout(resolve, 300));
            
            navigate('/profile');
            
        } 
        catch (err) 
        {
            setError(err.message || 'Произошла ошибка при переходе в профиль');
            if (err.name === 'SecurityError')
            {
                console.error('Ошибка безопасности при навигации:', err);
                alert('Ошибка безопасности. Пожалуйста, проверьте настройки браузера.');
            } 
            else if (err.name === 'NetworkError') 
            {
                console.error('Сетевая ошибка:', err);
                alert('Проблемы с сетью. Проверьте подключение к интернету.');
            } 
            else
            {
                console.error('Ошибка при переходе в профиль:', err);
                alert('Не удалось перейти в профиль. Попробуйте еще раз.');
            }
            
        } 
        finally 
        {
            setIsLoading(false);
        }
    };

    const validateToken = async (token) => {
        try 
        {
            return true; 
        }
        catch (err) 
        {
            console.error('Ошибка при валидации токена:', err);
            return false;
        }
    };

    const handleLogoClick = () => {
        try 
        {
            navigate('/');
        } 
        catch (err) 
        {
            console.error('Ошибка при переходе на главную:', err);
            setError('Не удалось перейти на главную страницу');
        }
    };

    const handleLogout = () => {
        try 
        {
            localStorage.removeItem('authToken');
            navigate('/authorization');
        } 
        catch (err) 
        {
            console.error('Ошибка при выходе:', err);
            setError('Не удалось выйти из системы');
        }
    };

    return (
        <header className="main-header">
            <img 
                className='logo-main' 
                src={logo} 
                alt="BrainTube Logo" 
                onClick={handleLogoClick}
                style={{ cursor: 'pointer' }}
            />
            
            <div className="header-actions">
                {error && (
                    <div className="header-error">
                        <span>{error}</span>
                        <button onClick={() => setError(null)}>×</button>
                    </div>
                )}
                <button 
                    className="profile-button"
                    onClick={handleProfileClick}
                    disabled={isLoading}
                    aria-label={isLoading ? "Загрузка..." : "Профиль"}
                    title="Перейти в профиль">
                    {isLoading ? (
                        <div className="loading-spinner">
                            <div className="spinner"></div>
                        </div>
                    ) : (
                        <img src={Profile} alt="Профиль пользователя" />
                    )}
                </button>
                
                <button 
                    className="logout-button"
                    onClick={handleLogout}
                    title="Выйти"
                    style={{
                        background: 'none',
                        border: 'none',
                        color: '#ff6b6b',
                        cursor: 'pointer',
                        marginLeft: '10px',
                        fontSize: '14px'
                    }}>
                    Выйти
                </button>
            </div>
        </header>
    );
};

export default Header;