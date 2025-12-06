import { useState, useRef, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

const VideoGraph = ({ initialVideo }) => {
    const [videoFile, setVideoFile] = useState(initialVideo?.file || null);
    const [videoUrl, setVideoUrl] = useState(initialVideo?.url || '');
    const [videoDuration, setVideoDuration] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    
    const [attentionData, setAttentionData] = useState([]);
    const [alphaData, setAlphaData] = useState([]);
    const [betaData, setBetaData] = useState([]);
    const [thetaData, setThetaData] = useState([]);
    
    const [currentAttention, setCurrentAttention] = useState(50);
    const [currentRelaxation, setCurrentRelaxation] = useState(50);
    const [currentAlpha, setCurrentAlpha] = useState(49);
    const [currentBeta, setCurrentBeta] = useState(21);
    const [currentTheta, setCurrentTheta] = useState(30);
    
    const videoRef = useRef(null);
    const analysisIntervalRef = useRef(null);

    // Инициализация при получении начального видео
    useEffect(() => {
        if (initialVideo?.file && initialVideo?.url) {
            setIsLoading(true);
            setVideoFile(initialVideo.file);
            setVideoUrl(initialVideo.url);
            
            const initialGraphData = generateInitialGraphData();
            setAttentionData(initialGraphData);
            
            if (initialGraphData.length > 0) {
                setCurrentAttention(Math.round(initialGraphData[0].attention));
                setCurrentRelaxation(Math.round(initialGraphData[0].relaxation));
            }
            
            setAlphaData(generateSpectralData(currentAlpha, 'alpha'));
            setBetaData(generateSpectralData(currentBeta, 'beta'));
            setThetaData(generateSpectralData(currentTheta, 'theta'));
        }
    }, [initialVideo]);

    const generateSpectralData = (baseValue, type) => {
        const points = [];
        const frequencies = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
        
        frequencies.forEach((freq, index) => {
            let value;
            switch(type) 
            {
                case 'alpha':
                    value = baseValue * Math.exp(-Math.pow((freq - 50) / 30, 2));
                    break;
                case 'beta':
                    value = baseValue * Math.exp(-Math.pow((freq - 60) / 25, 2));
                    break;
                case 'theta':
                    value = baseValue * Math.exp(-Math.pow((freq - 40) / 35, 2));
                    break;
                default:
                    value = baseValue;
            }
            
            value += (Math.random() * 10 - 5);
            value = Math.max(0, Math.min(100, value));
            
            points.push({ freq: freq.toString(), value: Math.round(value) });
        });
        
        return points;
    };

    const generateInitialGraphData = () => {
        const initialData = [];
        
        for (let i = 0; i <= 10; i++) 
        {
            const time = (i * 10).toString();
            
            const attention = 50 + 30 * Math.sin(i * 0.3) + (Math.random() * 10 - 5);
            const relaxation = 100 - attention;
            
            initialData.push({
                time: time,
                attention: Math.max(0, Math.min(100, attention)),
                relaxation: Math.max(0, Math.min(100, relaxation))
            });
        }
        
        return initialData;
    };

    const handleVideoUpload = (event) => {
        const file = event.target.files[0];
        if (file) 
        {
            setIsLoading(true);
            setVideoFile(file);
            
            const url = URL.createObjectURL(file);
            setVideoUrl(url);
            
            const initialGraphData = generateInitialGraphData();
            setAttentionData(initialGraphData);
            
            if (initialGraphData.length > 0) 
            {
                setCurrentAttention(Math.round(initialGraphData[0].attention));
                setCurrentRelaxation(Math.round(initialGraphData[0].relaxation));
            }
            
            setAlphaData(generateSpectralData(currentAlpha, 'alpha'));
            setBetaData(generateSpectralData(currentBeta, 'beta'));
            setThetaData(generateSpectralData(currentTheta, 'theta'));
        }
    };

    const handleVideoLoaded = () => {
        if (videoRef.current) 
        {
            setVideoDuration(videoRef.current.duration);
            setIsLoading(false);
        }
    };

    const startAnalysis = () => {
        if (!videoRef.current) 
            return;
        
        setIsPlaying(true);
        videoRef.current.play();
        
        analysisIntervalRef.current = setInterval(() => {
            if (videoRef.current) 
            {
                const time = videoRef.current.currentTime;
                setCurrentTime(time);
                
                const progress = Math.min(time / videoDuration, 1);
                const dataIndex = Math.min(Math.floor(progress * 10), 10);
                
                if (dataIndex >= 0 && dataIndex < attentionData.length) 
                {
                    const attentionChange = (Math.random() * 6 - 3);
                    const newAttention = Math.max(0, Math.min(100, 
                        attentionData[dataIndex].attention + attentionChange
                    ));
                    
                    const relaxationChange = (Math.random() * 6 - 3);
                    const newRelaxation = Math.max(0, Math.min(100,
                        attentionData[dataIndex].relaxation + relaxationChange
                    ));
                    
                    setCurrentAttention(Math.round(newAttention));
                    setCurrentRelaxation(Math.round(newRelaxation));
                    
                    const updatedAttentionData = [...attentionData];
                    updatedAttentionData[dataIndex] = {
                        time: updatedAttentionData[dataIndex].time,
                        attention: newAttention,
                        relaxation: newRelaxation
                    };
                    setAttentionData(updatedAttentionData);
                    
                    const alpha = 49 + (Math.random() * 6 - 3);
                    const beta = 21 + (Math.random() * 6 - 3);
                    const theta = 30 + (Math.random() * 6 - 3);
                    
                    setCurrentAlpha(Math.round(alpha));
                    setCurrentBeta(Math.round(beta));
                    setCurrentTheta(Math.round(theta));
                    
                    setAlphaData(generateSpectralData(alpha, 'alpha'));
                    setBetaData(generateSpectralData(beta, 'beta'));
                    setThetaData(generateSpectralData(theta, 'theta'));
                }
            }
        }, 500);
    };

    const pauseAnalysis = () => {
        setIsPlaying(false);
        
        if (videoRef.current) 
            videoRef.current.pause();
        
        if (analysisIntervalRef.current) 
        {
            clearInterval(analysisIntervalRef.current);
            analysisIntervalRef.current = null;
        }
    };

    const restartAnalysis = () => {
        if (videoRef.current) 
        {
            videoRef.current.currentTime = 0;
            videoRef.current.play();
            setCurrentTime(0);
            setIsPlaying(true);
        }
        
        const newData = generateInitialGraphData();
        setAttentionData(newData);
        
        if (newData.length > 0) 
        {
            setCurrentAttention(Math.round(newData[0].attention));
            setCurrentRelaxation(Math.round(newData[0].relaxation));
        }
        
        setAlphaData(generateSpectralData(currentAlpha, 'alpha'));
        setBetaData(generateSpectralData(currentBeta, 'beta'));
        setThetaData(generateSpectralData(currentTheta, 'theta'));
        
        if (analysisIntervalRef.current)
            clearInterval(analysisIntervalRef.current);
        
        analysisIntervalRef.current = setInterval(() => {
            if (videoRef.current)
            {
                const time = videoRef.current.currentTime;
                setCurrentTime(time);
                
                const progress = Math.min(time / videoDuration, 1);
                const dataIndex = Math.min(Math.floor(progress * 10), 10);
                
                if (dataIndex >= 0 && dataIndex < newData.length) 
                {
                    const attentionChange = (Math.random() * 6 - 3);
                    const newAttention = Math.max(0, Math.min(100, 
                        newData[dataIndex].attention + attentionChange
                    ));
                    
                    const relaxationChange = (Math.random() * 6 - 3);
                    const newRelaxation = Math.max(0, Math.min(100,
                        newData[dataIndex].relaxation + relaxationChange
                    ));
                    
                    setCurrentAttention(Math.round(newAttention));
                    setCurrentRelaxation(Math.round(newRelaxation));
                    
                    const updatedData = [...newData];
                    updatedData[dataIndex] = {
                        time: updatedData[dataIndex].time,
                        attention: newAttention,
                        relaxation: newRelaxation
                    };
                    setAttentionData(updatedData);
                    
                    const alpha = 49 + (Math.random() * 6 - 3);
                    const beta = 21 + (Math.random() * 6 - 3);
                    const theta = 30 + (Math.random() * 6 - 3);
                    
                    setCurrentAlpha(Math.round(alpha));
                    setCurrentBeta(Math.round(beta));
                    setCurrentTheta(Math.round(theta));
                    
                    setAlphaData(generateSpectralData(alpha, 'alpha'));
                    setBetaData(generateSpectralData(beta, 'beta'));
                    setThetaData(generateSpectralData(theta, 'theta'));
                }
            }
        }, 500);
    };

    useEffect(() => {
        return () => {
            if (analysisIntervalRef.current)
                clearInterval(analysisIntervalRef.current);
            
            if (videoUrl)
                URL.revokeObjectURL(videoUrl);
        };
    }, [videoUrl]);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) 
        {
            return (
                <div className="custom-tooltip">
                    <p className="label">{`Время: ${label}%`}</p>
                    {payload.map((entry, index) => (
                        <p key={index} className="value" style={{ color: entry.color }}>
                            {`${entry.name}: ${entry.value}%`}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    const SpectralTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) 
        {
            return (
                <div className="custom-tooltip">
                    <p className="label">{`Частота: ${label} Hz`}</p>
                    <p className="value" style={{ color: payload[0].color }}>
                        {`Амплитуда: ${payload[0].value}`}
                    </p>
                </div>
            );
        }
        return null;
    };

    const renderSpectralGraph = (data, color, name) => {
        const gradientId = `color-${name}`;
        const colors = {
            alpha: { primary: '#667eea', secondary: '#764ba2' },
            beta: { primary: '#FF6B6B', secondary: '#FF8E8E' },
            theta: { primary: '#4ECDC4', secondary: '#45B7AF' }
        };

        return (
            <div className="spectral-graph">
                <div className="spectral-label">{name.toUpperCase()}</div>
                <ResponsiveContainer width="100%" height={80}>
                    <AreaChart
                        data={data}
                        margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
                        <CartesianGrid 
                            strokeDasharray="3 3" 
                            stroke="#e0e0e0" 
                            vertical={false}
                            horizontal={false}/>
                        <XAxis 
                            dataKey="freq"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#666', fontSize: 9 }}
                            ticks={['0', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100']}/>
                        <YAxis 
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#666', fontSize: 9 }}
                            domain={[0, 100]}
                            hide={true}/>
                        <Tooltip 
                            content={<SpectralTooltip />}
                            animationDuration={300}/>
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={colors[color].primary}
                            fill={`url(#${gradientId})`}
                            strokeWidth={1.5}
                            fillOpacity={0.3}
                            animationDuration={500}
                            isAnimationActive={true}/>
                        <defs>
                            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={colors[color].primary} stopOpacity={0.6}/>
                                <stop offset="95%" stopColor={colors[color].primary} stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        );
    };

    return (
        <div className="monitoring-container">
            <div className="video-upload-section">
                <div className="video-controls">
                    {!videoUrl && (
                        <label className="upload-btn">
                            <input
                                type="file"
                                accept="video/*"
                                onChange={handleVideoUpload}
                                style={{ display: 'none' }}
                            />
                            Загрузить видео
                        </label>
                    )}
                    {videoUrl && (
                        <div className="player-controls">
                            <button 
                                onClick={isPlaying ? pauseAnalysis : startAnalysis}
                                disabled={isLoading}
                                className="control-btn">
                                {isPlaying ? 'Пауза' : 'Анализ'}
                            </button>
                            <button 
                                onClick={restartAnalysis}
                                disabled={isLoading}
                                className="control-btn">
                                Перезапуск
                            </button>
                            <div className="video-info">
                                {isLoading ? 'Загрузка...' : 
                                 `Время: ${currentTime.toFixed(1)} / ${videoDuration.toFixed(1)} сек`}
                            </div>
                        </div>
                    )}
                </div>
                {videoUrl && (
                    <div className="video-preview">
                        <video
                            ref={videoRef}
                            src={videoUrl}
                            onLoadedMetadata={handleVideoLoaded}
                            style={{ width: '100%', maxHeight: '200px' }}
                            controls={false}
                        />
                    </div>
                )}
            </div>
            <div className="monitoring-content">
                <div className="monitoring-left">
                    <h2 className="monitoring-title">Анализ видео</h2>
                    <div className="variants-list">
                        <div className="variant-item">
                            <span className="variant-name">Внимание</span>
                            <span className="variant-value">{currentAttention}%</span>
                        </div>
                        <div className="variant-item">
                            <span className="variant-name">Расслабление</span>
                            <span className="variant-value">{currentRelaxation}%</span>
                        </div>
                        <div className="variant-item">
                            <span className="variant-name">Альфа</span>
                            <span className="variant-value">{currentAlpha}%</span>
                        </div>
                        <div className="variant-item">
                            <span className="variant-name">Бета</span>
                            <span className="variant-value">{currentBeta}%</span>
                        </div>
                        <div className="variant-item">
                            <span className="variant-name">Тета</span>
                            <span className="variant-value">{currentTheta}%</span>
                        </div>
                    </div>
                    <div className="video-stats">
                        <div className="stat-item">
                            <span className="stat-label">Статус:</span>
                            <span className={`stat-value ${isPlaying ? 'playing' : 'paused'}`}>
                                {isPlaying ? 'Анализ в процессе' : 'На паузе'}
                            </span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Прогресс:</span>
                            <span className="stat-value">
                                {videoDuration > 0 
                                    ? `${Math.round((currentTime / videoDuration) * 100)}%` 
                                    : '0%'}
                            </span>
                        </div>
                    </div>
                </div>
                <div className="monitoring-right">
                    <div className="attention-section">
                        <h3 className="section-title">Внимание / Расслабление</h3>
                        <div className="graph-wrapper-small">
                            {attentionData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={200}>
                                    <LineChart
                                        data={attentionData}
                                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                        <CartesianGrid 
                                            strokeDasharray="3 3" 
                                            stroke="#e0e0e0" 
                                            vertical={false}/>
                                        <XAxis 
                                            dataKey="time"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fill: '#666', fontSize: 11 }}
                                            label={{ 
                                                value: 'Прогресс (%)', 
                                                position: 'insideBottomRight', 
                                                offset: -10,
                                                fill: '#666',
                                                fontSize: 12
                                            }}/>
                                        <YAxis 
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fill: '#666', fontSize: 11 }}
                                            domain={[0, 100]}
                                            label={{ 
                                                value: 'Уровень (%)', 
                                                angle: -90, 
                                                position: 'insideLeft',
                                                offset: 15,
                                                fill: '#666',
                                                fontSize: 12
                                            }}/>
                                        <Tooltip 
                                            content={<CustomTooltip />}
                                            animationDuration={300}/>
                                        <Legend 
                                            verticalAlign="top" 
                                            height={36}
                                            iconType="circle"
                                            iconSize={8}/>
                                        <Line
                                            type="monotone"
                                            dataKey="attention"
                                            stroke="#FF6B6B"
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ 
                                                r: 5, 
                                                strokeWidth: 2,
                                                stroke: '#fff',
                                                fill: '#FF6B6B'
                                            }}
                                            name="Внимание"
                                            animationDuration={500}
                                            isAnimationActive={true}/>
                                        <Line
                                            type="monotone"
                                            dataKey="relaxation"
                                            stroke="#4ECDC4"
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ 
                                                r: 5, 
                                                strokeWidth: 2,
                                                stroke: '#fff',
                                                fill: '#4ECDC4'
                                            }}
                                            name="Расслабление"
                                            animationDuration={500}
                                            isAnimationActive={true}/>
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="no-data">
                                    <p>Загрузите видео для начала анализа</p>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="spectral-section">
                        <h3 className="section-title">Спектральные данные</h3>
                        <div className="spectral-graphs">
                            {alphaData.length > 0 ? (
                                <>
                                    {renderSpectralGraph(alphaData, 'alpha', 'alpha')}
                                    {renderSpectralGraph(betaData, 'beta', 'beta')}
                                    {renderSpectralGraph(thetaData, 'theta', 'theta')}
                                </>
                            ) : (
                                <div className="no-data-small">
                                    <p>Данные появятся после загрузки видео</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoGraph;