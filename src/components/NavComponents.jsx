import { useNavigate } from 'react-router-dom';

import Menu from '../images/Menu.png';
import Bluetooh from '../images/Bluetooh.png';
import Z from '../images/Z.png';
import Camera from '../images/Camera.png';

const NavComponents = () => {
    const navigate = useNavigate();

    const handleButtonClick = (action) => {
        console.log(`Клик по кнопке: ${action}`)
    };

    return (
        <nav className="nav-sidebar">
            <div className="nav-column">
                <button 
                    className="nav-button"
                    onClick={() => handleButtonClick('menu')}
                    aria-label="Меню">
                    <img src={Menu} alt="Меню" className="nav-icon" />
                </button>
                <button 
                    className="nav-button"
                    onClick={() => handleButtonClick('bluetooth')}
                    aria-label="Bluetooth">
                    <img src={Bluetooh} alt="Bluetooth" className="nav-icon" />
                </button>
                <button 
                    className="nav-button"
                    onClick={() => handleButtonClick('search')}
                    aria-label="Поиск">
                    <img src={Z} alt="Поиск" className="nav-icon" />
                </button>
                <button 
                    className="nav-button"
                    onClick={() => handleButtonClick('camera')}
                    aria-label="Камера">
                    <img src={Camera} alt="Камера" className="nav-icon" />
                </button>
            </div>
        </nav>
    );
};

export default NavComponents;