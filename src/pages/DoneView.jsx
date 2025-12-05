import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/useAuth';

import logo from '../images/logo.png';
import Profile from '../images/Profile.png';
import NavComponents from '../components/NavComponents';

const DoneView = () => {
  const navigate = useNavigate();
  const auth = useAuth();

  const handleProfileClick = () => {
    console.log('Клик по профилю');
  };

  const handleLogout = () => {
    auth.removeToken();
    navigate('/authorization');
  };

  return (
    <div className="done-wrapper">
      <header className="main-header">
        <img className='logo-main' src={logo} alt="BrainTube Logo" />
        <button 
          className="profile-button"
          onClick={handleProfileClick}
          aria-label="Профиль">
          <img src={Profile} alt="Профиль пользователя" />
        </button>
      </header>
      <NavComponents />
    </div>
  );
};

export default DoneView;