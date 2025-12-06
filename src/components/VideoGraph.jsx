import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const VideoGraph = () => {
    const [data, setData] = useState([
        { time: '00:00', value: 30 },
        { time: '01:00', value: 45 },
        { time: '02:00', value: 60 },
        { time: '03:00', value: 55 },
        { time: '04:00', value: 70 },
        { time: '05:00', value: 85 },
        { time: '06:00', value: 80 },
        { time: '07:00', value: 90 },
        { time: '08:00', value: 75 },
        { time: '09:00', value: 95 },
    ]);

    const [isAnimating, setIsAnimating] = useState(false);

    const updateData = () => {
        setIsAnimating(true);
        const newData = data.map(item => ({
            ...item,
            value: Math.max(0, Math.min(100, item.value + (Math.random() * 20 - 10)))
        }));
        setData(newData);
        
        setTimeout(() => setIsAnimating(false), 1000);
    };

    useEffect(() => {
        const interval = setInterval(updateData, 5000);
        return () => clearInterval(interval);
    }, [data]);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="label">{`Время: ${label}`}</p>
                    <p className="value" style={{ color: payload[0].color }}>
                        {`Вовлеченность: ${payload[0].value}%`}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="graph-container">
            <div className="graph-header">
                <h2 className="graph-title">Статистика вовлеченности по времени</h2>
                <button 
                    className={`update-btn ${isAnimating ? 'animating' : ''}`}
                    onClick={updateData}
                    disabled={isAnimating}>
                    {isAnimating ? 'Обновление...' : 'Обновить данные'}
                </button>
            </div>
            <div className="graph-wrapper">
                <ResponsiveContainer width="100%" height={500}>
                    <LineChart
                        data={data}
                        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                        <CartesianGrid 
                            strokeDasharray="3 3" 
                            stroke="#e0e0e0" 
                            vertical={false}/>
                        <XAxis 
                            dataKey="time" 
                            stroke="#333"
                            tick={{ fill: '#333' }}
                            axisLine={{ stroke: '#333' }}
                            tickLine={{ stroke: '#333' }}
                            label={{ 
                                value: 'Время (мин)', 
                                position: 'insideBottomRight', 
                                offset: -10,
                                fill: '#333'
                            }}/>
                        <YAxis 
                            stroke="#333"
                            tick={{ fill: '#333' }}
                            axisLine={{ stroke: '#333' }}
                            tickLine={{ stroke: '#333' }}
                            domain={[0, 100]}
                            label={{ 
                                value: 'Вовлеченность (%)', 
                                angle: -90, 
                                position: 'insideLeft',
                                fill: '#333'
                            }}/>
                        <Tooltip 
                            content={<CustomTooltip />}
                            animationDuration={300}/>
                        <Legend 
                            verticalAlign="top" 
                            height={36}
                            formatter={() => 'Общая вовлеченность'}/>
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#007bff"
                            strokeWidth={3}
                            dot={{ 
                                r: 6, 
                                strokeWidth: 2,
                                stroke: '#fff',
                                fill: '#007bff'
                            }}
                            activeDot={{ 
                                r: 8, 
                                strokeWidth: 2,
                                stroke: '#fff',
                                fill: '#007bff'
                            }}
                            name="Вовлеченность"
                            animationDuration={1000}
                            animationEasing="ease-in-out"/>
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default VideoGraph;