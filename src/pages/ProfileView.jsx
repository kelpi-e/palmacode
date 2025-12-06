import Header from '../components/Header';
import NavComponents from '../components/NavComponents';

const ProfileView = () => {
    return (
        <div className="done-wrapper">
          <Header />
          <NavComponents />
          <div className="profile-section">
            <div className="profile-left">
                <h3 className='settings'>Настройки</h3>
                <button className='account'>Аккаунт</button>
                <button className='link'>Ссылка</button>
                <button className='exit'>Выход</button>
            </div>
            <div className="profile-right">
                <h3 className='static'>Общая статистика</h3>
                <div className="members-fill">
                    
                </div>
                <h1 className='link-true'>
                    https://disk.360.yandex.ru/i/Kn0yntXNxNZtEA
                </h1>
                <p className='update-src'>Обновить ссылку</p>
            </div>
          </div>
        </div>
    );
};

export default ProfileView;