import { Navigate } from 'react-router-dom';
import { useAuth } from '../api/useAuth.js';

/**
 * Protected Route Component
 * Redirects to authorization page if user is not authenticated
 */
const ProtectedRoute = ({ children }) => {
    const auth = useAuth();

    if (!auth.isAuthenticated()) {
        return <Navigate to="/authorization" replace />;
    }

    return children;
};

export default ProtectedRoute;

