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

#Consolidate user detail queries
def userDetails(email):
	results = runQuery("select id, availablenaira,nairabalance,dollarbalance from x_user where email =%s;", (email,))
	rr = {}
	rr["id"] = results[0][0]
	rr["availablenaira"] = results[0][1]
	rr["nairabalance"] = results[0][2]
	rr["dollarbalance"] = results[0][3]
	return rr

	
def createAuction(amount,close_date):
    c = tt.cursor()
    c.execute('''insert into x_auction (dollars,close_date) values (%s,%s);''',(amount,close_date))
    lrid = c.lastrowid
    tt.commit()
    c.close()
    runQuery('''create event ev%s on schedule at %s do update x_auction set status = 1 where id = %s;''',(lrid,close_date,lrid))
    runQuery('''create event cb%s on schedule at %s + interval 1 minute do call checkbids(%s);''',(lrid,close_date,lrid))

def auctionstatus(id):
	results = runQuery("select status from x_auction where id = %s", (id,))
	return results[0][0]

def bid(email, id, amount, rate):
    nairabalance = Decimal(nairaBalance(email))
    if  (nairabalance >= amount*rate) and auctionstatus(id) == 0:
        runQuery("insert into x_bid (rate,dollars,status,auction_id,user_id) values (%s,%s,%s,%s,%s);",(rate,amount,0,id,userDetails(email)["id"]))



