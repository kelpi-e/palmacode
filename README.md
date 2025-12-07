# BrainTube - Frontend Application

Frontend приложение для анализа видео с полной интеграцией FastAPI бэкенда.

## API Интеграция

Проект полностью интегрирован с FastAPI бэкендом через централизованный API клиент.

### Структура API

- **Конфигурация**: `src/api/config.js` - настройки API (базовый URL)
- **API Клиент**: `src/api/client.js` - централизованный клиент для всех API запросов
- **Аутентификация**: `src/api/useAuth.js` - хук для управления токенами

### Настройка API URL

Создайте файл `.env` в корне проекта:

```
REACT_APP_API_URL=http://localhost:8000
```

Или используйте значение по умолчанию (http://localhost:8000).

### Настройка CORS на бэкенде

Для работы фронтенда с бэкендом необходимо настроить CORS на FastAPI сервере. Добавьте в ваш FastAPI приложение:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # URL вашего React приложения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Это позволит браузеру отправлять запросы к API и обрабатывать preflight (OPTIONS) запросы.

### Реализованные эндпоинты

#### Аутентификация
- `POST /auth/register` - Регистрация пользователя
- `POST /auth/login` - Вход в систему

#### Пользователи
- `GET /users/` - Получить всех пользователей
- `GET /users/me` - Получить текущего пользователя
- `GET /users/{user_id}` - Получить пользователя по ID
- `PUT /users/{user_id}` - Обновить пользователя
- `DELETE /users/{user_id}` - Удалить пользователя

#### Видео
- `GET /video/` - Получить все видео пользователя
- `POST /video/` - Создать новое видео (загрузка файла)
- `GET /video/{video_id}` - Получить видео по ID
- `PUT /video/{video_id}` - Обновить видео
- `DELETE /video/{video_id}` - Удалить видео
- `GET /video/file/{video_id}` - Скачать файл видео

#### Админ-пользователи
- `POST /adminuser/invitation` - Создать пригласительный код
- `POST /adminuser/join` - Присоединиться к админу
- `GET /adminuser/my-admins` - Получить моих админов
- `GET /adminuser/my-users` - Получить моих пользователей
- `DELETE /adminuser/{user_id}` - Отвязать пользователя
- `DELETE /adminuser/leave/{admin_id}` - Отвязаться от админа

### Защита маршрутов

Защищенные маршруты обернуты в компонент `ProtectedRoute`, который автоматически перенаправляет неавторизованных пользователей на страницу входа.

Защищенные страницы:
- `/done` - Главная страница с видео
- `/profile` - Профиль пользователя
- `/analyse-video` - Анализ видео
- `/analyse-human` - Анализ человека

### Использование API клиента

```javascript
import apiClient from './api/client';

// Регистрация
const user = await apiClient.register(email, password, role);

// Вход
const tokenData = await apiClient.login(email, password);

// Загрузка видео
const video = await apiClient.createVideo(file, name);

// Получить все видео
const videos = await apiClient.getAllVideos();

// Получить текущего пользователя
const currentUser = await apiClient.getCurrentUser();
```

### Обработка ошибок

API клиент автоматически обрабатывает:
- Сетевые ошибки
- Ошибки авторизации (401) - автоматический logout
- Ошибки валидации (422)
- Таймауты запросов

## Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
