import os
import bcrypt
from models import *
from flask import Flask, session,render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import exc, or_, and_, func
from flask_sqlalchemy import SQLAlchemy
from helpers import apology, login_required, lookup, usd
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
import logging
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config.from_object(__name__)
Session(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

engine = create_engine(os.getenv("DATABASE_URL"))
db1 = scoped_session(sessionmaker(bind=engine))

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    id = session['user_id']
    rows = db1.execute(f"SELECT compsymbol, sum(quantity) AS quan FROM purchaseinfo WHERE id = {id} GROUP BY compsymbol HAVING sum(quantity) > 0")
    dic = {}
    totval = 0
    for row in rows:
        look = lookup(row.compsymbol)
        total = float(look['price']) * row.quan
        dic[row.compsymbol] = [look['name'], look['price'], row.quan, total]
        totval += total
    info = Users.query.get(id)
    # print(info.cash)
    dic['cash'] = ['','','',info.cash]
    dic['']=["","","",round((float(dic['cash'][3]) + totval), 2)]
    # print(dic)
    return render_template("index.html", dic = dic)

@app.route("/addmoney", methods=["GET", "POST"])
@login_required
def addmone():
    if request.method == "GET":
        return render_template("addmoney.html")
    else:
        if not request.form.get("addmoney"):
            return apology("Please Enter Amount", 400)
        id = session['user_id']
        info = Users.query.get(id)
        info.cash  = int(info.cash) + int(request.form.get("addmoney"))
        db.session.add(info)
        db.session.commit()
        return redirect("/")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        if not request.form.get("symbol"):
            return apology("please provide symbol", 400)
        symbol = request.form.get("symbol").upper()
        look = lookup(symbol)
        if look is None:
            return apology("Invalid Symbol", 400)
        if not request.form.get("shares"):
            return apology("please provide number of shares", 400)
        
        userid = session['user_id']
        userinfo = Users.query.get(userid)
        # print(type(look['price']))
        reqamt = look['price'] * float(request.form.get("shares"))
        if reqamt > userinfo.cash:
            return apology("purchase failed. Your balance is less than required amount")
        else:
            time_stamp = datetime.datetime.now()
            info = PurchaseInfo(userid, look['symbol'], look['name'], request.form.get("shares"), look['price'], reqamt, time_stamp)
            buyhistory = History(userid, look['symbol'], look['name'], request.form.get("shares"), look['price'], time_stamp)
            userinfo.cash = int(userinfo.cash) - reqamt
            try:
                db.session.add(info)
                db.session.add(userinfo)
                db.session.add(buyhistory)
                db.session.commit()
                return redirect("/")
            except:
                print('exception message', 'something went wrong while adding user')
                return apology("something went wrong while registering user, please register again", 500)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    id = session['user_id']
    rows = db1.execute(f"SELECT * FROM history WHERE id = {id}")
    dic = {}
    for row in rows:
        dic[row.timestamp] = [row.compsymbol, row.quantity, row.currentprice]
    # print(info.cash)
    # print(dic)
    return render_template("history.html", dic = dic)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = Users.query.filter_by(username = request.form.get('username')).first()
        
        # Ensure username exists and password is correct
        if rows is None or not check_password_hash(rows.hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("quote")
        look = lookup(symbol)
        if look is None:
            return apology("Invalid Symbol", 400)
        msg = f"A share of {look['name']} ({look['symbol']}) costs ${look['price']}."
    return render_template("quoted.html", msg = msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        # print(Users.query.filter_by(username = request.form.get("username")).first().cash)
        if not request.form.get("username"):
            return apology("must provide username", 403)
        if Users.query.filter_by(username = request.form.get("username")).first():
            return apology("username already exists", 403)
        if not request.form.get("password"):
            return apology("must provide password", 403)
        if not request.form.get("confirmation"):
            return apology("must provide confirm password", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and Confirm Password should match", 403)
        
        hash = generate_password_hash(request.form.get("password"))
        reg = Users(username = request.form.get("username"), hash = hash, cash = 10000)
        try:
            db.session.add(reg)
            db.session.commit()
            return redirect("/login")
        except:
            print('exception message', 'something went wrong while adding user')
            return apology("something went wrong while registering user, please register again", 500)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    id = session['user_id']
    if request.method == "GET":
        rows = db1.execute(f"SELECT DISTINCT compsymbol FROM purchaseinfo WHERE id = {id} AND quantity > 0 ")
        lis = []
        for row in rows:
            lis.append(row.compsymbol)
        return render_template("sell.html", lis=lis)
    else:
        # print(request.form.get("symbol"))
        if request.form.get("symbol") is None:
            return apology("please provide symbol", 400)
        if not request.form.get("shares"):
            return apology("please provide number of shares", 400)
        
        sharesymbol = request.form.get("symbol")
        sharequant = int(request.form.get("shares"))
        rows = db1.execute(f"SELECT sum(quantity) AS quan FROM purchaseinfo WHERE id = {id} AND compsymbol = '{sharesymbol}' GROUP BY compsymbol")
        quan = 0
        for row in rows:
            quan = row.quan
        if quan < sharequant:
            return apology("Entered share quantity is more than that of your current share quantity", 400)
        look = lookup(sharesymbol)
        totalamt = sharequant * look['price']
        userinfo = Users.query.get(id)
        userinfo.cash = int(userinfo.cash) + totalamt
        db.session.add(userinfo)
        db.session.commit()
        # rows1 = db1.execute(f"SELECT * FROM purchaseinfo WHERE id = {id} AND compsymbol = '{sharesymbol}' ORDER BY quantity DESC")
        rows1 = PurchaseInfo.query.filter(and_(PurchaseInfo.id == id, PurchaseInfo.compsymbol == sharesymbol)).order_by(PurchaseInfo.quantity.desc()).all()
        time_stamp = datetime.datetime.now()
        for row in rows1:
            # print(row.quantity)
            if sharequant > 0:
                if row.quantity > 0:
                    if row.quantity >= sharequant:
                        row.quantity = int(row.quantity) - sharequant
                        sharequant = 0
                        db.session.add(row)
                        db.session.commit()
                    elif row.quantity > 0 and row.quantity < sharequant:
                        sharequant -= int(row.quantity)
                        row.quantity = 0
                        db.session.add(row)
                        db.session.commit()
            else:
                break
        sellhistory = History(id, look['symbol'], look['name'], -(int((request.form.get("shares")))), look['price'], time_stamp)
        db.session.add(sellhistory)
        db.session.commit()
        return redirect("/")
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)