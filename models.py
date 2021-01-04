from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import BIGINT

db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, nullable = False, primary_key = True)
    username = db.Column(db.String(200), nullable = False)
    hash = db.Column(db.String(200), nullable = False)
    cash = db.Column(db.Numeric, nullable = False)
    
    def __init__(self, username, hash, cash):
        self.username = username
        self.hash = hash
        self.cash = cash

class PurchaseInfo(db.Model):
    __tablename__ = "purchaseinfo"
    id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    compsymbol = db.Column(db.String(50), nullable = False)
    compname = db.Column(db.String(200), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    currentprice = db.Column(db.Float, nullable = False)
    totalprice = db.Column(db.Float, nullable = False)
    timestamp = db.Column(db.DateTime(), nullable=False, primary_key = True)
    
    
    def __init__(self, id, compsymbol, compname, quantity, currentprice, totalprice, timestamp):
        self.id = id
        self.compsymbol = compsymbol
        self.compname = compname
        self.quantity = quantity
        self.currentprice = currentprice
        self.totalprice = totalprice
        self.timestamp = timestamp
        
class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    compsymbol = db.Column(db.String(50), nullable = False)
    compname = db.Column(db.String(200), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    currentprice = db.Column(db.Float, nullable = False)
    timestamp = db.Column(db.DateTime(), nullable=False, primary_key = True)
    
    
    def __init__(self, id, compsymbol, compname, quantity, currentprice, timestamp):
        self.id = id
        self.compsymbol = compsymbol
        self.compname = compname
        self.quantity = quantity
        self.currentprice = currentprice
        self.timestamp = timestamp
    