import cherrypy
import sample

cherrypy.config.update({'tools.sessions.on':True})

class TestAuction:
    @cherrypy.expose
    def index(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        else:
            return '''<html>
<head>
<title>Auctions</title>
</head>
<body style="font-family: verdana, arial, sans-serif;">
<h3>Open Auctions</h2>
<table>
<tr>
<td><b>ID</b></td>
<td><b>Amount</b><td>
<td><b>Closing Time</b></td>
</tr>
<tr>
<td><a href="auctions/1">1</a></td>
<td>$70,000.0000<td>
<td>11 Nov, 2011 19:59</a></td>
</tr>
<tr>
<tr>
<td><a href="auctions/2">2</a></td>
<td>$75,432.0000<td>
<td>12 Nov, 2011 04:59</a></td>
</tr>
<tr>
<tr>
<td><a href="auctions/5">5</a></td>
<td>$122,000.0000<td>
<td>10 Nov, 2011 10:00</a></td>
</tr>
<tr>
</table>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>''' % cherrypy.session.get('email')
    
#Login POST function
    @cherrypy.expose
    def login(self,email,password):
        d = cherrypy.request.headers
        if sample.login(email,password):
            cherrypy.session['email']=email
            raise cherrypy.HTTPRedirect("/")
        else:
            return "Login failed"

#Logout, redirects to home page and to Login page
    @cherrypy.expose
    def logout(self):
        cherrypy.session.delete()
        raise cherrypy.HTTPRedirect("/")

#Login page    
    @cherrypy.expose
    def signin(self):
        return '''<html>
<body style="font-family: verdana, arial, sans-serif;">
<form method="POST" action="/login">
<p>
Email: <input  type="text" name="email" size="40" /> <br>
Password: <input type="password" name="password" size="40" /> <br>
<input type="submit" value="Login" />
</form>
</body>
</html>'''

#Auction page shows details of auction and allows bid    
    @cherrypy.expose
    def auction (self,id):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        aa = sample.auctionDetails(id)
        if not aa:
            return '''Auction does not exist'''
        if aa["status"] == 0:
            return '''<html>
<body>
<h2>Auction %s</h2>
<table>
<tr>
<td>Creation date:</td> <td>%s</td>
</tr>
<tr>
<tr>
<td>Amount:</td> <td>$%s</td>
</tr>
<tr>
<td>Close date:</td> <td>%s</td>
</tr>
</table>
<form method="POST" action="/bid">
<p>
<input type="hidden" name="id" value=%s>
Amount:<input name="amount" type="text"><br>
Rate:<input name="rate" type="text"><br>
<input type="submit" value="Bid">
</p>
</form>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>
''' % (id,aa["creation_date"], aa["dollars"],aa["close_date"],id,email)
        if aa["status"] == 1:
            return '''<html>
<body>
<h2>Auction %s</h2>
<table>
<tr>
<td>Creation date:</td> <td>%s</td>
</tr>
<tr>
<tr>
<td>Amount:</td> <td>$%s</td>
</tr>
<tr>
</table>
<p> Auction is closed for bidding. <br>Winning bids are currently being calculated. <br>Please wait. </p>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>''' % (id, aa["creation_date"], aa["dollars"],email)
        if aa["status"] == 2:
            return '''<html>
<body>
<h2>Auction %s</h2>
<table>
<tr>
<td>Creation date:</td> <td>%s</td>
</tr>
<tr>
<tr>
<td>Amount:</td> <td>$%s</td>
</tr>
<tr>
</table>
<p> $%s dollars were sold at N%s to the dollar </p>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>''' % (id, aa["creation_date"], aa["dollars"], aa["sold"], aa["rate"],email)


    @cherrypy.expose
    def bid(self,id,amount,rate):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        if sample.bid(email,id,amount,rate):
            raise cherrypy.HTTPRedirect("/auction/%s"%id)
        else:
            return '''<html>Bid unsuccessful<br><a href="/auction/%s">Return to Auction</a></html>'''%id
    
    @cherrypy.expose
    def account(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        aa = sample.userDetails(email)
        return '''<html>
<head>
<title>Your Account</title>
</head>
<body style="font-family: verdana, arial, sans-serif;">
<h3>Open Bids</h2>
<p>
</p>
<h3>Wallet</h3>
<table>
<tr>
<td>Naira:</td>
<td>%s<td>
<td><a href="/refill">Refill</a></td>
</tr>
<tr>
<td>Dollars</td>
<td>%s<td>
<td><a href="./#">Withdraw</a></td>
</tr>
<tr>
<td>Available naira:</td>
<td>%s<td>
<td></td>
</tr>
</table>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''% (aa["nairabalance"], aa["dollarbalance"], aa["availablenaira"],email)

    @cherrypy.expose
    def refill(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        return '''<html>
<head>
<title>Reload Naira</title>
</head>
<body style="font-family: verdana, arial, sans-serif;">
<p>
<form method="POST" action="/nairareload">
<p>
Amount: <input  type="text" name="amount" size="20" /> <br>
<input type="submit" value="Reload" />
</p>
</form>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''
    
    @cherrypy.expose
    def nairareload(self,amount):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        sample.nairaReload(email,amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.expose
    def createauction(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        return'''<html>
<body>
<h2>Create Auction</h2>
<form method="POST" action="/create">
  <p>Dollars on sale: <input type="text" name="amount"></p>
  <p>Auction ends at: <input type="datetime" name="closedate"></p>
  <input type="submit" value="Create">
</form>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''%(email,)

    @cherrypy.expose
    def create(self,amount,closedate):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        sample.createAuction(amount,closedate)
        raise cherrypy.HTTPRedirect("/")
 
cherrypy.quickstart(TestAuction())
