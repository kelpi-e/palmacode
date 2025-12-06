import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import VideoComponent from '../components/VideoComponent';

const DoneView = () => {
    const navigate = useNavigate();
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const savedVideos = localStorage.getItem('uploadedVideos');
        if (savedVideos) 
        {
            try 
            {
                setVideos(JSON.parse(savedVideos));
            } 
            catch (err) 
            {
                console.error('Ошибка при загрузке сохраненных видео:', err);
            }
        }
    }, []);

    useEffect(() => {
        const handleVideoUploaded = (event) => {
            const video = event.detail;
            setVideos(prevVideos => {
                const newVideos = [...prevVideos, video];
                localStorage.setItem('uploadedVideos', JSON.stringify(newVideos));
                return newVideos;
            });
        };

        window.addEventListener('videoUploaded', handleVideoUploaded);
        
        return () => {
            window.removeEventListener('videoUploaded', handleVideoUploaded);
        };
    }, []);

    const handleClearVideo = (id) => {
        setVideos(prevVideos => {
            const videoToRemove = prevVideos.find(video => video.id === id);
            if (videoToRemove && videoToRemove.videoUrl)
                URL.revokeObjectURL(videoToRemove.videoUrl);
            const newVideos = prevVideos.filter(video => video.id !== id);
            localStorage.setItem('uploadedVideos', JSON.stringify(newVideos));
            return newVideos;
        });
    };

    const handleAnalyzeVideo = async (video) => {
        setLoading(true);
        try 
        {
            if (video.serverData) 
            {
                navigate('/analyse-video', { 
                    state: { 
                        videoFile: video.file,
                        videoUrl: video.videoUrl,
                        videoId: video.serverData.videoId || video.id,
                        serverResponse: video.serverData
                    } 
                });
            } 
            else 
            {
                navigate('/analyse-video', { 
                    state: { 
                        videoFile: video.file,
                        videoUrl: video.videoUrl
                    } 
                });
            }
        } 
        catch (err) 
        {
            console.error('Ошибка при переходе к анализу:', err);
            alert('Не удалось начать анализ видео');
        } 
        finally 
        {
            setLoading(false);
        }
    };

    const clearAllVideos = () => {
        videos.forEach(video => {
            if (video.videoUrl)
                URL.revokeObjectURL(video.videoUrl);
        });
        
        setVideos([]);
        localStorage.removeItem('uploadedVideos');
    };

    return (
        <div className="done-wrapper">
            <Header />
            <NavComponents />
            <div className="video-stats-grid">
                <div className="section-header">
                    <h3 className="section-title">
                        {videos.length > 0 ? 
                            `Загруженные видео (${videos.length})` : 
                            'Нет загруженных видео'
                        }
                    </h3>
                    {videos.length > 0 && (
                        <button 
                            onClick={clearAllVideos}
                            className="clear-all-btn"
                            disabled={loading}>
                            Очистить все
                        </button>
                    )}
                </div>
                {videos.length > 0 ? (
                    <div className="videos-grid">
                        {videos.map((video) => (
                            <div className="video-item" key={video.id}>
                                <div className="video-header">
                                    <span className="video-name" title={video.name}>
                                        {video.name.length > 30 ? 
                                            video.name.substring(0, 30) + '...' : 
                                            video.name
                                        }
                                    </span>
                                    <button
                                        onClick={() => handleClearVideo(video.id)}
                                        className="delete-btn"
                                        disabled={loading}
                                        title="Удалить видео">
                                        ×
                                    </button>
                                </div>
                                <div className="video-info">
                                    <div className="upload-date">
                                        {video.uploadDate}
                                    </div>
                                    <div className="video-size">
                                        {(video.size / (1024 * 1024)).toFixed(2)} MB
                                    </div>
                                    {video.serverData && (
                                        <div className="server-status">
                                            Загружено на сервер
                                        </div>
                                    )}
                                </div>
                                <VideoComponent videoUrl={video.videoUrl} />
                                <button
                                    onClick={() => handleAnalyzeVideo(video)}
                                    className="analyze-btn"
                                    disabled={loading}>
                                    {loading ? 'Загрузка...' : 'Проанализировать'}
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-videos-container">
                        <div className="no-videos-message">
                            <p>Используйте кнопку "Загрузить видео" в шапке сайта.</p>
                            <p>Поддерживаемые форматы: MP4, AVI, MOV, MKV и другие</p>
                            <p>Максимальный размер: 500MB</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DoneView;