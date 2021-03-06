USE testauction;

SET GLOBAL event_scheduler = ON;
SET @@global.event_scheduler = ON;
SET GLOBAL event_scheduler = 1;
SET @@global.event_scheduler = 1;

DROP TRIGGER IF EXISTS onbid;
DROP TRIGGER IF EXISTS oncreateauction;
DROP TABLE IF EXISTS x_bid;
DROP TABLE IF EXISTS x_auction;
DROP TABLE IF EXISTS x_user;

create table x_auction ( 
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
dollars DECIMAL (60,4) UNSIGNED NOT NULL DEFAULT 0, 
status TINYINT NOT NULL, 
rate DECIMAL (60,4) UNSIGNED DEFAULT 0,
creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
close_date TIMESTAMP NOT NULL,
sold DECIMAL (60,4) UNSIGNED DEFAULT 0) ENGINE=InnoDB;

create table x_user (
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
firstname VARCHAR(30) NOT NULL,
lastname VARCHAR(30) NOT NULL,
email VARCHAR(30) NOT NULL,
password VARCHAR(128) NOT NULL,
salt VARCHAR(12) NOT NULL,
nairabalance DECIMAL (60,4) UNSIGNED DEFAULT 0,
dollarbalance DECIMAL (60,4) UNSIGNED DEFAULT 0,
availablenaira DECIMAL (60,4) UNSIGNED DEFAULT 0,
isvalid TINYINT NOT NULL DEFAULT 0,
validcode VARCHAR(7),
validexpiry TIMESTAMP,
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

CREATE TRIGGER oncreateauction
BEFORE INSERT ON x_auction
FOR EACH ROW
UPDATE x_user SET x_user.dollarbalance = x_user.dollarbalance - (NEW.dollars) WHERE x_user.email = "cbngov@cbn.gov";

INSERT INTO x_user (firstname,lastname,email,password,salt,validcode, isvalid) 
VALUES ("CBN", "Gov", "cbngov@cbn.gov", "ed3a79b126c42ad128e43dc97ee1a0e6f68ed933f3d027e164f1fe72711a93423b801d64ff8a3936a12fff88233530e1684088bd31d51150646201713fc37c41","6W3IL0RBXHDU","DWCZIAE",1);

DROP PROCEDURE IF EXISTS checkbids;
DELIMITER ##
CREATE PROCEDURE checkbids(IN a_id INT)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE cbnmail VARCHAR(30);
    DECLARE amount_available DECIMAL(60,4);
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
    SET winning_rate=0;
    SET cbnmail = "cbngov@cbn.gov";
    
    firstpass: LOOP
        FETCH bid_cur INTO id_var,rate_var,dollars_var,bid_date_var,status_var,auction_id_var,user_id_var;
        IF done THEN LEAVE firstpass;
        END IF;
        IF dollars_var > amount_available THEN LEAVE firstpass;
        ELSE
            SET winning_rate = rate_var;
            SET amount_available = amount_available - dollars_var;
        END IF;
        IF done THEN LEAVE firstpass;
        END IF;
    END LOOP firstpass;
    CLOSE bid_cur;

    SET done = 0;
    OPEN bid_cur;
    SET amount_available = (SELECT dollars FROM testauction.x_auction where id = a_id); 
    secondpass: LOOP
        FETCH bid_cur INTO id_var,rate_var,dollars_var,bid_date_var,status_var,auction_id_var,user_id_var;
        IF done THEN LEAVE secondpass;
        END iF;
        IF rate_var >= winning_rate THEN
            SET amount_available = amount_available - dollars_var;
            IF amount_available >= 0 THEN
                UPDATE x_user SET availablenaira = availablenaira + (dollars_var*rate_var) - (dollars_var*winning_rate), nairabalance = nairabalance - (dollars_var*winning_rate), dollarbalance=dollarbalance+dollars_var where id = user_id_var;
                UPDATE x_user SET nairabalance = nairabalance + (dollars_var*winning_rate) where email=cbnmail;
                UPDATE x_bid SET status = 1 where id=id_var;
                ITERATE secondpass;
            ELSE
                UPDATE x_user SET availablenaira = availablenaira + (dollars_var*rate_var) where id = user_id_var;
                UPDATE x_bid SET status = 2 where id=id_var;
                ITERATE secondpass;
            END IF;
        ELSE
            UPDATE x_user SET availablenaira = availablenaira + (dollars_var*rate_var) where id = user_id_var;
            UPDATE x_bid SET status = 2 where id=id_var;
            ITERATE secondpass;
        END IF;            
        IF done THEN LEAVE secondpass;
        END iF;
    END LOOP secondpass;
    CLOSE bid_cur;
    
    UPDATE x_auction SET status=2, rate=winning_rate, sold=dollars-amount_available WHERE id = a_id;
    UPDATE x_user SET dollarbalance=dollarbalance+amount_available WHERE email=cbnmail;
END##



