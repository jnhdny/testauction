use testauction;

SET GLOBAL event_scheduler = ON;
SET @@global.event_scheduler = ON;
SET GLOBAL event_scheduler = 1;
SET @@global.event_scheduler = 1;

create table x_auction ( 
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
dollars DECIMAL (60,4) UNSIGNED NOT NULL, 
status TINYINT NOT NULL, 
rate DECIMAL (60,4) UNSIGNED,
creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
close_date TIMESTAMP NOT NULL,
sold DECIMAL (60,4) UNSIGNED) ENGINE=InnoDB;

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
status TINYINT NOT NULL,
auction_id INT NOT NULL,
user_id INT NOT NULL,
FOREIGN KEY (auction_id) REFERENCES x_auction(id),
FOREIGN KEY (user_id) REFERENCES x_user(id)) ENGINE=InnoDB;

CREATE TRIGGER onbid 
BEFORE INSERT ON x_bid 
FOR EACH ROW
UPDATE x_user SET x_user.availablenaira = x_user.availablenaira - (NEW.rate*NEW.dollars) WHERE x_user.id = NEW.user_id;

DROP PROCEDURE IF EXISTS checkbids;
DELIMITER ##
CREATE PROCEDURE checkbids(IN a_id INT)
BEGIN

	DECLARE ctr INT;
	DECLARE var1 DECIMAL(60,4);
	DECLARE bought DECIMAL(60,4);
	DECLARE winning_rate DECIMAL(60,4);
	DECLARE id_var INT(11);
	DECLARE rate_var DECIMAL(60,4);
	DECLARE dollars_var DECIMAL(60,4); 
	DECLARE bid_date_var TIMESTAMP;
	DECLARE status_var TINYINT(4);
	DECLARE auction_id_var INT(11);
	DECLARE user_id_var INT(11);
	DECLARE bid_cur CURSOR FOR SELECT * FROM testauction.x_bid WHERE auction_id = a_id ORDER BY rate DESC, bid_date;
	OPEN bid_cur;
	SET ctr = 0;
	SET var1 = 0;
	SET bought = 0;
	label1: LOOP
		FETCH bid_cur INTO id_var,rate_var,dollars_var,bid_date_var,status_var,auction_id_var,user_id_var;
		-- first record sets the winning rate
		IF ctr = 0 THEN
			SET winning_rate = rate_var;
			SET var1 = (SELECT dollars FROM testauction.x_auction where id = a_id);
		END IF;
		IF dollars_var >= var1 THEN
			SET bought = var1;
			UPDATE x_user SET availablenaira = availablenaira + (dollars_var*rate_var) - (bought*winning_rate), nairabalance = nairabalance - (bought*winning_rate), dollarbalance=dollarbalance+bought where id = user_id_var;
			IF dollars_var = var1 THEN
				UPDATE x_bid SET status = 1 where id=id_var;
			ELSE UPDATE x_bid SET status = 2 where id=id_var;
			END IF;
		ELSE
			SET bought = dollars_var;
			UPDATE x_user SET nairabalance = nairabalance - (bought*winning_rate), dollarbalance= dollarbalance+bought where id = user_id_var;
			UPDATE x_bid SET status = 1 where id=id_var;
		END IF;
		SET var1 = var1 - bought;
		SET ctr = ctr+1;
		IF var1 = 0 THEN LEAVE label1;
		END IF;
	END LOOP label1;
	CLOSE bid_cur;
	UPDATE x_auction SET status=2, rate=winning_rate, sold=dollars-var1 WHERE id = a_id;
END##



