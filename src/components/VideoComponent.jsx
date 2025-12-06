import Image from '../images/Image.png';
import Str from '../images/Arrow.png';
import Dots from '../images/Dots.png';

const VideoComponent = () => {
    const videoData = {
        title: 'Название видео',
        rating: 'Рейтинг видео'
    };

    return (
        <div className="video-stats-container">
            <div className="video-stats-card">
                <div className="video-content">
                    <div className="video-image-container">
                        <img src={Image} alt="Превью видео" className="video-preview" />
                        <div className="video-overlay">
                            <img src={Dots} alt="Опции" className="dots-icon" />
                        </div>
                    </div>
                    <div className="video-bottom-content">
                        <div className="video-info">
                            <div className="video-info-item">
                                <p className="video-title">{videoData.title}</p>
                            </div>
                            <div className="video-info-item">
                                <p className="rating-value">{videoData.rating}</p>
                            </div>
                        </div>
                        <div className="statistics-section">
                            <button className="statics" onClick={() => console.log('Статистика кликнута')}>
                                <span className="statistics-text">Статистика</span>
                                <img src={Str} alt="Стрелка" className="arrow-icon" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoComponent;