import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RegistrationView from '../pages/RegistrationView';
import AuthorizationView from '../pages/AuthorizationView';
import VerifyView from '../pages/VerifyView';
import DoneView from '../pages/DoneView';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RegistrationView />} />
        <Route path="/authorization" element={<AuthorizationView />} />
        <Route path="/verify" element={<VerifyView />} />
        <Route path="/done" element={<DoneView />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;