CREATE DATABASE IF NOT EXISTS teste
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE teste;

CREATE TABLE IF NOT EXISTS tbl_user (
  user_id BIGINT NOT NULL AUTO_INCREMENT,
  user_name VARCHAR(45) NULL,
  user_username VARCHAR(45) NULL,
  user_password VARCHAR(45) NULL,
  gender ENUM('M','F','O') NOT NULL DEFAULT 'O',
  birth_date DATE NULL,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_user_username (user_username)
);

DELIMITER //

DROP PROCEDURE IF EXISTS sp_createUser//

CREATE PROCEDURE sp_createUser(
  IN p_name VARCHAR(20),
  IN p_username VARCHAR(20),
  IN p_password VARCHAR(20),
  IN p_gender ENUM('M','F','O'),
  IN p_birth_date DATE
)
BEGIN
  IF EXISTS (SELECT 1 FROM tbl_user WHERE user_username = p_username) THEN
    SELECT 'Username Exists !!' AS message;
  ELSE
    INSERT INTO tbl_user (
      user_name,
      user_username,
      user_password,
      gender,
      birth_date
    )
    VALUES (
      p_name,
      p_username,
      p_password,
      IFNULL(p_gender,'O'),
      p_birth_date
    );

    SELECT 'User Created' AS message;
  END IF;
END//

DELIMITER ;
