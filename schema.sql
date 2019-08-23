CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    first_name VARCHAR(255),
	  last_name VARCHAR(255),
    email varchar(255) UNIQUE,
    date_birth DATE,
	  profile_pic LONGBLOB,
	  bio VARCHAR(255),
	  gender ENUM('Female', 'Male', 'Secret'),
	  password VARCHAR (255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);


CREATE TABLE Friends (
	  user_id INT4 NOT NULL,
	  friend_id INT4 NOT NULL,
  CONSTRAINT users_fk FOREIGN KEY (user_id) REFERENCES Users(user_id),
  CONSTRAINT friends_fk FOREIGN KEY (friend_id) REFERENCES Users(user_id)
);

CREATE TABLE Albums (
  	album_id INT4 AUTO_INCREMENT,
  	title VARCHAR(255),
  	date_creation DATE,
    user_id INT4 NOT NULL,
  CONSTRAINT albums_pk PRIMARY KEY (album_id),
  CONSTRAINT albums_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Photos (
    photo_id INT4 AUTO_INCREMENT,
    caption VARCHAR(255),
	  data LONGBLOB,
    user_id INT4 NOT NULL,
    album_id INT4 NOT NULL,
  CONSTRAINT photos_pk PRIMARY KEY (photo_id),
  CONSTRAINT photos_fk FOREIGN KEY (user_id) REFERENCES Users(user_id),
  CONSTRAINT photos_fk2 FOREIGN KEY (album_id) REFERENCES Albums(album_id)
);

CREATE TABLE Tagged_Photos (
  	word VARCHAR(50),
  	photo_id INT4 NOT NULL,
  CONSTRAINT tagged_fk FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
);

CREATE TABLE Comments (
  	comment_id INT4 AUTO_INCREMENT,
    text VARCHAR(300),
  	writer_id INT4 NOT NULL,
  	date_left DATE,
  	photo_id INT4 NOT NULL,
  CONSTRAINT comments_pk PRIMARY KEY (comment_id),
  CONSTRAINT comments_fk FOREIGN KEY (writer_id) REFERENCES Users(user_id),
  CONSTRAINT comments_fk2 FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
);

CREATE TABLE Likes (
  	user_id INT4,
  	photo_id INT4,
  CONSTRAINT likes_fk FOREIGN KEY (user_id) REFERENCES Users(user_id),
  CONSTRAINT likes_fk2 FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
);

INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
INSERT INTO Users (user_id, first_name, last_name, email) VALUES (-1, 'Guest', '', 'anonymous@anonymous');
