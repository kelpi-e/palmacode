<?php
class AuthController
{
    private $user;
    private $secret_key = "your-secret-key-here";

    public function __construct($db)
    {
        $this->user = new User($db);
        $this->user->createTable();
    }
    public function generateToken($user_id, $email)
    {
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $payload = json_encode(['user_id' => $user_id, 'email' => $email, 'exp' => time() + (60 * 60 * 24)]);

        $base64UrlHeader = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($header));
        $base64UrlPayload = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($payload));

        $signature = hash_hmac('sha256', $base64UrlHeader . "." . $base64UrlPayload, $this->secret_key, true);
        $base64UrlSignature = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($signature));

        return $base64UrlHeader . "." . $base64UrlPayload . "." . $base64UrlSignature;
    }
    public function validateToken($token)
    {
        $parts = explode('.', $token);
        if (count($parts) != 3)
            return false;

        $signature = hash_hmac('sha256', $parts[0] . "." . $parts[1], $this->secret_key, true);
        $base64UrlSignature = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($signature));

        if ($base64UrlSignature !== $parts[2])
            return false;

        $payload = json_decode(base64_decode($parts[1]), true);
        
        if(isset($payload['exp']) && $payload['exp'] < time()) 
            return false;

        return $payload;
    }
    public function register($data)
    {
        if(empty($data['first_name']) || empty($data['last_name']) || empty($data['email']) || empty($data['password']) || empty($data['birth_date']) || empty($data['country']))
            return ['success' => false, 'message' => 'Все поля обязательны для заполнения'];
        if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL))
            return ['success' => false, 'message' => 'Некорректный email'];
        if(strlen($data['password']) < 6)
            return ['success' => false, 'message' => 'Пароль должен содержать минимум 6 символов'];
        if($data['password'] !== $data['confirm_password'])
            return ['success' => false, 'message' => 'Пароли не совпадают'];
        $this->user->email = $data['email'];
        if($this->user->emailExists())
            return ['success' => false, 'message' => 'Пользователь с таким email уже существует'];

        $this->user->first_name = $data['first_name'];
        $this->user->last_name = $data['last_name'];
        $this->user->birth_date = $data['birth_date'];
        $this->user->country = $data['country'];
        $this->user->email = $data['email'];
        $this->user->password = $data['password'];

        if($this->user->register()) 
        {
            $token = $this->generateToken($this->user->id, $data['email']);
            return [
                'success' => true, 
                'message' => 'Регистрация успешна',
                'token' => $token,
                'user' => [
                    'id' => $this->user->id,
                    'first_name' => $this->user->first_name,
                    'last_name' => $this->user->last_name,
                    'email' => $this->user->email
                ]
            ];
        }

        return ['success' => false, 'message' => 'Ошибка при регистрации'];
    }
    public function login($data) 
    {
        if(empty($data['email']) || empty($data['password']))
            return ['success' => false, 'message' => 'Email и пароль обязательны'];

        $user = $this->user->login($data['email'], $data['password']);
        
        if($user) 
        {
            $token = $this->generateToken($user['id'], $data['email']);
            return [
                'success' => true,
                'message' => 'Авторизация успешна',
                'token' => $token,
                'user' => $user
            ];
        }

        return ['success' => false, 'message' => 'Неверный email или пароль'];
    }
    public function verifyToken($token) 
    {
        $payload = $this->validateToken($token);
        
        if($payload) 
        {
            $user = $this->user->getById($payload['user_id']);
            if($user)
                return ['success' => true, 'user' => $user];
        }
        
        return ['success' => false, 'message' => 'Недействительный токен'];
    }
    public function getProfile($token) 
    {
        $result = $this->verifyToken($token);
        
        if($result['success'])
            return $result;
        
        return ['success' => false, 'message' => 'Доступ запрещен'];
    }
}
?>