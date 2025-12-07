import { useState, useEffect } from 'react';
import { STORAGE_KEYS } from './config';

export const useAuth = () => {
    const [token, setTokenState] = useState(() => {
        return (
            localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) ||
            localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) ||
            localStorage.getItem(STORAGE_KEYS.TOKEN) ||
            ''
        );
    });
  
    // Remove the useEffect that was causing re-renders
    // Token will be updated only when setToken is called

    const setToken = (newToken) => {
        if (newToken) {
            setTokenState(newToken);
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newToken);
            // Keep backward compatibility
            localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, newToken);
        } else {
            removeToken();
        }
    };
    
    const removeToken = () => {
        setTokenState('');
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        sessionStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    };
    
    const getToken = () => {
        return token || 
            localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) ||
            localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) ||
            localStorage.getItem(STORAGE_KEYS.TOKEN) ||
            '';
    };

    const isAuthenticated = () => {
        return !!getToken();
    };
    
    return { token, setToken, removeToken, getToken, isAuthenticated };
};