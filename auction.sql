use testauction;

create table x_auction ( 
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
dollars DECIMAL (60,4) UNSIGNED NOT NULL, 
state TINYINT NOT NULL, 
rate DECIMAL (60,4) UNSIGNED,
creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
close_date TIMESTAMP NOT NULL) ENGINE=InnoDB;

create table x_user (
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
firstname VARCHAR(30) NOT NULL,
lastname VARCHAR(30) NOT NULL,
email VARCHAR(30) NOT NULL,
password VARCHAR(30) NOT NULL,
nairabalance DECIMAL (60,4) UNSIGNED,
dollarbalance DECIMAL (60,4) UNSIGNED,
availablenaira DECIMAL (60,4) UNSIGNED,
UNIQUE (email)
) ENGINE=InnoDB;

create table x_bid (
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
rate DECIMAL (60,4) NOT NULL,
dollars DECIMAL (60,4) UNSIGNED NOT NULL,
bid_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
state TINYINT NOT NULL,
auction_id INT NOT NULL,
user_id INT NOT NULL,
FOREIGN KEY (auction_id) REFERENCES x_auction(id),
FOREIGN KEY (user_id) REFERENCES x_user(id)) ENGINE=InnoDB;

create trigger onbid before insert on x_bid for each row update x_user set x_user.availablenaira = x_user.availablenaira - (NEW.rate*NEW.dollars) where x_user.id = NEW.user_id;


