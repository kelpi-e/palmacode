import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';
import OtchetComponent from '../components/OtchetComponent';
import VideoGraph from '../components/VideoGraph';

const AnalyseVideo = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [initialVideo, setInitialVideo] = useState(null);
    const [videoData, setVideoData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const API_BASE_URL = 'http://192.168.31.111:8099'; 

    useEffect(() => {
        const fetchVideoData = async () => {
            if (!location.state) 
            {
                setError('Нет данных о видео');
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);

            try 
            {
                const { videoFile, videoUrl, videoId, serverResponse } = location.state;
                
                setInitialVideo({
                    file: videoFile,
                    url: videoUrl
                });

                if (serverResponse) 
                {
                    setVideoData(serverResponse);
                    setLoading(false);
                    return;
                }

                if (videoId) 
                {
                    const token = localStorage.getItem('authToken') || 
                                  localStorage.getItem('token') || 
                                  sessionStorage.getItem('authToken');
                    
                    const headers = {
                        'Accept': 'application/json',
                    };
                    
                    if (token)
                        headers['Authorization'] = `Bearer ${token}`;

                    const response = await fetch(`${API_BASE_URL}/video/${videoId}`, {
                        method: 'GET',
                        headers: headers,
                    });

                    if (!response.ok)
                        throw new Error(`Ошибка получения данных видео: ${response.status}`);

                    const data = await response.json();
                    setVideoData(data);
                } 
                else 
                {
                    if (videoFile) 
                      {
                        const formData = new FormData();
                        formData.append('video', videoFile);
                        
                        const token = localStorage.getItem('authToken') || 
                                      localStorage.getItem('token') || 
                                      sessionStorage.getItem('authToken');
                        
                        const headers = {
                            'Accept': 'application/json',
                        };
                        
                        if (token)
                            headers['Authorization'] = `Bearer ${token}`;

                        const uploadResponse = await fetch(`${API_BASE_URL}/video`, {
                            method: 'POST',
                            headers: headers,
                            body: formData,
                        });

                        if (!uploadResponse.ok)
                            throw new Error(`Ошибка загрузки видео: ${uploadResponse.status}`);

                        const uploadData = await uploadResponse.json();
                        setVideoData(uploadData);
                    }
                }
            } 
            catch (err) 
            {
                console.error('Ошибка при получении данных видео:', err);
                setError(err.message || 'Произошла ошибка при загрузке данных видео');
            } 
            finally 
            {
                setLoading(false);
            }
        };

        fetchVideoData();
    }, [location.state]);

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
                    <BestMomentsComponent videoData={videoData} />
                </div>
                <div className="analyse-right">
                    <OtchetComponent videoData={videoData} />
                </div>
            </div>
        </div>
    );
};

export default AnalyseVideo;