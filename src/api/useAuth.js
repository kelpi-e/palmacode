import { useState } from 'react'

export const useAuth = () => {
    const [token, setTokenState] = useState(localStorage.getItem('access_token') || '');
  
    const setToken = (newToken) => {
        setTokenState(newToken);
        localStorage.setItem('access_token', newToken);
    };
    
    const removeToken = () => {
        setTokenState('');
        localStorage.removeItem('access_token');
    };
    
    const getToken = () => {
        return token;
    };
    
    return { token, setToken, removeToken, getToken };
};