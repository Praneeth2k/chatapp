from flask import Flask
from models import *
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']="postgres://calqfxvqbxtbbn:6fe9fc7be82a96c7b3509f396af0c71b4a63e0185ec67b369b6c89dabd656a38@ec2-107-20-198-176.compute-1.amazonaws.com:5432/dbin3qup59b8ra"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()
