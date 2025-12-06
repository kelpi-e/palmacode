import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';

import example from '../images/ExamplePic.png';

const AnalyseVideo = () => {
    return (
        <div className="done-wrapper">
            <Header />
            <NavComponents />
            <div className="analyse-left">
                <img class="graphics-pic" src={example} />
                <div className="components-info">
                    <BestMomentsComponent />
                </div>
            </div>
        </div>
    );
};

export default AnalyseVideo;