import Header from '../components/Header';
import NavComponents from '../components/NavComponents';
import BestMomentsComponent from '../components/BestMomentsComponent';
import OtchetComponent from '../components/OtchetComponent';
import HumanGraphs from '../components/HumanGraphs';

const AnalyseHuman = () => {
    return (
        <div className="analyse-container">
            <Header />
            <NavComponents />
            <div className="analyse-content">
                <div className="analyse-left">
                    <HumanGraphs />
                    <BestMomentsComponent />
                </div>
                <div className="analyse-right">
                    <OtchetComponent />
                </div>
            </div>
        </div>
    );
};

export default AnalyseHuman;