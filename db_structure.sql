-- Terminal-chat database structure for well app working.

CREATE DATABASE chat; -- Tworzenie bazy danych

USE chat; -- Wybór utworzonej bazy danych

-- Tworzenie tabeli użytkowników
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_online INT,
    unregistered INT
);

-- Tworzenie tabeli czatów
CREATE TABLE chats (
    chat_id INT PRIMARY KEY AUTO_INCREMENT,
    chat_name VARCHAR(255) NOT NULL,
    created_by INT NOT NULL
);

-- Tworzenie tabeli połączeniowej użytkowników i czatów
CREATE TABLE chats_users (
    chat_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (chat_id, user_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Tworzenie tabeli wiadomości
CREATE TABLE messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    chat_id INT,
    sender_id INT,
    content VARCHAR(255) NOT NULL,
    timestamp DATETIME,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
);