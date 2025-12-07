import { useState, useRef, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import reportData from '../report_20251206_153204.json';

const VideoGraph = ({ initialVideo, videoData }) => {
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
    
    const [reportRecords, setReportRecords] = useState([]);
    const [maxVideoTime, setMaxVideoTime] = useState(0);
    
    const videoRef = useRef(null);
    const analysisIntervalRef = useRef(null);

    // Загрузка данных из JSON отчета
    useEffect(() => {
        if (reportData && reportData.records && reportData.records.length > 0) {
            const records = reportData.records;
            setReportRecords(records);
            
            // Находим максимальное время видео
            const maxTime = Math.max(...records.map(r => r.video_ms || 0));
            setMaxVideoTime(maxTime);
            
            // Преобразуем данные для графика внимания/расслабления
            // Создаем точки каждые 10% прогресса
            const graphDataPoints = [];
            const totalPoints = 100; // 100 точек для плавного графика
            
            for (let i = 0; i <= totalPoints; i++) {
                const progressPercent = i;
                const targetTime = (progressPercent / 100) * maxTime;
                
                // Находим ближайшую запись по времени
                const closestRecord = records.reduce((prev, curr) => {
                    const prevDiff = Math.abs((prev.video_ms || 0) - targetTime);
                    const currDiff = Math.abs((curr.video_ms || 0) - targetTime);
                    return currDiff < prevDiff ? curr : prev;
                });
                
                graphDataPoints.push({
                    time: progressPercent.toString(),
                    attention: Math.round(closestRecord.attention || 0),
                    relaxation: Math.round(closestRecord.relaxation || 0)
                });
            }
            
            setAttentionData(graphDataPoints);
            
            // Устанавливаем начальные значения
            if (records.length > 0) {
                const firstRecord = records[0];
                setCurrentAttention(Math.round(firstRecord.attention || 0));
                setCurrentRelaxation(Math.round(firstRecord.relaxation || 0));
                setCurrentAlpha(firstRecord.alpha || 0);
                setCurrentBeta(firstRecord.beta || 0);
                setCurrentTheta(firstRecord.theta || 0);
                
                // Генерируем спектральные данные на основе первого значения
                setAlphaData(generateSpectralData(firstRecord.alpha || 0, 'alpha'));
                setBetaData(generateSpectralData(firstRecord.beta || 0, 'beta'));
                setThetaData(generateSpectralData(firstRecord.theta || 0, 'theta'));
            }
        }
    }, []);
    
    // Инициализация при получении начального видео
    useEffect(() => {
        if (initialVideo?.url) {
            setIsLoading(true);
            setVideoFile(initialVideo.file || null);
            setVideoUrl(initialVideo.url);
            setIsLoading(false);
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
            
            // Используем данные из отчета, если они есть
            if (reportRecords && reportRecords.length > 0) {
                const firstRecord = reportRecords[0];
                setCurrentAttention(Math.round(firstRecord.attention || 0));
                setCurrentRelaxation(Math.round(firstRecord.relaxation || 0));
                setCurrentAlpha(firstRecord.alpha || 0);
                setCurrentBeta(firstRecord.beta || 0);
                setCurrentTheta(firstRecord.theta || 0);
                
                setAlphaData(generateSpectralData(firstRecord.alpha || 0, 'alpha'));
                setBetaData(generateSpectralData(firstRecord.beta || 0, 'beta'));
                setThetaData(generateSpectralData(firstRecord.theta || 0, 'theta'));
            }
        }
    };

    const handleVideoLoaded = () => {
        if (videoRef.current) 
        {
            setVideoDuration(videoRef.current.duration);
            setIsLoading(false);
        }
    };

    // Функция для получения данных по времени видео
    const getDataByVideoTime = (videoTimeMs) => {
        if (!reportRecords || reportRecords.length === 0) return null;
        
        // Находим ближайшую запись по времени
        const closestRecord = reportRecords.reduce((prev, curr) => {
            const prevDiff = Math.abs((prev.video_ms || 0) - videoTimeMs);
            const currDiff = Math.abs((curr.video_ms || 0) - videoTimeMs);
            return currDiff < prevDiff ? curr : prev;
        });
        
        return closestRecord;
    };
    
    const startAnalysis = () => {
        if (!videoRef.current) 
            return;
        
        setIsPlaying(true);
        videoRef.current.play();
        
        // Clear any existing interval
        if (analysisIntervalRef.current) {
            clearInterval(analysisIntervalRef.current);
        }
        
        // Update data in real-time during playback
        analysisIntervalRef.current = setInterval(() => {
            if (videoRef.current && !videoRef.current.paused) 
            {
                const time = videoRef.current.currentTime;
                setCurrentTime(time);
                
                if (videoDuration > 0 && maxVideoTime > 0) {
                    // Конвертируем время видео в миллисекунды
                    const videoTimeMs = (time / videoDuration) * maxVideoTime;
                    
                    // Получаем данные из отчета
                    const record = getDataByVideoTime(videoTimeMs);
                    
                    if (record) {
                        // Обновляем текущие значения
                        setCurrentAttention(Math.round(record.attention || 0));
                        setCurrentRelaxation(Math.round(record.relaxation || 0));
                        setCurrentAlpha(record.alpha || 0);
                        setCurrentBeta(record.beta || 0);
                        setCurrentTheta(record.theta || 0);
                        
                        // Обновляем спектральные данные
                        setAlphaData(generateSpectralData(record.alpha || 0, 'alpha'));
                        setBetaData(generateSpectralData(record.beta || 0, 'beta'));
                        setThetaData(generateSpectralData(record.theta || 0, 'theta'));
                        
                        // Обновляем график внимания/расслабления
                        const progress = Math.min(time / videoDuration, 1);
                        const dataIndex = Math.min(Math.floor(progress * (attentionData.length - 1)), attentionData.length - 1);
                        
                        if (dataIndex >= 0 && dataIndex < attentionData.length) {
                            const updatedAttentionData = [...attentionData];
                            updatedAttentionData[dataIndex] = {
                                ...updatedAttentionData[dataIndex],
                                attention: Math.round(record.attention || 0),
                                relaxation: Math.round(record.relaxation || 0)
                            };
                            setAttentionData(updatedAttentionData);
                        }
                    }
                }
            }
        }, 100); // Update every 100ms for smooth tracking
    };

    const formatTime = (seconds) => {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
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
        
        // Сбрасываем данные на начальные значения из отчета
        if (reportRecords && reportRecords.length > 0) {
            const firstRecord = reportRecords[0];
            setCurrentAttention(Math.round(firstRecord.attention || 0));
            setCurrentRelaxation(Math.round(firstRecord.relaxation || 0));
            setCurrentAlpha(firstRecord.alpha || 0);
            setCurrentBeta(firstRecord.beta || 0);
            setCurrentTheta(firstRecord.theta || 0);
            
            setAlphaData(generateSpectralData(firstRecord.alpha || 0, 'alpha'));
            setBetaData(generateSpectralData(firstRecord.beta || 0, 'beta'));
            setThetaData(generateSpectralData(firstRecord.theta || 0, 'theta'));
        }
        
        if (analysisIntervalRef.current)
            clearInterval(analysisIntervalRef.current);
        
        // Перезапускаем анализ
        startAnalysis();
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
                {!videoUrl && (
                    <div style={{ 
                        textAlign: 'center', 
                        padding: '40px',
                        background: 'white',
                        borderRadius: '12px',
                        border: '2px dashed #dee2e6'
                    }}>
                        <label className="upload-btn" style={{ 
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer'
                        }}>
                            <input
                                type="file"
                                accept="video/*"
                                onChange={handleVideoUpload}
                                style={{ display: 'none' }}
                            />
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/>
                            </svg>
                            Загрузить видео для анализа
                        </label>
                        <p style={{ marginTop: '15px', color: '#666', fontSize: '14px' }}>
                            Поддерживаемые форматы: MP4, AVI, MOV, MKV
                        </p>
                    </div>
                )}
                {videoUrl && (
                    <div className="video-player-full">
                        <div className="video-wrapper">
                            <video
                                ref={videoRef}
                                src={videoUrl}
                                onLoadedMetadata={handleVideoLoaded}
                                onTimeUpdate={() => {
                                    if (videoRef.current) {
                                        setCurrentTime(videoRef.current.currentTime);
                                    }
                                }}
                                onEnded={() => {
                                    pauseAnalysis();
                                }}
                                className="main-video-player"
                                onClick={() => {
                                    if (isPlaying) {
                                        pauseAnalysis();
                                    } else {
                                        startAnalysis();
                                    }
                                }}
                            />
                            {!isPlaying && (
                                <div className="video-play-overlay" onClick={startAnalysis}>
                                    <div className="play-button-large">
                                        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                                            <circle cx="30" cy="30" r="30" fill="rgba(0, 0, 0, 0.6)"/>
                                            <path d="M24 18L42 30L24 42V18Z" fill="white"/>
                                        </svg>
                                    </div>
                                </div>
                            )}
                            <div className="video-progress-bar">
                                <div 
                                    className="video-progress-fill"
                                    style={{ 
                                        width: `${videoDuration > 0 ? (currentTime / videoDuration) * 100 : 0}%` 
                                    }}
                                />
                            </div>
                        </div>
                        <div className="video-controls-full">
                            <button 
                                onClick={isPlaying ? pauseAnalysis : startAnalysis}
                                disabled={isLoading}
                                className="video-control-btn play-pause-btn">
                                {isPlaying ? (
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                        <rect x="6" y="4" width="4" height="16" rx="1"/>
                                        <rect x="14" y="4" width="4" height="16" rx="1"/>
                                    </svg>
                                ) : (
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M8 5v14l11-7z"/>
                                    </svg>
                                )}
                            </button>
                            <div className="video-time-display">
                                <span>{formatTime(currentTime)}</span>
                                <span className="time-separator">/</span>
                                <span>{formatTime(videoDuration)}</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max={videoDuration || 0}
                                value={currentTime}
                                onChange={(e) => {
                                    const newTime = parseFloat(e.target.value);
                                    if (videoRef.current) {
                                        videoRef.current.currentTime = newTime;
                                        setCurrentTime(newTime);
                                        
                                        // Обновляем данные при перемотке
                                        if (videoDuration > 0 && maxVideoTime > 0) {
                                            const videoTimeMs = (newTime / videoDuration) * maxVideoTime;
                                            const record = getDataByVideoTime(videoTimeMs);
                                            
                                            if (record) {
                                                setCurrentAttention(Math.round(record.attention || 0));
                                                setCurrentRelaxation(Math.round(record.relaxation || 0));
                                                setCurrentAlpha(record.alpha || 0);
                                                setCurrentBeta(record.beta || 0);
                                                setCurrentTheta(record.theta || 0);
                                                
                                                setAlphaData(generateSpectralData(record.alpha || 0, 'alpha'));
                                                setBetaData(generateSpectralData(record.beta || 0, 'beta'));
                                                setThetaData(generateSpectralData(record.theta || 0, 'theta'));
                                            }
                                        }
                                    }
                                }}
                                className="video-seek-bar"
                            />
                            <button 
                                onClick={restartAnalysis}
                                disabled={isLoading}
                                className="video-control-btn restart-btn"
                                title="Перезапустить">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                                </svg>
                            </button>
                        </div>
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