import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import apiClient from '../api/client.js';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';
import OtchetComponent from '../components/OtchetComponent';
import VideoGraph from '../components/VideoGraph';

const AnalyseVideo = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [initialVideo, setInitialVideo] = useState(null);
    const [videoData, setVideoData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchVideoData = async () => {
            if (!videoId) 
            {
                setError('ID видео не указан');
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);

            try 
            {
                // Always fetch video data from server using videoId
                const data = await apiClient.getVideoById(videoId);
                setVideoData(data);
                
                // Try to get video file from server
                try {
                    const videoBlob = await apiClient.downloadVideoFile(videoId);
                    const videoUrl = URL.createObjectURL(videoBlob);
                    
                    setInitialVideo({
                        file: null, // We don't have the original file
                        url: videoUrl,
                        serverUrl: data.url // Store server URL as well
                    });
                } catch (downloadErr) {
                    console.warn('Не удалось загрузить файл видео, используем URL:', downloadErr);
                    // If download fails, try to use URL from server data
                    if (data.url) {
                        setInitialVideo({
                            file: null,
                            url: data.url,
                            serverUrl: data.url
                        });
                    } else {
                        throw new Error('Не удалось получить видео файл');
                    }
                }
            } 
            catch (err) 
            {
                console.error('Ошибка при получении данных видео:', err);
                
                if (err.type === 'network') {
                    setError(err.message);
                } else if (err.type === 'unauthorized' || err.status === 401) {
                    setError('Требуется авторизация. Перенаправляем на страницу входа...');
                    setTimeout(() => {
                        navigate('/authorization');
                    }, 2000);
                } else {
                    setError(err.message || 'Произошла ошибка при загрузке данных видео');
                }
            } 
            finally 
            {
                setLoading(false);
            }
        };

        fetchVideoData();
    }, [videoId, navigate]);

    if (loading) {
        return (
            <div className="analyse-container">
                <Header />
                <NavComponents />
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Загрузка данных видео...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="analyse-container">
                <Header />
                <NavComponents />
                <div className="error-container">
                    <h3>Ошибка</h3>
                    <p>{error}</p>
                    <button onClick={() => navigate('/done')}>Вернуться на главную</button>
                </div>
            </div>
        );
    }

    return (
        <div className="analyse-container">
            <Header />
            <NavComponents />
            <div className="analyse-content">
                <div className="analyse-left">
                    <VideoGraph 
                        initialVideo={initialVideo} 
                        videoData={videoData} />
                </div>
                <div className="analyse-right">
                    <OtchetComponent videoData={videoData} />
                </div>
            </div>
        </div>
    );
};

export default AnalyseVideo;