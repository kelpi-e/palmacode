import { useState, useRef, useEffect } from 'react';
import Image from '../images/Image.png';
import Str from '../images/Arrow.png';
import Dots from '../images/Dots.png';
import Play from '../images/Play.png';

const VideoComponent = ({ videoUrl, videoName, videoId, onLoadVideo }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const videoRef = useRef(null);
    
    // Try to load video when component mounts if videoUrl is not available
    useEffect(() => {
        if (!videoUrl && videoId && onLoadVideo) {
            // Don't auto-load, let user click to load
            // This prevents too many requests
        }
    }, [videoUrl, videoId, onLoadVideo]);

    const handlePlayPause = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    return (
        <div className="video-stats-container">
            <div className="video-stats-card">
                <div className="video-content">
                    <div className="video-image-container">
                        {videoUrl ? (
                            <div style={{ position: 'relative', width: '100%', height: '100%' }}>
                                <video
                                    ref={videoRef}
                                    src={videoUrl}
                                    className="video-preview"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    onPlay={() => setIsPlaying(true)}
                                    onPause={() => setIsPlaying(false)}
                                />
                                <div className="video-overlay" onClick={handlePlayPause}>
                                    {!isPlaying && (
                                        <img 
                                            src={Play} 
                                            alt="Play" 
                                            style={{ 
                                                width: '40px', 
                                                height: '40px', 
                                                cursor: 'pointer' 
                                            }} 
                                        />
                                    )}
                                    <img src={Dots} alt="Опции" className="dots-icon" />
                                </div>
                            </div>
                        ) : videoId ? (
                            <div style={{ 
                                position: 'relative', 
                                width: '100%', 
                                height: '100%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: '#f0f0f0'
                            }}>
                                {isLoading ? (
                                    <div className="spinner" style={{ width: '30px', height: '30px' }}></div>
                                ) : (
                                    <>
                                        <img src={Image} alt="Превью видео" className="video-preview" />
                                        <div className="video-overlay" onClick={onLoadVideo} style={{ cursor: 'pointer' }}>
                                            <div style={{ 
                                                position: 'absolute', 
                                                top: '50%', 
                                                left: '50%', 
                                                transform: 'translate(-50%, -50%)',
                                                background: 'rgba(0,0,0,0.7)',
                                                color: 'white',
                                                padding: '8px 12px',
                                                borderRadius: '4px',
                                                fontSize: '12px'
                                            }}>
                                                Загрузить превью
                                            </div>
                                            <img src={Dots} alt="Опции" className="dots-icon" />
                                        </div>
                                    </>
                                )}
                            </div>
                        ) : (
                            <>
                                <img src={Image} alt="Превью видео" className="video-preview" />
                                <div className="video-overlay">
                                    <img src={Dots} alt="Опции" className="dots-icon" />
                                </div>
                            </>
                        )}
                    </div>
                    <div className="video-bottom-content">
                        <div className="video-info">
                            <div className="video-info-item">
                                <p className="video-title">{videoName || 'Название видео'}</p>
                            </div>
                            <div className="video-info-item">
                                <p className="rating-value">Рейтинг видео</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoComponent;