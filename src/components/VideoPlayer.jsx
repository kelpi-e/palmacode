import Play from '../images/RightStr.png';
import eop from '../images/ExampleOfPlayer.png';

const VideoPlayer = (props) => {
    return (
        <div className="video-player-wrapper">
            <div className="video-player-container">
                <div className="video-player-placeholder">
                    <img className='ex' src={eop} alt="Превью видео" />
                    <div className="button-play">
                        <img className='play' src={Play} alt="Воспроизвести" />
                    </div>
                    <div className="video-player-info">
                        <div className="video-stats-content">
                            <div className="video-duration">{props.time}</div>
                            <div className="video-engagement">{props.attention}% вовлеченности</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoPlayer;