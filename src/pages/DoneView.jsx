import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';
import apiClient from '../api/client.js';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import VideoComponent from '../components/VideoComponent';

const DoneView = () => {
    const navigate = useNavigate();
    const auth = useAuth();
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Load videos from server and localStorage - ONLY ONCE on mount or when auth token changes
    useEffect(() => {
        let isMounted = true;
        let isLoading = false; // Prevent concurrent loads
        
        const loadVideos = async () => {
            // Prevent multiple concurrent loads
            if (isLoading) return;
            isLoading = true;
            
            setLoading(true);
            setError(null);

            try {
                const isAuth = auth.isAuthenticated();
                
                // First, try to load from server if authenticated
                if (isAuth) {
                    try {
                        const serverVideos = await apiClient.getAllVideos();
                        
                        if (!isMounted) return;
                        
                        console.log('Видео с сервера:', serverVideos);

                        // Merge with local videos
                        const localVideos = JSON.parse(localStorage.getItem('uploadedVideos') || '[]');
                        
                        // Create a map of server videos by ID
                        const serverVideosMap = new Map();
                        serverVideos.forEach(video => {
                            serverVideosMap.set(video.id, video);
                        });

                        // Update local videos with server data
                        const updatedLocalVideos = localVideos.map(localVideo => {
                            if (localVideo.serverData?.id) {
                                const serverVideo = serverVideosMap.get(localVideo.serverData.id);
                                if (serverVideo) {
                                    return {
                                        ...localVideo,
                                        serverData: serverVideo,
                                        name: serverVideo.name || localVideo.name,
                                    };
                                }
                            }
                            return localVideo;
                        });

                        // Add new server videos that aren't in local storage
                        // Don't load all videos at once to avoid performance issues
                        // Videos will be loaded on demand when needed
                        for (const serverVideo of serverVideos) {
                            const exists = updatedLocalVideos.some(
                                v => v.serverData?.id === serverVideo.id || v.id === serverVideo.id
                            );
                            if (!exists) {
                                // Create placeholder - video will be loaded when user clicks on it
                                updatedLocalVideos.push({
                                    id: serverVideo.id,
                                    name: serverVideo.name,
                                    size: 0,
                                    type: 'video/*',
                                    uploadDate: new Date().toLocaleDateString('ru-RU'),
                                    videoUrl: null, // Will be loaded on demand
                                    serverData: serverVideo,
                                    file: null,
                                    needsLoad: true, // Flag to load video when needed
                                });
                            }
                        }

                        if (isMounted) {
                            setVideos(updatedLocalVideos);
                            localStorage.setItem('uploadedVideos', JSON.stringify(updatedLocalVideos));
                        }
                    } catch (err) {
                        console.error('Ошибка при загрузке видео с сервера:', err);
                        
                        if (!isMounted) return;
                        
                        // Fall back to local storage
                        const savedVideos = localStorage.getItem('uploadedVideos');
                        if (savedVideos) {
                            try {
                                const parsed = JSON.parse(savedVideos);
                                if (isMounted) {
                                    setVideos(parsed);
                                }
                            } catch (parseErr) {
                                console.error('Ошибка при парсинге сохраненных видео:', parseErr);
                                if (isMounted) {
                                    setError('Ошибка при загрузке сохраненных видео');
                                }
                            }
                        } else if (err.type !== 'network') {
                            // Only show error if it's not a network error (might be temporary)
                            if (isMounted) {
                                setError('Не удалось загрузить видео с сервера');
                            }
                        }
                    }
                } else {
                    // Not authenticated, load only from localStorage
                    const savedVideos = localStorage.getItem('uploadedVideos');
                    if (savedVideos) {
                        try {
                            const parsed = JSON.parse(savedVideos);
                            if (isMounted) {
                                setVideos(parsed);
                            }
                        } catch (err) {
                            console.error('Ошибка при загрузке сохраненных видео:', err);
                            if (isMounted) {
                                setError('Ошибка при загрузке сохраненных видео');
                            }
                        }
                    }
                }
            } catch (err) {
                console.error('Ошибка при загрузке видео:', err);
                if (isMounted) {
                    setError('Не удалось загрузить видео');
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
                isLoading = false;
            }
        };

        loadVideos();
        
        return () => {
            isMounted = false;
        };
    }, [auth.token]); // Only depend on token, not the whole auth object or videos array

    useEffect(() => {
        const handleVideoUploaded = (event) => {
            const video = event.detail;
            setVideos(prevVideos => {
                // Check if video already exists (by ID or serverData.id)
                const exists = prevVideos.some(v => 
                    v.id === video.id || 
                    (v.serverData?.id && v.serverData.id === video.serverData?.id)
                );
                
                if (exists) {
                    // Update existing video
                    return prevVideos.map(v => 
                        (v.id === video.id || (v.serverData?.id && v.serverData.id === video.serverData?.id))
                            ? { ...v, ...video }
                            : v
                    );
                } else {
                    // Add new video
                    const newVideos = [...prevVideos, video];
                    localStorage.setItem('uploadedVideos', JSON.stringify(newVideos));
                    return newVideos;
                }
            });
        };

        window.addEventListener('videoUploaded', handleVideoUploaded);
        
        return () => {
            window.removeEventListener('videoUploaded', handleVideoUploaded);
        };
    }, [videos]);

    const handleClearVideo = async (id) => {
        if (!window.confirm('Вы уверены, что хотите удалить это видео?')) {
            return;
        }

        setLoading(true);
        const videoToRemove = videos.find(video => video.id === id);
        
        // Delete from server if it exists there
        if (videoToRemove?.serverData?.id && auth.isAuthenticated()) {
            try {
                await apiClient.deleteVideo(videoToRemove.serverData.id);
                console.log('Видео удалено с сервера');
            } catch (err) {
                console.error('Ошибка при удалении видео с сервера:', err);
                // Continue with local deletion even if server deletion fails
                if (err.type !== 'network') {
                    alert('Не удалось удалить видео с сервера, но оно будет удалено локально.');
                }
            }
        }

        // Remove from local state and storage
        setVideos(prevVideos => {
            if (videoToRemove && videoToRemove.videoUrl)
                URL.revokeObjectURL(videoToRemove.videoUrl);
            const newVideos = prevVideos.filter(video => video.id !== id);
            localStorage.setItem('uploadedVideos', JSON.stringify(newVideos));
            return newVideos;
        });
        
        setLoading(false);
    };

    const handleAnalyzeVideo = async (video) => {
        setLoading(true);
        try 
        {
            // Always use videoId from server data
            const targetVideoId = video.serverData?.id || video.id;
            
            if (targetVideoId) 
            {
                // Navigate to specific video page using videoId in URL
                navigate(`/analyse-video/${targetVideoId}`);
            }
            else 
            {
                throw new Error('Не удалось определить ID видео. Видео должно быть загружено на сервер.');
            }
        } 
        catch (err) 
        {
            console.error('Ошибка при переходе к анализу:', err);
            alert(err.message || 'Не удалось начать анализ видео');
        } 
        finally 
        {
            setLoading(false);
        }
    };

    const clearAllVideos = async () => {
        if (!window.confirm(`Вы уверены, что хотите удалить все видео (${videos.length})?`)) {
            return;
        }

        setLoading(true);
        
        // Delete from server if authenticated
        if (auth.isAuthenticated()) {
            const serverVideos = videos.filter(v => v.serverData?.id);
            for (const video of serverVideos) {
                try {
                    await apiClient.deleteVideo(video.serverData.id);
                } catch (err) {
                    console.error(`Ошибка при удалении видео ${video.serverData.id}:`, err);
                }
            }
        }

        // Clean up local URLs
        videos.forEach(video => {
            if (video.videoUrl)
                URL.revokeObjectURL(video.videoUrl);
        });
        
        setVideos([]);
        localStorage.removeItem('uploadedVideos');
        
        setLoading(false);
    };

    return (
        <div className="done-wrapper">
            <Header />
            <NavComponents />
            <div className="video-stats-grid">
                <div className="section-header">
                    <div className="section-title-wrapper">
                        <h3 className="section-title">
                            {videos.length > 0 ? 
                                `Загруженные видео (${videos.length})` : 
                                'Нет загруженных видео'
                            }
                        </h3>
                        {videos.length > 0 && (
                            <p className="section-subtitle">
                                Нажмите "Проанализировать" для просмотра детальной статистики
                            </p>
                        )}
                    </div>
                    {/* {videos.length > 0 && (
                        <button 
                            onClick={clearAllVideos}
                            className="clear-all-btn"
                            disabled={loading}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: '6px' }}>
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                            </svg>
                            Очистить все
                        </button>
                    )} */}
                </div>
                {loading && videos.length === 0 ? (
                    <div className="loading-container">
                        <div className="spinner"></div>
                        <p>Загрузка видео...</p>
                    </div>
                ) : videos.length > 0 ? (
                    <div className="videos-grid">
                        {videos.map((video) => (
                            <div className="video-item" key={video.id || video.serverData?.id || `video-${Date.now()}`}>
                                <div className="video-header">
                                    <span className="video-name" title={video.name}>
                                        {video.name && video.name.length > 30 ? 
                                            video.name.substring(0, 30) + '...' : 
                                            video.name || 'Без названия'
                                        }
                                    </span>
                                    <button
                                        onClick={() => handleClearVideo(video.id)}
                                        className="delete-btn"
                                        disabled={loading}
                                        title="Удалить видео">
                                        Удалить
                                    </button>
                                </div>
                                <div className="video-info">
                                    {video.uploadDate && (
                                        <div className="upload-date">
                                            {video.uploadDate}
                                        </div>
                                    )}
                                    {video.size > 0 && (
                                        <div className="video-size">
                                            {(video.size / (1024 * 1024)).toFixed(2)} MB
                                        </div>
                                    )}
                                    {video.serverData && (
                                        <div className="server-status" style={{
                                            color: '#4caf50',
                                            fontSize: '12px',
                                            marginTop: '5px'
                                        }}>
                                            Загружено на сервер
                                        </div>
                                    )}
                                </div>
                                <VideoComponent 
                                    videoUrl={video.videoUrl} 
                                    videoName={video.name}
                                    videoId={video.serverData?.id || video.id}
                                    onLoadVideo={async () => {
                                        // Load video from server if not loaded
                                        if (!video.videoUrl && (video.serverData?.id || video.id)) {
                                            try {
                                                setLoading(true);
                                                const videoId = video.serverData?.id || video.id;
                                                const videoBlob = await apiClient.downloadVideoFile(videoId);
                                                const videoUrl = URL.createObjectURL(videoBlob);
                                                
                                                // Update video in state
                                                setVideos(prevVideos => 
                                                    prevVideos.map(v => 
                                                        (v.id === video.id && v.id === videoId) || 
                                                        (v.serverData?.id === video.serverData?.id && v.serverData?.id === videoId)
                                                            ? { ...v, videoUrl }
                                                            : v
                                                    )
                                                );
                                                
                                                // Update localStorage
                                                const savedVideos = JSON.parse(localStorage.getItem('uploadedVideos') || '[]');
                                                const updatedVideos = savedVideos.map(v => 
                                                    (v.id === video.id && v.id === videoId) || 
                                                    (v.serverData?.id === video.serverData?.id && v.serverData?.id === videoId)
                                                        ? { ...v, videoUrl }
                                                        : v
                                                );
                                                localStorage.setItem('uploadedVideos', JSON.stringify(updatedVideos));
                                            } catch (err) {
                                                console.error('Ошибка при загрузке превью видео:', err);
                                                alert('Не удалось загрузить превью видео: ' + (err.message || 'Неизвестная ошибка'));
                                            } finally {
                                                setLoading(false);
                                            }
                                        }
                                    }}
                                />
                                <button
                                    onClick={() => handleAnalyzeVideo(video)}
                                    className="analyze-btn"
                                    disabled={loading || !(video.serverData?.id || video.id)}>
                                    {loading ? (
                                        <>
                                            <span className="spinner" style={{ marginRight: '8px' }}></span>
                                            Загрузка...
                                        </>
                                    ) : (
                                        <>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: '6px' }}>
                                                <path d="M8 5v14l11-7z"/>
                                            </svg>
                                            Проанализировать
                                        </>
                                    )}
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-videos-container">
                        {error ? (
                            <div className="error-message" style={{ color: 'red', marginBottom: '20px' }}>
                                <strong>Ошибка:</strong> {error}
                                <button 
                                    onClick={() => window.location.reload()} 
                                    style={{ 
                                        marginLeft: '10px', 
                                        padding: '5px 10px',
                                        cursor: 'pointer'
                                    }}>
                                    Обновить
                                </button>
                            </div>
                        ) : (
                            <div className="no-videos-message">
                                <p>Используйте кнопку "Загрузить видео" в шапке сайта.</p>
                                <p>Поддерживаемые форматы: MP4, AVI, MOV, MKV и другие</p>
                                <p>Максимальный размер: 500MB</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default DoneView;