import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import VideoComponent from '../components/VideoComponent';

const DoneView = () => {
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const videoCount = 6;

  useEffect(() => {
    const savedVideos = localStorage.getItem('uploadedVideos');
    if (savedVideos) {
      setVideos(JSON.parse(savedVideos));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('uploadedVideos', JSON.stringify(videos));
  }, [videos]);

  const handleClearVideo = (id) => {
    setVideos(prevVideos => {
      const videoToRemove = prevVideos.find(video => video.id === id);
      if (videoToRemove && videoToRemove.url)
        URL.revokeObjectURL(videoToRemove.url);
      return prevVideos.filter(video => video.id !== id);
    });
  };

  const addVideo = (video) => {
    setVideos(prevVideos => [...prevVideos, video]);
  };

  useEffect(() => {
    const handleVideoUploaded = (event) => {
      const video = event.detail;
      addVideo(video);
    };

    window.addEventListener('videoUploaded', handleVideoUploaded);
    
    return () => {
      window.removeEventListener('videoUploaded', handleVideoUploaded);
    };
  }, []);

  return (
    <div className="done-wrapper">
      <Header />
      <NavComponents />
      <div className="video-stats-grid">
        <h3 className="section-title">
          {videos.length > 0 ? 'Загруженные видео' : 'Нет загруженных видео'}
        </h3>
        
        {videos.length > 0 ? (
          <div className="videos-grid">
            {videos.map((video) => (
              <div className="video-item" key={video.id}>
                <div className="video-header">
                  <span className="video-name">
                    {video.name}
                  </span>
                  <button
                    onClick={() => handleClearVideo(video.id)}
                    className="delete-btn">
                    Удалить
                  </button>
                </div>
                <div className="upload-date">
                  Загружено: {video.uploadDate}
                </div>
                <VideoComponent />
                <button
                  onClick={() => navigate('/analyse-video', { 
                    state: { 
                      videoFile: video.file,
                      videoUrl: video.url
                    } 
                  })}
                  className="analyze-btn">
                  Проанализировать
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-videos-container">
            <div className="no-videos-message">
              Используйте кнопку "Загрузить видео" в шапке сайта.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DoneView;