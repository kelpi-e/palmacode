import { useNavigate } from 'react-router-dom'
import { useAuth } from '../api/useAuth'

const DoneView = () => {
  const navigate = useNavigate();
  const auth = useAuth();

  const handleLogout = () => {
    auth.removeToken();
    navigate('/authorization');
  };

  return (
    <div>
      <h1>Успешный вход!</h1>
      <button onClick={handleLogout} className="submit-button">
        Выйти
      </button>
    </div>
  );
};

export default DoneView;