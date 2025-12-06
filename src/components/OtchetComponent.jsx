import Play from '../images/Play.png'

const OtchetComponent = () => {
    const otchetCount = 6;

    return (
        <div className="otchet-wrapper">
            <h1 className='main-otchet'>Список отчетов</h1>
            <div className="otchet-col">
                {Array.from({ length: otchetCount }).map((_, index) => (
                    <div className="otchet-item" key={index}>
                        <div className="otchet-content">
                            <div className="otchet-name">Отчет {index + 1}</div>
                            <div className="otchet-actions">
                                <button className="download-btn">
                                    <img src={Play} alt="Скачать" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default OtchetComponent;