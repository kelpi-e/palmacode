import Play from '../images/RightStr.png';
import eop from '../images/ExampleOfPlayer.png';

const VideoPlayer = () => {
    const VideoPlayerData = {
        time: "1:12:34",
        attention: 95
    };

    return (
        <div className="video-player-wrapper">
            <div className="video-player-container">
                <div className="video-player-placeholder">
                    <img className='ex' src={eop} />
                    <div className="button-play">
                        <img className='play' src={Play} />
                    </div>
                </div>
                <div className="video-player-info">
                    <div className="video-stats-content">
                        <div className="video-duration">{VideoPlayerData.time}</div>
                        <div className="video-engagement">{VideoPlayerData.attention}% вовлеченности</div>
                    </div>
                </div>
            </div>
        </div>
    )
};

export default VideoPlayer;