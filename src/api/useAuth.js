import { useState } from 'react'

export const useAuth = () => {
    const [token, setTokenState] = useState(localStorage.getItem('webid_token') || '');
  
    const setToken = (newToken) => {
        setTokenState(newToken);
        localStorage.setItem('webid_token', newToken);
    };
    
    const removeToken = () => {
        setTokenState('');
        localStorage.removeItem('webid_token');
    };
    
    const getToken = () => {
        return token;
    };
    
    return { token, setToken, removeToken, getToken };
};