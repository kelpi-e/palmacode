import { useNavigate } from 'react-router-dom';

import logo from '../images/logo.png';
import Profile from '../images/Profile.png';

const Header = () => {
    const navigate = useNavigate();

    const handleProfileClick = () => {
        console.log('Клик по профилю');
    };

    return (
        <header className="main-header">
            <img className='logo-main' src={logo} alt="BrainTube Logo" />
            <button 
                className="profile-button"
                onClick={handleProfileClick}
                aria-label="Профиль">
                <img src={Profile} alt="Профиль пользователя" />
            </button>
        </header>
    );
};

export default Header;