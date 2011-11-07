import pymysql
from decimal import *
tt = pymysql.connect("127.0.0.1","root","","testauction")

def runQuery(query, parameters):
	c = tt.cursor()
	c.execute(query, parameters)
	results = c.fetchall()
	tt.commit()
	c.close()
	return results


def userID(email):
	results = runQuery("select id from x_user where email = %s;", (email,))
	return results[0][0]

def availableNaira(email):
	results = runQuery("select availablenaira from x_user where email =%s;", (email,))
	if not results[0][0]:
		return 0
	else:
		return results[0][0]

def nairaBalance(email):
	results = runQuery("select nairabalance from x_user where email =%s;", (email,))
	if not results[0][0]:
		return 0
	else:
		return results[0][0]

def dollarBalance(email):
	results = runQuery("select dollarbalance from x_user where email =%s;", (email,))
	if not results[0][0]:
		return 0
	else:
		return results[0][0]

	
def createAuction(amount,close_date):
    c = tt.cursor()
    c.execute('''insert into x_auction (dollars,close_date) values (%s,%s);''',(amount,close_date))
    lid = c.lastrowid
    tt.commit()
    c.close()
    runQuery('''create event ev%s on schedule at %s do update x_auction set status = 1 where id = %s;''',(lid,close_date,lid))
    runQuery('''create event cb%s on schedule at %s + interval 1 minute do call checkbids(%s);''',(lid,close_date,lid))

def auctionstatus(id):
	results = runQuery("select status from x_auction where id = %s", (id,))
	return results[0][0]

def bid(email, id, amount, rate):
    nairabalance = Decimal(nairaBalance(email))
    if  (nairabalance >= amount*rate) and auctionstatus(id) == 0:
        runQuery("insert into x_bid (rate,dollars,status,auction_id,user_id) values (%s,%s,%s,%s,%s);",(rate,amount,0,id,userID(email)))




