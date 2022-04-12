#Modules that need to be imported for the code to work
from flask import Flask
from markupsafe import escape
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import abort
from flask import make_response
import sqlite3
from flask import flash, session, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5


#Variables used to connect to the bank project and form a secure relationship for the payment system to work

sid = '72v-akx1a2U='
pid = 'payment1'
secret = 'dOQ9eDFm7xCSPjbW91Rf0W2NgEMA'



app = Flask(__name__) #allows for the app to be exported before its run
app.secret_key = "secret key" #secret key used within the code



@app.route('/index')
def index():
    """
    Checks for username in session and will return either to home or login page depending on whether user is in session
    """
    print(url_for('index'))
    if 'username' in session:
        session['test'] = 'Test1' #creates a seperate session for logged in users, this is to ensure that the program will always know what user is logged in even when the pages change
        return home() #after checking that there is a user already logged in it will return to the home page
    else:
        return "You are not logged in Please login to continue. <br><a href='/login'><button>Login</button></a>" #If the user is not logged in then it will prompt the user to log in and generate a html button for them to login


@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Takes no inputs, will generate a form for the user to use to enter username and password to login
    """
    if request.method == 'POST':
        return do_the_login(request.form['uname'], request.form['pwd'])
    else:
        return show_the_login_form()
        
def show_the_login_form():
    return render_template('login.html',page=url_for('login')) #returns the template for the login page
 
def do_the_login(u,p):
    """
    Takes no inputs
    Connects to database which posses the table for the login information
    If login information matches it will return the user to the index which will send them to the home page
    """
    con = sqlite3.connect('Logins1.sqlite3')
    cur = con.cursor();
    cur.execute("SELECT count(*) FROM Logins WHERE Name=? AND Password=?;", (u, p))
    if(int(cur.fetchone()[0]))>0:# fetchone only takes 1 instance. if the fetchone is 0 then the user does not exist, otherwise it is 1.
        session['username'] = u # will create a session for the user when they are confimred to be logged in so the website will not automatically log the user out
        return redirect (url_for('index'))
    else:
        return render_template('unauthorised.html') # if the details do not match the user will not be logged in and sent to an unauthorised page

#def logged_in(t,n):
#    con = sqlite3.connect('logged_in.db')
#    try:
 #       con.execute('CREATE TABLE auth (title TEXT, name TEXT)')
 #       print ('Table created successfully');
#    except:
#        pass

#    con.close()  
#    con = sqlite3.connect('logged_in.db')
#    con.execute("INSERT INTO auth values(?,?);", (t,n))
#    con.commit()
#    con.close()  
    

@app.route('/add', methods=['POST'])
def add_product_to_cart():
    """
    Takes no paramethis inputs, will take inputs from form which adds products to the cart and will then use data from the products database to add costs and book codes
    will then also link to the simple payments project to create a checkout when the user checkouts the products.
    """
    
    cursor = None
    try:
        _quantity = int(request.form['quantity'])
        _code = request.form['code'] 
        # forms which take input for the quanityt of books being added and adding the books to the cart
        
        if _quantity and _code and request.method == 'POST':
            con = sqlite3.connect('products.db')
            cur = con.cursor();
            cur.execute("SELECT * FROM products WHERE code=?;", [_code])
            row = cur.fetchone()
            #connects to the product database and look for the product details and then add them to an array
            itemArray = { row[2] : {'name' : row[1], 'code' : row[2], 'quantity' : _quantity, 'price' : row[4], 'image' : row[3], 'total_price': _quantity * row[4]}}
            print('itemArray is', itemArray)
            
            all_total_price = 0
            all_total_quantity = 0
            
            session.modified = True
            
            if 'cart_item' in session:
                print('in session')
                #This will check if the code for the book selected is within the cart and make sure to adjust the quantity depending on how many are added to the cart
                if row[2] in session['cart_item']:
                    for key, value in session['cart_item'].items():
                        if row[2] == key:
                            old_quantity = session['cart_item'][key]['quantity']
                            total_quantity = old_quantity + _quantity
                            session['cart_item'][key]['quantity'] = total_quantity
                            session['cart_item'][key]['total_price'] = total_quantity * row[4]
                else:
                    session['cart_item'] = array_merge(session['cart_item'], itemArray)
                    
                for key, value in session['cart_item'].items():
                    individual_quantity = int(session['cart_item'][key]['quantity'])
                    individual_price = float(session['cart_item'][key]['total_price'])
                    all_total_quantity = all_total_quantity + individual_quantity
                    all_total_price = all_total_price + individual_price
                    #this will check for the price and adjust the price within the cart
                
            else:
                session['cart_item'] = itemArray
                all_total_quantity = all_total_quantity + _quantity
                all_total_price = all_total_price + _quantity * row[4]
                
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price
            

            checksumstr = f"pid={pid:s}&sid={sid:s}&amount={all_total_price:.1f}&token={secret:s}" #this will use the variables sid, pid and the secret token to form the checksum which will form a secure connection to the payment system allowing payments to go through
            #print('checksumstr is', checksumstr)
            checksum = md5(checksumstr.encode('utf-8')).hexdigest()
            session['checksum'] = checksum
            #print('checksum is', checksum)
            session['sid'] = sid
            session['pid'] = pid
            
            return redirect(url_for('.home'))
        else:
            return 'Error while adding item to cart'
    except Exception as e:
        print(e)
    finally:
        cur.close()
        con.close()

@app.route('/stock')
def stocklevel():
    """Takes no inputs, will connect to the products database and return the html template and make sure the stock is added to the template"""
    con = sqlite3.connect('products.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * from products")
    rows = cur.fetchall()
    con.close()
    return render_template("stock.html",rows = rows)

@app.route('/stock/addnew', methods=['GET', 'POST'])
def updatenewstock():
    """Takes no paramethis inputs, will return the stock form in which the user can input stock information and add new stock, which then updates the stock databse"""
    if request.method == 'POST':
        return insertNewStock(request.form['aiidd'], request.form['bname'], request.form['ccode'], request.form['iidir'], request.form['aprice'], request.form['ddscr'], request.form['ddate'], request.form['tprice'], request.form['quant'])
    else:
        return showstockupd();
    
def showstockupd():
    """Takes no inputs, returns the addstock html template"""
    return render_template('addstock.html')

def insertNewStock(a, n, c, i, p, d, w, t, q):
    """Takes no inputs, will connect to the products database and insert values for the new stock added"""
    con = sqlite3.connect('products.db')
    con.execute("INSERT INTO products values(?,?,?,?,?,?,?,?,?);", (a, n, c, i, p, d, w, t, q))
    con.commit()
    con.close()  

    return showstockupd()
       
@app.route('/home')
def home():
    """Takes no inputs, will check whether the user is using an admin account and if they are it will return the admin template,
    else if the user is not logging in with the admin account it will return them to the customer homepage"""
    print(url_for('home'))
    if session['username'] == 'admin':
        test = session['test']
        con = sqlite3.connect('products.db')
        cur = con.cursor();
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()
        return render_template('adminProducts.html', products=rows, page=url_for('home'))

    else:
        test = session['test']
        print(test)
        con = sqlite3.connect('products.db')
        cur = con.cursor();
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()
        return render_template('products.html', products=rows, page=url_for('home'))

@app.route('/empty')
def empty_cart():
    #Takes no inputs, will pop all items out of the cart item array and empty the cart 
	try:
		session.pop('cart_item', None)
		return redirect(url_for('home'))
	except Exception as e:
		print(e)

@app.route('/delete/<string:code>')
def delete_product(code):
    #Takes input code which will remove the code for the book and then it will check if the session has an items and
    #will adjust values for price and quantity and then return the user back to the homepage"""
	try:
		all_total_price = 0
		all_total_quantity = 0
		session.modified = True
		
		for item in session['cart_item'].items():
			if item[0] == code:				
				session['cart_item'].pop(item[0], None)
				if 'cart_item' in session:
					for key, value in session['cart_item'].items():
						individual_quantity = int(session['cart_item'][key]['quantity'])
						individual_price = float(session['cart_item'][key]['total_price'])
						all_total_quantity = all_total_quantity + individual_quantity
						all_total_price = all_total_price + individual_price
				break
		
		if all_total_quantity == 0:
			session.pop('cart_item', None)
		else:
			session['all_total_quantity'] = all_total_quantity
			session['all_total_price'] = all_total_price
		return redirect(url_for('home'))
	except Exception as e:
		print(e)
		
def array_merge( first_array , second_array ):
	if isinstance( first_array , list ) and isinstance( second_array , list ):
		return first_array + second_array
	elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
		return dict( list( first_array.items() ) + list( second_array.items() ) )
	elif isinstance( first_array , set ) and isinstance( second_array , set ):
		return first_array.union( second_array )
	return False		
		
    
if __name__ == "__main__":
    app.run()
    