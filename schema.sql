
CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

CREATE TABLE IF NOT EXISTS members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    joined_on DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS publishers (
    publisher_id INT AUTO_INCREMENT PRIMARY KEY,
    publisher_name VARCHAR(100) NOT NULL,
    city VARCHAR(60),
    email VARCHAR(100),
    phone VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(60) NOT NULL UNIQUE,
    description VARCHAR(255),
    shelf_location VARCHAR(30),
    created_on DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    CHECK (total_copies >= 0),
    CHECK (available_copies >= 0 AND available_copies <= total_copies)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    status ENUM('Issued', 'Returned') NOT NULL DEFAULT 'Issued',
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    CHECK (due_date >= issue_date)
);

INSERT IGNORE INTO members
(member_id, name, email, phone, joined_on) VALUES
(1, 'Aarav Sharma', 'aarav@example.com', '9876500001', '2026-01-05'),
(2, 'Diya Rao', 'diya@example.com', '9876500002', '2026-01-10'),
(3, 'Rohan Kumar', 'rohan@example.com', '9876500003', '2026-02-01'),
(4, 'Ananya Singh', 'ananya@example.com', '9876500004', '2026-02-12'),
(5, 'Kabir Patel', 'kabir@example.com', '9876500005', '2026-03-01');

INSERT IGNORE INTO publishers
(publisher_id, publisher_name, city, email, phone) VALUES
(1, 'Pearson', 'Delhi', 'pearson@example.com', '9811100001'),
(2, 'McGraw Hill', 'Mumbai', 'mcgraw@example.com', '9811100002'),
(3, 'Penguin', 'Bengaluru', 'penguin@example.com', '9811100003'),
(4, 'Oxford Press', 'Chennai', 'oxford@example.com', '9811100004'),
(5, 'Wiley', 'Hyderabad', 'wiley@example.com', '9811100005');

INSERT IGNORE INTO categories
(category_id, category_name, description, shelf_location, created_on) VALUES
(1, 'Technology', 'Computing and engineering', 'A1', '2026-01-01'),
(2, 'Science', 'Scientific books', 'A2', '2026-01-01'),
(3, 'Fiction', 'Fictional stories', 'B1', '2026-01-01'),
(4, 'Business', 'Management and business', 'B2', '2026-01-01'),
(5, 'Education', 'Learning and textbooks', 'C1', '2026-01-01');

INSERT IGNORE INTO books
(book_id, title, author, publisher_id, category_id,
 total_copies, available_copies, price) VALUES
(1, 'Python Programming', 'John Smith', 1, 1, 5, 5, 550.00),
(2, 'Database Systems', 'Rita Joseph', 2, 1, 5, 5, 650.00),
(3, 'Basic Science', 'Arun Das', 4, 2, 5, 5, 400.00),
(4, 'The Silent River', 'Meera Rao', 3, 3, 5, 5, 350.00),
(5, 'Business Essentials', 'Karan Mehta', 5, 4, 5, 5, 500.00);

DELIMITER //

CREATE TRIGGER before_loan_insert
BEFORE INSERT ON loans
FOR EACH ROW
BEGIN
    DECLARE copies_available INT;

    IF NEW.status = 'Issued' THEN
        SELECT available_copies INTO copies_available
        FROM books
        WHERE book_id = NEW.book_id;

        IF copies_available IS NULL OR copies_available < 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Book is not available';
        END IF;
    END IF;
END//

CREATE TRIGGER after_loan_insert
AFTER INSERT ON loans
FOR EACH ROW
BEGIN
    IF NEW.status = 'Issued' THEN
        UPDATE books
        SET available_copies = available_copies - 1
        WHERE book_id = NEW.book_id;
    END IF;
END//

CREATE TRIGGER after_loan_update
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    IF OLD.status = 'Issued' AND NEW.status = 'Returned' THEN
        UPDATE books
        SET available_copies = available_copies + 1
        WHERE book_id = NEW.book_id;
    END IF;
END//

DELIMITER ;

INSERT IGNORE INTO loans
(loan_id, member_id, book_id, issue_date, due_date, return_date, status)
VALUES
(1, 1, 1, '2026-09-01', '2026-09-15', NULL, 'Issued'),
(2, 2, 2, '2026-09-02', '2026-09-16', NULL, 'Issued'),
(3, 3, 3, '2026-09-03', '2026-09-17', '2026-09-10', 'Returned'),
(4, 4, 4, '2026-09-04', '2026-09-18', NULL, 'Issued'),
(5, 5, 5, '2026-09-05', '2026-09-19', '2026-09-12', 'Returned');

CREATE OR REPLACE VIEW book_details AS
SELECT
    b.book_id,
    b.title,
    b.author,
    p.publisher_name,
    c.category_name,
    b.total_copies,
    b.available_copies,
    b.price
FROM books b
JOIN publishers p ON b.publisher_id = p.publisher_id
JOIN categories c ON b.category_id = c.category_id;

CREATE OR REPLACE VIEW loan_details AS
SELECT
    l.loan_id,
    m.name AS member_name,
    b.title AS book_title,
    l.issue_date,
    l.due_date,
    l.return_date,
    l.status
FROM loans l
JOIN members m ON l.member_id = m.member_id
JOIN books b ON l.book_id = b.book_id;

-- Verify that the database contains the expected records.
SELECT * FROM members;
SELECT * FROM publishers;
SELECT * FROM categories;
SELECT * FROM books;
SELECT * FROM loans;
