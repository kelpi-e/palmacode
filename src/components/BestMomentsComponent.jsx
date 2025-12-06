import VideoPlayer from "./VideoPlayer";

const BestMomentsComponent = () => {
    const moments = [
        { time: "1:12:34", attention: 95 },
        { time: "2:02:54", attention: 85 },
        { time: "3:15:22", attention: 78 },
        { time: "2:02:54", attention: 85 },
        { time: "3:15:22", attention: 78 },
        { time: "2:02:54", attention: 85 },
        { time: "3:15:22", attention: 78 }
    ];

    return (
        <div className="best-wrapper">
            <h1 className="best-par">Лучшие моменты</h1>
            <div className="best-moments-grid">
                {moments.map((moment, index) => (
                    <div className="moment-item" key={index}>
                        <VideoPlayer 
                            time={moment.time}
                            attention={moment.attention}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default BestMomentsComponent;