<?php
$allowed_origins = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173', 
    'http://127.0.0.1:3000'
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins))
    header("Access-Control-Allow-Origin: $origin");
else
    header("Access-Control-Allow-Origin: http://localhost:3000");

header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT");
header("Access-Control-Max-Age: 3600");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With, Origin, Accept");
header("Access-Control-Allow-Credentials: true");

if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    header("HTTP/1.1 200 OK");
    exit(0);
}

error_reporting(E_ALL);
ini_set('display_errors', 1);

error_log("Текущая директория: " . __DIR__);

include_once __DIR__ . '/config/database.php';
include_once __DIR__ . '/models/User.php';
include_once __DIR__ . '/controllers/AuthController.php';
include_once __DIR__ . '/middleware/AuthMiddleware.php';

try 
{
    $database = new Database();
    $db = $database->getConnection();
    
    if (!$db)
        throw new Exception("Не удалось подключиться к базе данных");

    $authController = new AuthController($db);
    $authMiddleware = new AuthMiddleware($authController);

    $method = $_SERVER['REQUEST_METHOD'];
    $input = json_decode(file_get_contents("php://input"), true);
    
    error_log("Запрос: " . $method . " " . $_SERVER['REQUEST_URI']);

    if(isset($_GET['action'])) 
    {
        $action = $_GET['action'];
        error_log("Действие: " . $action);
        
        switch($action) 
        {
            case 'register':
                if ($method === 'POST')
                    $result = $authController->register($input);
                else
                    $result = ['success' => false, 'message' => 'Метод не поддерживается для регистрации'];
                break;
                
            case 'login':
                if ($method === 'POST')
                    $result = $authController->login($input);
                else
                    $result = ['success' => false, 'message' => 'Метод не поддерживается для входа'];
                break;
                
            case 'verify':
                if ($method === 'POST')
                    $result = $authController->verifyToken($input['token'] ?? '');
                else
                    $result = ['success' => false, 'message' => 'Метод не поддерживается для проверки токена'];
                break;
            default:
                $result = ['success' => false, 'message' => 'Неизвестное действие: ' . $action];
        }
    } 
    else
        $result = ['success' => false, 'message' => 'Действие не указано'];

    http_response_code($result['success'] ? 200 : 400);
    echo json_encode($result);

} 
catch(Exception $e) 
{
    error_log("Ошибка API: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => 'Внутренняя ошибка сервера: ' . $e->getMessage()]);
}
?>