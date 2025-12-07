import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';
import apiClient from '../api/client.js';
import Header from '../components/Header';
import NavComponents from '../components/NavComponents';

const ProfileView = () => {
    const navigate = useNavigate();
    const auth = useAuth();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [admins, setAdmins] = useState([]);
    const [users, setUsers] = useState([]);
    const [invitationLink, setInvitationLink] = useState('');
    const [invitationCode, setInvitationCode] = useState('');

    useEffect(() => {
        let isMounted = true;
        
        const loadProfileData = async () => {
            if (!auth.isAuthenticated()) {
                if (isMounted) {
                    navigate('/authorization');
                }
                return;
            }

            setLoading(true);
            setError(null);

            try {
                // Load current user
                const userData = await apiClient.getCurrentUser();
                
                if (!isMounted) return;
                
                setUser(userData);

                // Load admins if user is not admin
                if (userData.role !== 'admin') {
                    try {
                        const adminsData = await apiClient.getMyAdmins();
                        if (isMounted) {
                            setAdmins(adminsData);
                        }
                    } catch (err) {
                        console.error('Ошибка при загрузке админов:', err);
                    }
                }

                // Load users if user is admin
                if (userData.role === 'admin') {
                    try {
                        const usersData = await apiClient.getMyUsers();
                        if (isMounted) {
                            setUsers(usersData);
                        }
                    } catch (err) {
                        console.error('Ошибка при загрузке пользователей:', err);
                    }
                }
            } catch (err) {
                console.error('Ошибка при загрузке профиля:', err);
                if (isMounted) {
                    if (err.type === 'unauthorized' || err.status === 401) {
                        auth.removeToken();
                        apiClient.removeToken();
                        navigate('/authorization');
                    } else {
                        setError(err.message || 'Не удалось загрузить данные профиля');
                    }
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        loadProfileData();
        
        return () => {
            isMounted = false;
        };
    }, [auth.token, navigate]); // Only depend on token, not the whole auth object

    const handleCreateInvitation = async () => {
        try {
            const data = await apiClient.createInvitation();
            setInvitationLink(data.link);
            setInvitationCode(data.link.split('/').pop() || '');
        } catch (err) {
            console.error('Ошибка при создании приглашения:', err);
            setError(err.message || 'Не удалось создать пригласительный код');
        }
    };

    const handleJoinAdmin = async () => {
        if (!invitationCode.trim()) {
            setError('Введите пригласительный код');
            return;
        }

        try {
            await apiClient.joinAdmin(invitationCode.trim());
            setInvitationCode('');
            // Reload admins
            const adminsData = await apiClient.getMyAdmins();
            setAdmins(adminsData);
        } catch (err) {
            console.error('Ошибка при присоединении к админу:', err);
            setError(err.message || 'Не удалось присоединиться к админу');
        }
    };

    const handleLeaveAdmin = async (adminId) => {
        if (!window.confirm('Вы уверены, что хотите отвязаться от этого админа?')) {
            return;
        }

        try {
            await apiClient.leaveAdmin(adminId);
            // Reload admins
            const adminsData = await apiClient.getMyAdmins();
            setAdmins(adminsData);
        } catch (err) {
            console.error('Ошибка при отвязке от админа:', err);
            setError(err.message || 'Не удалось отвязаться от админа');
        }
    };

    const handleRemoveUser = async (userId) => {
        if (!window.confirm('Вы уверены, что хотите отвязать этого пользователя?')) {
            return;
        }

        try {
            await apiClient.removeUserFromAdmin(userId);
            // Reload users
            const usersData = await apiClient.getMyUsers();
            setUsers(usersData);
        } catch (err) {
            console.error('Ошибка при отвязке пользователя:', err);
            setError(err.message || 'Не удалось отвязать пользователя');
        }
    };

    const handleLogout = () => {
        auth.removeToken();
        apiClient.removeToken();
        navigate('/authorization');
    };

    if (loading) {
        return (
            <div className="done-wrapper">
                <Header />
                <NavComponents />
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Загрузка профиля...</p>
                </div>
            </div>
        );
    }

    if (error && !user) {
        return (
            <div className="done-wrapper">
                <Header />
                <NavComponents />
                <div className="error-container">
                    <h3>Ошибка</h3>
                    <p>{error}</p>
                    <button onClick={() => navigate('/done')}>Вернуться на главную</button>
                </div>
            </div>
        );
    }

    return (
        <div className="done-wrapper">
          <Header />
          <NavComponents />
          <div className="profile-section">
            <div className="profile-left">
                <h3 className='settings'>Настройки</h3>
                    <div className="profile-info">
                        {user && (
                            <>
                                <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    gap: '10px', 
                                    marginBottom: '15px',
                                    paddingBottom: '15px',
                                    borderBottom: '1px solid #e1e5e9'
                                }}>
                                    <div style={{
                                        width: '60px',
                                        height: '60px',
                                        borderRadius: '50%',
                                        background: 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'white',
                                        fontSize: '24px',
                                        fontWeight: 'bold',
                                        boxShadow: '0 4px 12px rgba(0, 123, 255, 0.3)'
                                    }}>
                                        {user.email.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <p style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#333' }}>
                                            {user.email}
                                        </p>
                                        <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#666' }}>
                                            {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
                                        </p>
                                    </div>
                                </div>
                                <div style={{ 
                                    display: 'grid', 
                                    gridTemplateColumns: '1fr 1fr', 
                                    gap: '10px',
                                    marginTop: '15px'
                                }}>
                                    <div style={{
                                        padding: '10px',
                                        background: '#f8f9fa',
                                        borderRadius: '8px',
                                        border: '1px solid #e1e5e9'
                                    }}>
                                        <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>ID пользователя</p>
                                        <p style={{ margin: '5px 0 0 0', fontSize: '16px', fontWeight: '600', color: '#0022FF' }}>
                                            #{user.id}
                                        </p>
                                    </div>
                                    <div style={{
                                        padding: '10px',
                                        background: user.role === 'admin' ? '#d4edda' : '#fff3cd',
                                        borderRadius: '8px',
                                        border: `1px solid ${user.role === 'admin' ? '#c3e6cb' : '#ffeaa7'}`
                                    }}>
                                        <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>Статус</p>
                                        <p style={{ 
                                            margin: '5px 0 0 0', 
                                            fontSize: '16px', 
                                            fontWeight: '600',
                                            color: user.role === 'admin' ? '#155724' : '#856404'
                                        }}>
                                            {user.role === 'admin' ? '✓ Админ' : 'Пользователь'}
                                        </p>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                    {error && (
                        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
                            {error}
                        </div>
                    )}
                    {user?.role === 'admin' && (
                        <div className="admin-section" style={{ marginTop: '20px' }}>
                            <h4>Пригласительный код</h4>
                            <button 
                                className='account' 
                                onClick={handleCreateInvitation}
                                style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    gap: '8px'
                                }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                                </svg>
                                Создать приглашение
                            </button>
                            {invitationLink && (
                                <div style={{ 
                                    marginTop: '15px', 
                                    padding: '15px',
                                    background: '#f8f9fa',
                                    borderRadius: '8px',
                                    border: '1px solid #e1e5e9'
                                }}>
                                    <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#666', fontWeight: '600' }}>
                                        Пригласительный код:
                                    </p>
                                    <p style={{ 
                                        margin: 0, 
                                        fontSize: '14px', 
                                        color: '#0022FF',
                                        wordBreak: 'break-all',
                                        fontFamily: 'monospace',
                                        padding: '8px',
                                        background: 'white',
                                        borderRadius: '4px',
                                        border: '1px solid #e1e5e9'
                                    }}>
                                        {invitationLink}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                    {user?.role !== 'admin' && (
                        <div className="join-admin-section" style={{ marginTop: '20px' }}>
                            <h4>Присоединиться к админу</h4>
                            <input
                                type="text"
                                placeholder="Введите пригласительный код"
                                value={invitationCode}
                                onChange={(e) => setInvitationCode(e.target.value)}
                                style={{ 
                                    marginBottom: '10px', 
                                    padding: '12px', 
                                    width: '100%',
                                    boxSizing: 'border-box',
                                    border: '1px solid #e1e5e9',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            />
                            <button 
                                className='link' 
                                onClick={handleJoinAdmin}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px'
                                }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                                </svg>
                                Присоединиться
                            </button>
                        </div>
                    )}
                    <button className='exit' onClick={handleLogout}>Выход</button>
            </div>
            <div className="profile-right">
                <h3 className='static'>Общая статистика</h3>
                    {user?.role === 'admin' && (
                        <div className="members-fill">
                            <h4>Мои пользователи ({users.length})</h4>
                            {users.length > 0 ? (
                                <ul>
                                    {users.map((u) => (
                                        <li key={u.id} style={{ marginBottom: '10px' }}>
                                            {u.email} (ID: {u.id})
                                            <button
                                                onClick={() => handleRemoveUser(u.id)}
                                                style={{ marginLeft: '10px', color: 'white' }}
                                            >
                                                Отвязать
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Нет привязанных пользователей</p>
                            )}
                        </div>
                    )}
                    {user?.role !== 'admin' && (
                <div className="members-fill">
                            <h4>Мои админы ({admins.length})</h4>
                            {admins.length > 0 ? (
                                <ul>
                                    {admins.map((admin) => (
                                        <li key={admin.id} style={{ marginBottom: '10px' }}>
                                            {admin.email} (ID: {admin.id})
                                            <button
                                                onClick={() => handleLeaveAdmin(admin.id)}
                                                style={{ marginLeft: '10px', color: 'red' }}
                                            >
                                                Отвязаться
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Нет привязанных админов</p>
                            )}
                </div>
                    )}
            </div>
          </div>
        </div>
    );
};

export default ProfileView;