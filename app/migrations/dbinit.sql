-- CREATE DATABASE jobportal;


CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  password VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(100),
  description TEXT,
  company VARCHAR(100),
  location VARCHAR(100),
  user_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT,
  user_id INT,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE jobs ADD COLUMN is_closed BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN role ENUM('applicant', 'employer') DEFAULT 'applicant';

ALTER TABLE users 
ADD COLUMN bio TEXT,
ADD COLUMN skills TEXT,
ADD COLUMN resume_url VARCHAR(255);

ALTER TABLE applications
ADD COLUMN status ENUM('applied', 'reviewed', 'shortlisted', 'rejected') DEFAULT 'applied';

ALTER TABLE applications
ADD COLUMN status ENUM('applied', 'reviewed', 'shortlisted', 'rejected') DEFAULT 'applied';

