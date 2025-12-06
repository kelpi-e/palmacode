import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RegistrationView from '../pages/RegistrationView';
import AuthorizationView from '../pages/AuthorizationView';
import VerifyView from '../pages/VerifyView';
import DoneView from '../pages/DoneView';
import AnalyseVideoView from '../pages/AnalyseVideoView';
import AnalyseHumanView from '../pages/AnalyseHumanView';
import ProfileView from '../pages/ProfileView';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RegistrationView />} />
        <Route path="/authorization" element={<AuthorizationView />} />
        <Route path="/verify" element={<VerifyView />} />
        <Route path="/done" element={<DoneView />} />
        <Route path="/profile" element={<ProfileView />} />
        <Route path="/analyse-video" element={<AnalyseVideoView />} />
        <Route path="/analyse-human" element={<AnalyseHumanView />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;