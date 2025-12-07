import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../api/useAuth.js';
import apiClient from '../api/client.js';
import logo from '../images/logo.png';
import Profile from '../images/Profile.png';

const Header = () => {
    const navigate = useNavigate();
    const auth = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [userRole, setUserRole] = useState(null);
    const [isCreatingInvitation, setIsCreatingInvitation] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const checkAuth = async () => {
            try 
            {
                const token = auth.getToken();
                if (!token) {
                    console.log('Пользователь не авторизован. Токен не найден.');
                    setUserRole(null);
                    return;
                }
                
                console.log('Токен найден:', token.substring(0, 20) + '...');
                
                // Get user role
                try {
                    const user = await apiClient.getCurrentUser();
                    setUserRole(user.role);
                } catch (err) {
                    console.error('Ошибка при получении данных пользователя:', err);
                    setUserRole(null);
                }
            } 
            catch (err) 
            {
                console.error('Ошибка при проверке авторизации:', err);
                setUserRole(null);
            }
        };
        
        checkAuth();
    }, [auth.token]);

    const handleVideoUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) 
            return;

        setIsUploading(true);
        setError(null);
        setSuccessMessage(null);

        try 
        {
            // Check authentication
            if (!auth.isAuthenticated()) {
                throw new Error('Требуется авторизация. Пожалуйста, войдите в систему.');
            }

            // Validate file type
            if (!file.type.startsWith('video/'))
                throw new Error('Пожалуйста, выберите видео файл');

            // Validate file size (500MB max)
            const maxSize = 500 * 1024 * 1024; 
            if (file.size > maxSize)
                throw new Error('Файл слишком большой. Максимальный размер: 500MB');

            console.log('Начинаю загрузку видео:', file.name, 'размер:', file.size);

            // Use video name or file name
            const videoName = file.name.replace(/\.[^/.]+$/, ''); // Remove extension

            // Call API
            const data = await apiClient.createVideo(file, videoName);

            console.log('Видео успешно загружено:', data);
            
            // Create local URL for preview
            const videoUrl = URL.createObjectURL(file);
            
            // Prepare video info
            const videoInfo = {
                id: data.id || Date.now(),
                name: data.name || file.name,
                size: file.size,
                type: file.type,
                uploadDate: new Date().toLocaleDateString('ru-RU'),
                videoUrl: videoUrl,
                serverData: data,
                file: file,
            };

            // Save to localStorage
            const savedVideos = JSON.parse(localStorage.getItem('uploadedVideos') || '[]');
            savedVideos.push(videoInfo);
            localStorage.setItem('uploadedVideos', JSON.stringify(savedVideos));

            // Dispatch event to update DoneView
            window.dispatchEvent(new CustomEvent('videoUploaded', { 
                detail: videoInfo 
            }));

            // Show success message
            setError(null);
            setSuccessMessage(`Видео "${videoInfo.name}" успешно загружено!`);
            
            // Clear success message after 3 seconds
            setTimeout(() => {
                setSuccessMessage(null);
            }, 3000);
            
            // Navigate to video analysis page with videoId
            if (data.id) {
                navigate(`/analyse-video/${data.id}`);
            } else if (window.location.pathname !== '/done') {
                navigate('/done');
            }

        } 
        catch (err) 
        {
            console.error('Ошибка при загрузке видео:', err);
            
            // Handle specific error types
            if (err.type === 'network') {
                setError(err.message);
            } else if (err.type === 'unauthorized' || err.status === 401) {
                setError('Сессия истекла. Пожалуйста, войдите снова.');
                setTimeout(() => {
                    navigate('/authorization');
                }, 2000);
            } else if (err.message.includes('Требуется авторизация')) {
                setError(err.message);
                setTimeout(() => {
                    navigate('/authorization');
                }, 2000);
            } else {
                setError(err.message || 'Произошла ошибка при загрузке видео');
            }
        } 
        finally 
        {
            setIsUploading(false);
            if (fileInputRef.current)
                fileInputRef.current.value = '';
        }
    };

    const handleUploadClick = () => {
        if (!auth.isAuthenticated()) 
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
            if (!auth.isAuthenticated()) 
            {
                navigate('/authorization');
                return;
            }

            // Validate token by getting current user
            try {
                await apiClient.getCurrentUser();
            } catch (err) {
                if (err.type === 'unauthorized' || err.status === 401) {
                    auth.removeToken();
                    apiClient.removeToken();
                    navigate('/authorization');
                    return;
                }
                throw err;
            }

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
            auth.removeToken();
            apiClient.removeToken();
            localStorage.removeItem('uploadedVideos');
            setUserRole(null);
            navigate('/authorization');
        } 
        catch (err) 
        {
            console.error('Ошибка при выходе:', err);
            setError('Не удалось выйти из системы');
        }
    };

    const handleCopyInvitation = async () => {
        setIsCreatingInvitation(true);
        setError(null);
        setSuccessMessage(null);

        try {
            if (!auth.isAuthenticated()) {
                throw new Error('Требуется авторизация');
            }

            // Create invitation
            const invitationData = await apiClient.createInvitation();
            
            // Extract code from link
            // API returns { link: string, admin_id: number }
            // The link might be a full URL or just a code
            let invitationCode = '';
            let fullLink = '';
            
            if (invitationData.link) {
                fullLink = invitationData.link;
                // Try to extract code from link (last part after /)
                const parts = invitationData.link.split('/');
                invitationCode = parts[parts.length - 1] || invitationData.link;
            } else if (invitationData.code) {
                invitationCode = invitationData.code;
                fullLink = invitationData.code;
            } else {
                // Fallback: use admin_id as code
                invitationCode = invitationData.admin_id?.toString() || '';
                fullLink = invitationCode;
            }

            // Copy code to clipboard (prefer code over full link)
            const textToCopy = invitationCode || fullLink;
            
            try {
                await navigator.clipboard.writeText(textToCopy);
                setSuccessMessage(
                    fullLink !== textToCopy 
                        ? `Код скопирован: ${textToCopy}` 
                        : `Пригласительный код скопирован: ${textToCopy}`
                );
                
                // Clear success message after 5 seconds
                setTimeout(() => {
                    setSuccessMessage(null);
                }, 5000);
            } catch (clipboardErr) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '0';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    const successful = document.execCommand('copy');
                    if (successful) {
                        setSuccessMessage(
                            fullLink !== textToCopy 
                                ? `Код скопирован: ${textToCopy}` 
                                : `Пригласительный код скопирован: ${textToCopy}`
                        );
                        setTimeout(() => {
                            setSuccessMessage(null);
                        }, 5000);
                    } else {
                        throw new Error('Copy failed');
                    }
                } catch (err) {
                    // If copy fails, show the code for manual copy
                    setSuccessMessage(`Код: ${textToCopy} (нажмите для копирования)`);
                    setTimeout(() => {
                        setSuccessMessage(null);
                    }, 8000);
                }
                document.body.removeChild(textArea);
            }
        } catch (err) {
            console.error('Ошибка при создании пригласительного кода:', err);
            
            if (err.type === 'network') {
                setError(err.message);
            } else if (err.type === 'unauthorized' || err.status === 401) {
                setError('Сессия истекла. Пожалуйста, войдите снова.');
                setTimeout(() => {
                    navigate('/authorization');
                }, 2000);
            } else {
                setError(err.message || 'Не удалось создать пригласительный код');
            }
        } finally {
            setIsCreatingInvitation(false);
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
                {successMessage && (
                    <div className="header-success" style={{
                        background: '#4caf50',
                        color: 'white',
                        padding: '8px 16px',
                        borderRadius: '4px',
                        marginRight: '10px',
                        fontSize: '14px',
                        maxWidth: '400px',
                        wordBreak: 'break-word'
                    }}>
                        <span>{successMessage}</span>
                        <button onClick={() => setSuccessMessage(null)} style={{
                            marginLeft: '10px',
                            background: 'none',
                            border: 'none',
                            color: 'white',
                            cursor: 'pointer'
                        }}>×</button>
                    </div>
                )}
                {userRole === 'admin' && auth.isAuthenticated() && (
                    <button 
                        className="invitation-btn"
                        onClick={handleCopyInvitation}
                        disabled={isCreatingInvitation || isUploading}
                        aria-label="Скопировать пригласительный код"
                        title="Создать и скопировать пригласительный код"
                        style={{
                            padding: '8px 16px',
                            marginRight: '10px',
                            background: isCreatingInvitation ? '#ccc' : '#2196F3',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: isCreatingInvitation ? 'not-allowed' : 'pointer',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}>
                        {isCreatingInvitation ? (
                            <>
                                <span className="spinner" style={{ marginRight: '8px' }}></span>
                                Создание...
                            </>
                        ) : (
                            'Код приглашения'
                        )}
                    </button>
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