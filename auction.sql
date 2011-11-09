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
	DECLARE done INT DEFAULT 0;
	DECLARE amount_available DECIMAL(60,4);
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
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
	
	OPEN bid_cur;
	SET amount_available = (SELECT dollars FROM testauction.x_auction where id = a_id);
	SET bought = 0;
	
	firstpass: LOOP
		FETCH bid_cur INTO id_var,rate_var,dollars_var,bid_date_var,status_var,auction_id_var,user_id_var;
		IF dollars_var >= amount_available THEN
			SET bought = amount_available;
		ELSE
			SET bought = dollars_var;
		END IF;
		SET winning_rate = rate_var;
		SET amount_available = amount_available - bought;
		IF amount_available = 0 THEN LEAVE firstpass;
		END IF;
		IF done THEN LEAVE firstpass;
		END IF;
	END LOOP firstpass;
	CLOSE bid_cur;
	

	SET done = 0;
	OPEN bid_cur;
	SET amount_available = (SELECT dollars FROM testauction.x_auction where id = a_id);
	SET bought = 0; 
	secondpass: LOOP
		FETCH bid_cur INTO id_var,rate_var,dollars_var,bid_date_var,status_var,auction_id_var,user_id_var;
		IF dollars_var >= amount_available THEN
			SET bought = amount_available;
			UPDATE x_user SET availablenaira = availablenaira + (dollars_var*rate_var) - (bought*winning_rate), nairabalance = nairabalance - (bought*winning_rate), dollarbalance=dollarbalance+bought where id = user_id_var;
			IF dollars_var = amount_available THEN
				UPDATE x_bid SET status = 1 where id=id_var;
			ELSE UPDATE x_bid SET status = 2 where id=id_var;
			END IF;
		ELSE
			SET bought = dollars_var;
			UPDATE x_user SET nairabalance = nairabalance - (bought*winning_rate), dollarbalance= dollarbalance+bought where id = user_id_var;
			UPDATE x_bid SET status = 1 where id=id_var;
		END IF;
		SET amount_available = amount_available - bought;
		IF amount_available = 0 THEN LEAVE secondpass;
		END IF;
		IF done THEN LEAVE secondpass;
		END IF;
	END LOOP secondpass;
	CLOSE bid_cur;
	
	UPDATE x_auction SET status=2, rate=winning_rate, sold=dollars-amount_available WHERE id = a_id;
END##



