<?php
class User
{
    private $conn;
    private $table_name = "users";
    public $id;
    public $first_name;
    public $last_name;
    public $birth_date;
    public $country;
    public $email;
    public $password;
    public $created_at;

    public function __construct($db)
    {
        $this->conn = $db;
    }
    public function createTable() 
    {
        $query = "CREATE TABLE IF NOT EXISTS " . $this->table_name . " (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            birth_date DATE NOT NULL,
            country VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )";

        $stmt = $this->conn->prepare($query);
        return $stmt->execute();
    }
    public function register()
    {
        $query = "INSERT INTO " . $this->table_name . " 
                  SET first_name=:first_name, last_name=:last_name, 
                      birth_date=:birth_date, country=:country, 
                      email=:email, password=:password";

        $stmt = $this->conn->prepare($query);

        $this->first_name = htmlspecialchars((strip_tags($this->first_name)));
        $this->last_name = htmlspecialchars((strip_tags($this->last_name)));
        $this->birth_date = htmlspecialchars(strip_tags($this->birth_date));
        $this->country = htmlspecialchars(strip_tags($this->country));
        $this->email = htmlspecialchars(strip_tags($this->email));

        $this->password = password_hash($this->password, PASSWORD_DEFAULT);

        $stmt->bindParam(":first_name", $this->first_name);
        $stmt->bindParam(":last_name", $this->last_name);
        $stmt->bindParam(":birth_date", $this->birth_date);
        $stmt->bindParam(":country", $this->country);
        $stmt->bindParam(":email", $this->email);
        $stmt->bindParam(":password", $this->password);

        if($stmt->execute()) 
        {
            $this->id = $this->conn->lastInsertId();
            return true;
        }
        return false;
    }
    public function emailExists()
    {
        $query = "SELECT id, first_name, last_name, password 
                  FROM " . $this->table_name . " 
                  WHERE email = ? 
                  LIMIT 0,1";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(1, $this->email);
        $stmt->execute();

        if ($stmt->rowCount() > 0)
        {
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            $this->id = $row['id'];
            $this->first_name = $row['first_name'];
            $this->last_name = $row['last_name'];
            $this->password = $row['password'];
            return true;
        }
        return false;
    }
    public function login($email, $password)
    {
        $this->email = $email;

        if ($this->emailExists() && password_verify($password, $this->password)) 
        {
            return [
                'id' => $this->id,
                'first_name' => $this->first_name,
                'last_name' => $this->last_name,
                'email' => $email
            ];
        }
        return false;
    }
    public function getById($id)
    {
        $query = "SELECT id, first_name, last_name, email, birth_date, country, created_at 
                  FROM " . $this->table_name . " 
                  WHERE id = ? 
                  LIMIT 0,1";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(1, $id);
        $stmt->execute();

        if($stmt->rowCount() > 0)
            return $stmt->fetch(PDO::FETCH_ASSOC);
        return false;
    }
}
?>