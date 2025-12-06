import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import VideoComponent from '../components/VideoComponent';

const DoneView = () => {
  const videoCount = 6;

  return (
    <div className="done-wrapper">
      <Header />
      <NavComponents />
      <div className="video-stats-grid">
        {Array.from({ length: videoCount }).map((_, index) => (
          <div className="video-item" key={index}>
            <VideoComponent />
          </div>
        ))}
      </div>
    </div>
  );
};

export default DoneView;