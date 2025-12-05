import { useState } from 'react';

import Image from '../images/Image.png';

const VideoComponent = () => {
    const [isExpanded, setIsExpanded] = useState(false);
    const toggleExpand = () => { setIsExpanded(!isExpanded) };

    return (
        <div className="video-stats-container">
            <div className="video-stats-card">
                <img src={Image} />
            </div>
        </div>
    );
};

export default VideoComponent;