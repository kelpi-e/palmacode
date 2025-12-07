import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RegistrationView from '../pages/RegistrationView';
import AuthorizationView from '../pages/AuthorizationView';
import VerifyView from '../pages/VerifyView';
import DoneView from '../pages/DoneView';
import AnalyseVideoView from '../pages/AnalyseVideoView';
import AnalyseHumanView from '../pages/AnalyseHumanView';
import ProfileView from '../pages/ProfileView';
import ProtectedRoute from '../components/ProtectedRoute';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RegistrationView />} />
        <Route path="/authorization" element={<AuthorizationView />} />
        <Route path="/verify" element={<VerifyView />} />
        <Route 
          path="/done" 
          element={
            <ProtectedRoute>
              <DoneView />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <ProfileView />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/analyse-video/:videoId?" 
          element={
            <ProtectedRoute>
              <AnalyseVideoView />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/analyse-human" 
          element={
            <ProtectedRoute>
              <AnalyseHumanView />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;