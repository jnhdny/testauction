import pymysql, random, string, datetime, hashlib, smtplib
from decimal import *
from email.mime.text import MIMEText

# Please set to your own values
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "testauction"
CBN_ACCOUNT = "cbngov@cbn.gov"
WEB_ADDRESS = "127.0.0.1:8080"
MAIL_SERVER = "127.0.0.1"
MAIL_ADDRESS = "github@places.com.ng"

conn = pymysql.connect(DB_HOST,DB_USER,DB_PASSWORD,DB_NAME)

# Ignacio's random string generator from
# http://stackoverflow.com/questions/2257441/python-random-string-generation-with-upper-case-letters-and-digits
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def runQuery(query, parameters=()):
	c = conn.cursor()
	try:
	    c.execute(query, parameters)
	except:
	    raise
	results = c.fetchall()
	conn.commit()
	c.close()
	return results

def userDetails(email):
	results = runQuery("select id, availablenaira,nairabalance,dollarbalance,email from x_user where email = %s", (email,))
	# Courtesy http://stackoverflow.com/questions/209840/map-two-lists-into-a-dictionary-in-python
	return dict(zip(["id", "availablenaira", "nairabalance", "dollarbalance", "email"],results[0]))

def auctionDetails(id):
    results = runQuery("select id, dollars, status, rate, creation_date, close_date, sold from x_auction where id = %s", (id,))
    try:
        return dict(zip(["id","dollars","status","rate","creation_date","close_date","sold"],results[0]))
    except:
        return 0

def bidDetails(auction_id, email):
    results = runQuery('''select dollars, rate, bid_date, status from x_bid inner join x_user on x_user.id=x_bid.user_id where auction_id = %s and x_user.email = %s''', (auction_id,email))
    return results

def createAuction(amount,close_date):
    #Check if there is enough money in CBN account and then create an auction
    dav = runQuery('''select dollarbalance from x_user where email = %s''',(CBN_ACCOUNT))[0][0]
    close_date = getDate(close_date)
    if Decimal(amount) <= dav:
        c = tt.cursor()
        c.execute('''insert into x_auction (dollars,close_date) values (%s,%s);''',(amount,close_date))
        lrid = c.lastrowid
        tt.commit()
        c.close()        
        runQuery('''drop event if exists ev%s;''',(lrid))
        runQuery('''drop event if exists cb%s;''',(lrid))
        #Create event that closes the auction (changes its status) at close_date
        runQuery('''create event ev%s on schedule at %s do update x_auction set status = 1 where id = %s;''',(lrid,close_date,lrid))
        #Create event that calls stored procedure that computes bid winners and updates their account balances 1 minute after the bid ends
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
	try:
		hexhash = hashlib.sha512((password+pp[0][2]).encode("utf-8")).hexdigest()
		if hexhash == pp[0][0]:
			if pp[0][1] == 1:
				return 1
			if pp[0][1] == 0:
				return 2
	except:
		pass
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
Thank you.''' % (firstname, lastname, WEB_ADDRESS, MAIL_ADDRESS, vcode, vcode)
    try:
        sendEmail(emailstring, email)
    except:
        raise
    return 1

def oldAuctions():
    results = runQuery('''select close_date, dollars, sold, rate, status, id from x_auction where status = 2''')
    rr = []
    for i in results:
        rr.append(dict(zip(["close_date", "dollars", "sold", "rate", "status", "id"], i)))
    return rr

def validate(email,code):
    validcode = runQuery('''select validcode from x_user where email = %s''', (email,))[0][0]
    if code == validcode:
        runQuery('''update x_user set isvalid=1 where email = %s''', (email,))
        return 1
    else:
        return 0

def sendEmail(emailstring,email):
    msg = MIMEText(emailstring)
    msg['Subject'] = "Verification Email"
    msg['From'] = MAIL_ADDRESS
    msg['To'] = email
    s = smtplib.SMTP(MAIL_SERVER)
    s.sendmail(MAIL_ADDRESS, [email], msg.as_string())
    s.quit()

# I don't like these functions

def getDay(st):
    try:
        return int( st[(st.index("day")) - 1] )
    except:
        return 0

def getHour(st):
    try:
        return int( st[(st.index("hour")) - 1] )
    except:
        return 0

def getMinute(st):
    try:
        return int( st[(st.index("minute")) - 1] )
    except:
        return 0

def getDate(st):
    st = [a.strip("s") for a in st.strip().split()]
    return ( datetime.datetime.now() + datetime.timedelta(days=getDay(st),hours=getHour(st), minutes=getMinute(st)) ).strftime("%Y-%m-%d %H:%M:%S")

# Functions should do what they say, only
def getTimeLeft(tt):
	diff = tt - datetime.datetime.now()
	hours,minutes,seconds = (0,0,0)
	if diff.seconds > 60:
		minutes,seconds = divmod(diff.seconds,60)
		if minutes > 60:
			hours,minutes = divmod(minutes,60)
	datestring = ""
	if diff.days:
		datestring = datestring + str(diff.days) + " days "
	if hours:
		datestring = datestring + str(hours) + " hours "
	if minutes:
		datestring = datestring+ str(minutes)+ " minutes "
	if not (diff.days or hours or minutes):
		datestring = str(diff.seconds) + " seconds"
	return datestring
