import Play from '../images/Play.png'

const OtchetComponent = ({ videoData }) => {
    return (
        <div className="otchet-wrapper">
            <h1 className='main-otchet'>Список отчетов</h1>
            <div className="otchet-col">
                <div className="otchet-item">
                    <div className="otchet-content">
                        <div className="otchet-name">Отчет 1</div>
                        <div className="otchet-actions">
                            <button className="download-btn">
                                <img src={Play} alt="Скачать" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OtchetComponent;