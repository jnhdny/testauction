import cherrypy
import sample

cherrypy.config.update({'tools.sessions.on':True})

class TestAuction:
    @cherrypy.expose
    def index(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("http://127.0.0.1:8080/signin")
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
<h3><a href="/past">Past Auction Results</a></h3>
<p>Logged in as %s <a href="/logout">Logout</a></p>
</body>
</html>''' % cherrypy.session.get('email')
    
#Login function called by POST
    @cherrypy.expose
    def login(self,email,password):
        d = cherrypy.request.headers
        if sample.login(email,password):
            cherrypy.session['email']=email
            raise cherrypy.HTTPRedirect("/")
        else:
            return "Login failed"

#Logout, redirects to home page
    @cherrypy.expose
    def logout(self):
        cherrypy.session.delete()
        raise cherrypy.HTTPRedirect("/")

#Login page    
    @cherrypy.expose
    def signin(self):
        return '''<html>
<body style="font-family: verdana, arial, sans-serif;">
<form method="POST" action="http://127.0.0.1:8080/login">
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
</body>
</html>
''' % (id,aa["creation_date"], aa["dollars"],aa["close_date"],id)
        else:
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
<p> Auction is closed </p>
</body>
</html>''' % (id, aa["creation_date"], aa["dollars"])


    @cherrypy.expose
    def bid(self,id,amount,rate):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("http://127.0.0.1:8080/signin")
        email=cherrypy.session.get('email')
        sample.bid(email,id,amount,rate)
        raise cherrypy.HTTPRedirect("/auction/%s"%id)

 
cherrypy.quickstart(TestAuction())
