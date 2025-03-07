CREATE TABLE lms_books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(13) UNIQUE NOT NULL,
    total_copies INTEGER NOT NULL,
    available_copies INTEGER NOT null
);

-- select * from lms_books;
CREATE TABLE lms_members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email varchar(255) not null,
    password varchar(1000) not null
);

-- insert into lms_members (name, email, "password") values ('admin', 'adminlms@gmail.com', '@dmin');
-- select * from lms_members;
-- delete from lms_members where id=2;
CREATE TABLE lms_book_issue (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES lms_books(id),
    member_id INTEGER REFERENCES lms_members(id),
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_date TIMESTAMP,
    is_returned BOOLEAN DEFAULT FALSE
);

-- drop table lms_book_issue;
-- select * from lms_book_issue;
-- -- Create tables for the library management system
-- CREATE TABLE books (
--     id SERIAL PRIMARY KEY,
--     title VARCHAR(255) NOT NULL,
--     author VARCHAR(255) NOT NULL,
--     isbn VARCHAR(13) UNIQUE NOT NULL,
--     total_copies INTEGER NOT NULL,
--     available_copies INTEGER NOT NULL
-- );
-- CREATE TABLE members (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     member_id VARCHAR(50) UNIQUE NOT NULL
-- );
-- CREATE TABLE issue (
--     id SERIAL PRIMARY KEY,
--     book_id INTEGER REFERENCES books(id),
--     member_id INTEGER REFERENCES members(id),
--     issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     return_date TIMESTAMP,
--     is_returned BOOLEAN DEFAULT FALSE
-- );
-- create table lms_admin(
--     id serial primary key,
--     name VARCHAR(255) NOT NULL,
--     email varchar(255) not null,
--     password varchar(1000) not null
-- );
-- drop table lms_admin;
-- select * from lms_admin;