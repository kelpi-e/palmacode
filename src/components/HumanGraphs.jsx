import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const HumanGraphs = () => {
    const [data, setData] = useState([
        { time: '00:00', high: 25, medium: 20, low: 15 },
        { time: '01:00', high: 40, medium: 35, low: 30 },
        { time: '02:00', high: 55, medium: 50, low: 45 },
        { time: '03:00', high: 45, medium: 40, low: 35 },
        { time: '04:00', high: 65, medium: 60, low: 55 },
        { time: '05:00', high: 80, medium: 75, low: 70 },
        { time: '06:00', high: 75, medium: 70, low: 65 },
        { time: '07:00', high: 85, medium: 80, low: 75 },
        { time: '08:00', high: 70, medium: 65, low: 60 },
        { time: '09:00', high: 90, medium: 85, low: 80 },
    ]);

    const [isAnimating, setIsAnimating] = useState(false);
    const [showAllLines, setShowAllLines] = useState(true);

    const updateData = () => {
        setIsAnimating(true);
        const newData = data.map(item => ({
            ...item,
            high: Math.max(0, Math.min(100, item.high + (Math.random() * 15 - 7.5))),
            medium: Math.max(0, Math.min(100, item.medium + (Math.random() * 15 - 7.5))),
            low: Math.max(0, Math.min(100, item.low + (Math.random() * 15 - 7.5)))
        }));
        setData(newData);
        
        setTimeout(() => setIsAnimating(false), 1000);
    };

    useEffect(() => {
        const interval = setInterval(updateData, 5000);
        return () => clearInterval(interval);
    }, [data]);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) 
        {
            return (
                <div className="custom-tooltip">
                    <p className="label">{`Время: ${label}`}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }}>
                            {`${entry.dataKey === 'high' ? 'Высокая' : entry.dataKey === 'medium' ? 'Средняя' : 'Низкая'}: ${entry.value}%`}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="multi-graph-container">
            <div className="graph-header">
                <h2 className="graph-title">Анализ вовлеченности по группам</h2>
                <div className="graph-controls">
                    <button 
                        className={`update-btn ${isAnimating ? 'animating' : ''}`}
                        onClick={updateData}
                        disabled={isAnimating}>
                        {isAnimating ? 'Обновление...' : 'Обновить данные'}
                    </button>
                    <button 
                        className="toggle-btn"
                        onClick={() => setShowAllLines(!showAllLines)}>
                        {showAllLines ? 'Скрыть все' : 'Показать все'}
                    </button>
                </div>
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
                            height={36}/>
                        {showAllLines && (
                            <>
                                <Line
                                    type="monotone"
                                    dataKey="high"
                                    stroke="#007bff"
                                    strokeWidth={3}
                                    dot={{ 
                                        r: 5, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#007bff'
                                    }}
                                    activeDot={{ 
                                        r: 7, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#007bff'
                                    }}
                                    name="Высокая вовлеченность"
                                    animationDuration={1000}
                                    animationEasing="ease-in-out"/>
                                <Line
                                    type="monotone"
                                    dataKey="medium"
                                    stroke="#28a745"
                                    strokeWidth={3}
                                    strokeDasharray="5 5"
                                    dot={{ 
                                        r: 5, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#28a745'
                                    }}
                                    activeDot={{ 
                                        r: 7, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#28a745'
                                    }}
                                    name="Средняя вовлеченность"
                                    animationDuration={1200}
                                    animationEasing="ease-in-out"/>
                                <Line
                                    type="monotone"
                                    dataKey="low"
                                    stroke="#dc3545"
                                    strokeWidth={3}
                                    dot={{ 
                                        r: 5, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#dc3545'
                                    }}
                                    activeDot={{ 
                                        r: 7, 
                                        strokeWidth: 2,
                                        stroke: '#fff',
                                        fill: '#dc3545'
                                    }}
                                    name="Низкая вовлеченность"
                                    animationDuration={1400}
                                    animationEasing="ease-in-out"/>
                            </>
                        )}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default HumanGraphs;