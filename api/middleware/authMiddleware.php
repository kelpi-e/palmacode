<?php
class AuthMiddleware {
    private $authController;

    public function __construct($authController) {
        $this->authController = $authController;
    }

    public function checkAuth() {
        $headers = getallheaders();
        $token = isset($headers['Authorization']) ? str_replace('Bearer ', '', $headers['Authorization']) : null;

        if(!$token) {
            http_response_code(401);
            echo json_encode(['success' => false, 'message' => 'Токен не предоставлен']);
            exit;
        }

        $result = $this->authController->verifyToken($token);
        
        if(!$result['success']) {
            http_response_code(401);
            echo json_encode($result);
            exit;
        }

        return $result['user'];
    }
}
?>