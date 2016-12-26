CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE User CASCADE;


CREATE TABLE User(
	id int NOT NULL AUTO_INCREMENT,
	first_name varchar (30) NOT NULL,
	last_name varchar (30) NOT NULL,
	email varchar(30) NOT NULL UNIQUE,
	dob char(15) NOT NULL,
	hometown varchar(70),
	gender char(10),
	password varchar(20) NOT NULL,
	contributions int DEFAULT 0,
	PRIMARY KEY (id)
);



/*
A user can have 0 or more friends. If a user with id = 1 friends a user 
with id = 2, then the following tuple will be inserted: (1,2) 
Each id  must reference the an id in the User table. 
If either user in a friendship is deleted, delete the friendship.

*/

CREATE TABLE Has_Friends(
	id1 int NOT NULL,
	id2 int NOT NULL,
	FOREIGN KEY (id1) REFERENCES User(id)
		ON DELETE CASCADE,
	FOREIGN KEY (id2) REFERENCES User(id)
		ON DELETE CASCADE
);

/*
An album must have a name and must be associated with a owner. 
owner_id is a foreign key that references id in User, and owner_id can't be null.
If the owner is deleted, delete the album. 
An album can have 0 or more photos.
*/


CREATE TABLE Album(
	album_id int NOT NULL AUTO_INCREMENT,
	date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	name varchar(30) NOT NULL,
	owner_id int NOT NULL,
	PRIMARY KEY (album_id),
	FOREIGN KEY (owner_id) REFERENCES User(id)
		ON DELETE CASCADE
);


/*
Every photo must have an album. 
album_id is a foreign key that references id in album, and album_id can't be null.
If the photo's album is deleted, delete the photo as well.
*/

CREATE TABLE Photo(
	id int NOT NULL AUTO_INCREMENT,
	user_id int NOT NULL,
	album_id int NOT NULL,
	caption varchar(255),
	imgdata longblob NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (album_id) REFERENCES Album(album_id) ON DELETE CASCADE
);


/*
Every tag must have text, but a tag can exist once the associated photo is deleted.
photo_id references id in Photo, but this field is optional since tags can exist without photos
*/
CREATE TABLE Tag( 
	text varchar(20) NOT NULL,
	photo_id int,
	FOREIGN KEY (photo_id) REFERENCES Photo(id) ON DELETE CASCADE
);


/*
Every comment is associated with a photo. A comment can only be placed after
the picture is uploaded. Delete the comment if the commenter or photo is deleted.

owner_id (not null) is a foreign key referencing id in User
photo_id (not null) is a foreign key referencing id in Photo

*/

CREATE TABLE Comment(
	id int NOT NULL AUTO_INCREMENT,
	text varchar(200) NOT NULL,
	owner_id int,
	photo_id int NOT NULL,
	date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (owner_id) REFERENCES User(id)
		ON DELETE CASCADE,
	FOREIGN KEY (photo_id) REFERENCES Photo(id)
		 ON DELETE CASCADE,
	PRIMARY KEY (id)
);

/*
Every like needs a photo, but doesn't have to be associated with a person. If either is deleted, delete the like

photo_id  is a foreign key referencing id in photo
user_id  is a foreign key referencing id in user
*/

CREATE TABLE Likes(
	photo_id int NOT NULL,
	user_id int,
	FOREIGN KEY (photo_id) REFERENCES Photo(id) 
		ON DELETE CASCADE,
	FOREIGN KEY (user_id) REFERENCES User(id)
	    ON DELETE CASCADE
);





#INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
#INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
