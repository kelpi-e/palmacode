import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../api/useAuth.js';
import logo from '../images/logo.png';
import Profile from '../images/Profile.png';

const Header = () => {
    const navigate = useNavigate();
    const auth = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const API_BASE_URL = 'http://192.168.31.111:8099';

    useEffect(() => {
        const checkAuth = () => {
            try 
            {
                const token = getToken();
                if (!token)
                    console.log('Пользователь не авторизован. Токен не найден.');
                else
                    console.log('Токен найден:', token.substring(0, 20) + '...');
            } 
            catch (err) 
            {
                console.error('Ошибка при проверке авторизации:', err);
            }
        };
        
        checkAuth();
    }, []);

    const getToken = () => {
        const token = localStorage.getItem('authToken') || 
                     localStorage.getItem('token') || 
                     sessionStorage.getItem('authToken');
        
        if (!token && auth && auth.token)
            return auth.token;
        
        return token;
    };

    const handleVideoUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) 
            return;

        setIsUploading(true);
        setError(null);

        try 
        {
            const token = getToken();
            if (!token)
                throw new Error('Требуется авторизация. Пожалуйста, войдите в систему.');

            console.log('Используемый токен для загрузки видео:', token.substring(0, 20) + '...');

            if (!file.type.startsWith('video/'))
                throw new Error('Пожалуйста, выберите видео файл');

            const maxSize = 500 * 1024 * 1024; 
            if (file.size > maxSize)
                throw new Error('Файл слишком большой. Максимальный размер: 500MB');

            console.log('Начинаю загрузку видео:', file.name, 'размер:', file.size);

            const formData = new FormData();
            formData.append('video', file);
            
            const headers = {
                'Accept': 'application/json',
            };
            
            if (token) 
            {
                headers['Authorization'] = `Bearer ${token}`;
                console.log('Добавлен заголовок Authorization с токеном');
            }

            console.log('Отправка запроса на:', `${API_BASE_URL}/video`);
            console.log('Заголовки запроса:', headers);

            const response = await fetch(`${API_BASE_URL}/video`, {
                method: 'POST',
                headers: headers,
                body: formData,
            });

            console.log('Ответ сервера:', response.status, response.statusText);

            const responseText = await response.text();
            console.log('Тело ответа:', responseText);

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

            if (response.status === 401) 
            {
                console.error('Ошибка 401: Неавторизованный доступ');
                localStorage.removeItem('authToken');
                localStorage.removeItem('token');
                sessionStorage.removeItem('authToken');
                
                if (auth && auth.setToken)
                    auth.setToken(null);
                
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }

            if (!response.ok)
                throw new Error(data.message || data.error || data.detail || `Ошибка загрузки: ${response.status}`);

            console.log('Видео успешно загружено:', data);
            
            const videoUrl = URL.createObjectURL(file);
            
            const videoInfo = {
                id: data.videoId || Date.now(),
                name: file.name,
                size: file.size,
                type: file.type,
                uploadDate: new Date().toLocaleDateString('ru-RU'),
                videoUrl: videoUrl,
                serverData: data,
                file: file,
            };

            const savedVideos = JSON.parse(localStorage.getItem('uploadedVideos') || '[]');
            savedVideos.push(videoInfo);
            localStorage.setItem('uploadedVideos', JSON.stringify(savedVideos));

            window.dispatchEvent(new CustomEvent('videoUploaded', { 
                detail: videoInfo 
            }));

            navigate('/analyse-video', { 
                state: { 
                    videoFile: file,
                    videoUrl: videoUrl,
                    videoId: data.videoId || videoInfo.id,
                    serverResponse: data
                } 
            });

        } 
        catch (err) 
        {
            console.error('Ошибка при загрузке видео:', err);
            
            if (err.name === 'TypeError' && err.message.includes('Failed to fetch'))
                setError('Не удалось подключиться к серверу. Проверьте: 1) Запущен ли бекенд 2) Правильность URL: ' + API_BASE_URL);
            else if (err.message.includes('HTML страницу'))
                setError(err.message + '. Возможно, неправильный endpoint API или проблемы с CORS.');
            else if (err.message.includes('Сессия истекла') || err.message.includes('Требуется авторизация')) 
            {
                setError(err.message);
                setTimeout(() => {
                    navigate('/authorization');
                }, 2000);
            } 
            else
                setError(err.message || 'Произошла ошибка при загрузке видео');
        } 
        finally 
        {
            setIsUploading(false);
            if (fileInputRef.current)
                fileInputRef.current.value = '';
        }
    };

    const handleUploadClick = () => {
        const token = getToken();
        if (!token) 
        {
            setError('Для загрузки видео требуется авторизация');
            setTimeout(() => {
                navigate('/authorization');
            }, 1500);
            return;
        }
        
        if (fileInputRef.current)
            fileInputRef.current.click();
    };

    const handleProfileClick = async () => {
        setIsLoading(true);
        setError(null);
        
        try 
        {
            const token = getToken();
            
            if (!token) 
            {
                navigate('/authorization');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/auth/validate`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json',
                },
            });

            if (response.status === 401) 
            {
                localStorage.removeItem('authToken');
                localStorage.removeItem('token');
                sessionStorage.removeItem('authToken');
                if (auth && auth.setToken)
                    auth.setToken(null);
                navigate('/authorization');
                return;
            }

            await new Promise(resolve => setTimeout(resolve, 300));
            navigate('/profile');
            
        } 
        catch (err) 
        {
            setError(err.message || 'Произошла ошибка при переходе в профиль');
            console.error('Ошибка при переходе в профиль:', err);
        } 
        finally 
        {
            setIsLoading(false);
        }
    };

    const handleLogoClick = () => {
        try 
        {
            navigate('/done');
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
            localStorage.removeItem('token');
            sessionStorage.removeItem('authToken');
            
            if (auth && auth.setToken)
                auth.setToken(null);
            
            localStorage.removeItem('uploadedVideos');
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
                style={{ cursor: 'pointer' }}/>
            <div className="header-actions">
                {error && (
                    <div className="header-error">
                        <span>{error}</span>
                        <button onClick={() => setError(null)}>×</button>
                    </div>
                )}
                <button 
                    className="upload-video-btn"
                    onClick={handleUploadClick}
                    disabled={isUploading}
                    aria-label="Загрузить видео"
                    title="Загрузить видео для анализа">
                    {isUploading ? (
                        <>
                            <span className="spinner"></span>
                            Загрузка...
                        </>
                    ) : (
                        'Загрузить видео'
                    )}
                </button>
                <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    ref={fileInputRef}
                    style={{ display: 'none' }}/>
                <button 
                    className="profile-button"
                    onClick={handleProfileClick}
                    disabled={isLoading || isUploading}
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
                    disabled={isUploading}
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