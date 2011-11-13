import pymysql, random, string, datetime,hashlib
from decimal import *
import smtplib
from email.mime.text import MIMEText
tt = pymysql.connect("127.0.0.1","root","","testauction")
CBN_ACCOUNT = "cbngov@cbn.gov"
WEB_ADDRESS = "127.0.0.1:8080"


# Ignacio's random string generator from
# http://stackoverflow.com/questions/2257441/python-random-string-generation-with-upper-case-letters-and-digits
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

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

def userDetails(email):
	results = runQuery("select id, availablenaira,nairabalance,dollarbalance,email from x_user where email =%s;", (email,))
	# Courtesy http://stackoverflow.com/questions/209840/map-two-lists-into-a-dictionary-in-python
	return dict(zip(["id", "availablenaira", "nairabalance", "dollarbalance", "email"],results[0]))

def auctionDetails(id):
    results = runQuery("select id, dollars, status, rate, creation_date, close_date, sold from x_auction where id =%s;", (id,))
    try:
        return dict(zip(["id","dollars","status","rate","creation_date","close_date","sold"],results[0]))
    except:
        return 0

def bidDetails(auction_id, email):
    results = runQuery('''select dollars, rate, bid_date, status from x_bid,x_user where auction_id = %s and x_user.email=%s''', (auction_id,email))
    return results
	
def createAuction(amount,close_date):
    #Check if there is enough money in CBN account and then create an auction
    dav = runQuery('''select dollarbalance from x_user where email=%s''',(CBN_ACCOUNT))[0][0]
    if Decimal(amount) <= dav:
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
    else:
        return 0

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
	pp = runQuery('''select password,isvalid,salt from x_user where email=%s;''', (email,))
	hexhash = hashlib.sha512((password+pp[0][2]).encode("utf-8")).hexdigest()
	try:
		if hexhash == pp[0][0]:
			if pp[0][1] == 1:
				return 1
			if pp[0][1] == 0:
				return 2
	except:
		raise
	else:
		return 0

def nairaReload(email,amount):
    runQuery('''update x_user set availablenaira=availablenaira+%s, nairabalance=nairabalance+%s where email=%s''', (amount,amount,email))

def dollarReload(email,amount):
    runQuery('''update x_user set dollarbalance=dollarbalance+%s where email=%s''', (amount,email))

def nairaRemove(email,amount):
    runQuery('''update x_user set availablenaira=availablenaira-%s, nairabalance=nairabalance-%s where email=%s''', (amount,amount,email))

def dollarRemove(email,amount):
    runQuery('''update x_user set dollarbalance=dollarbalance-%s where email=%s''', (amount,email))

def createUser(firstname,lastname,email,password):
    '''return 0 if user creation fails because of Duplicate entry'''
    vcode = id_generator(7)
    salt = id_generator(12)
    hexhash = hashlib.sha512((password+salt).encode("utf-8")).hexdigest()
    try:
        runQuery('''insert into x_user (firstname,lastname,email,password,salt,validcode,validexpiry) values (%s,%s,%s,%s,%s,%s,NOW()+INTERVAL 2 HOUR)''',(firstname,lastname,email,hexhash,salt,vcode))
    except:
        raise
    emailstring = '''Dear %s %s,
An account has been created with this email at the CBN dollar auction site.
Go to http://%s/emailvalidate?email=%s&code=%s to validate your email address.
ALternatively, login and use this validation code %s.
Thank you.'''%(firstname,lastname,WEB_ADDRESS,email,vcode,vcode)
    try:
        sendEmail(emailstring, email)
    except:
        raise
    return 1

def sendEmail(emailstring,email):
    msg = MIMEText(emailstring)
    msg['Subject'] = "Verification Email"
    msg['From'] = "admin@places.com.ng"
    msg['To'] = email
    s = smtplib.SMTP('localhost')
    s.sendmail("admin@places.com.ng", [email], msg.as_string())
    s.quit()

def oldAuctions():
    results = runQuery('''select close_date, dollars, sold, rate, status, id from x_auction where status=2;''', ())
    rr = []
    for i in results:
        rr.append(dict(zip(["close_date", "dollars", "sold", "rate", "status", "id"], i)))
    return rr

def validate(email,code):
    rr = runQuery('''select validcode from x_user where email=%s''', (email,))
    if rr[0][0] == code:
        runQuery('''update x_user set isvalid=1 where email=%s''',(email,))
        return 1
    else:
        return 0
    