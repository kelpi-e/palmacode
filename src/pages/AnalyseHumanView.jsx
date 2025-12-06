import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';
import OtchetComponent from '../components/OtchetComponent';

import example from '../images/ExamplePic.png';

const AnalyseVideo = () => {
    return (
        <div className="analyse-container">
            <Header />
            <NavComponents />
            <div className="analyse-content">
                <div className="analyse-left">
                    <img className="graphics-pic" src={example} />
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