CREATE DATABASE IF NOT EXISTS stockpredict
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE stockpredict;

CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(150) NOT NULL UNIQUE,
    password     VARCHAR(256) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;