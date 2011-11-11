import pymysql
from decimal import *
tt = pymysql.connect("127.0.0.1","root","","testauction")

def runQuery(query, parameters):
	c = tt.cursor()
	try:
	    c.execute(query, parameters)
	except:
	    raise
	results = c.fetchall()
	tt.commit()
	c.close()
	return results

#Consolidate user detail queries
def userDetails(email):
	results = runQuery("select id, availablenaira,nairabalance,dollarbalance,email from x_user where email =%s;", (email,))
	# Courtesy http://stackoverflow.com/questions/209840/map-two-lists-into-a-dictionary-in-python
	return dict(zip(["id", "availablenaira", "nairabalance", "dollarbalance", "email"],results[0]))

#Consolidate auction detail query
def auctionDetails(id):
    results = runQuery("select id, dollars, status, rate, creation_date, close_date, sold from x_auction where id =%s;", (id,))
    try:
        return dict(zip(["id","dollars","status","rate","creation_date","close_date","sold"],results[0]))
    except:
        return 0

def bidDetails(auction_id, email):
    results = runQuery('''select dollars, rate, bid_date, status from x_bid,x_user where x_bid = %s and x_user.email=%s''' % (auction_id,email))
	
def createAuction(amount,close_date):
    c = tt.cursor()
    c.execute('''insert into x_auction (dollars,close_date) values (%s,%s);''',(amount,close_date))
    lrid = c.lastrowid
    tt.commit()
    c.close()
    #This event closes the auction at close_date
    runQuery('''create event ev%s on schedule at %s do update x_auction set status = 1 where id = %s;''',(lrid,close_date,lrid))
    #The following event computes bid winners and updates their account balances 1 minute after the bid ends
    runQuery('''create event cb%s on schedule at %s + interval 1 minute do call checkbids(%s);''',(lrid,close_date,lrid))
    return 1

def bid(email, id, amount, rate):
    availablenaira = Decimal(userDetails(email)["availablenaira"])
    if not auctionDetails(id):
        return 0
    if  (availablenaira >= Decimal(amount)*Decimal(rate)) and auctionDetails(id)["status"] == 0:
        runQuery("insert into x_bid (rate,dollars,status,auction_id,user_id) values (%s,%s,%s,%s,%s);",(rate,amount,0,id,userDetails(email)["id"]))
        return 1
    else:
        return 0

def login(email,password):
	pp = runQuery('''select password from x_user where email=%s;''', (email,))
	try:
		if pp[0][0] == password:
			return 1
	except:
		pass
	else:
		return 0

def nairaReload(email,amount):
    runQuery('''update x_user set availablenaira=availablenaira+%s, nairabalance=nairabalance+%s where email=%s''', (amount,amount,email))

def createUser(firstname,lastname,email,password):
    '''return 0 if user creation fails because of Duplicate entry'''
    try:
        runQuery('''insert into x_user (firstname,lastname,email,password) values (%s,%s,%s,%s)''',(firstname,lastname,email,password))
    except:
        return 0
    return 1

def oldAuctions():
    results = runQuery('''select close_date, dollars, sold, rate, status, id from x_auction where status=2;''', ())
    rr = []
    for i in results:
        rr.append(dict(zip(["close_date", "dollars", "sold", "rate", "status", "id"], i)))
    return rr



    