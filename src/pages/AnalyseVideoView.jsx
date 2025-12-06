import { useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';
import OtchetComponent from '../components/OtchetComponent';
import VideoGraph from '../components/VideoGraph';

const AnalyseVideo = () => {
  const location = useLocation();
  const [initialVideo, setInitialVideo] = useState(null);

  useEffect(() => {
    if (location.state) {
      setInitialVideo({
        file: location.state.videoFile,
        url: location.state.videoUrl
      });
    }
  }, [location.state]);

  return (
    <div className="analyse-container">
      <Header />
      <NavComponents />
      <div className="analyse-content">
        <div className="analyse-left">
          <VideoGraph initialVideo={initialVideo} />
          <BestMomentsComponent />
        </div>
        <div className="analyse-right">
          <OtchetComponent />
        </div>
      </div>
    </div>
  );
};

export default AnalyseVideo;