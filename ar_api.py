#To run program:  python3 fth_api.py prashant

#README:  if conn error make sure password is set properly in RDS PASSWORD section

#README:  Debug Mode may need to be set to Fales when deploying live (although it seems to be working through Zappa)

#README:  if there are errors, make sure you have all requirements are loaded
#pip3 install flask
#pip3 install flask_restful
#pip3 install flask_cors
#pip3 install Werkzeug
#pip3 install pymysql
#pip3 install python-dateutil

import os
import uuid
import boto3
import json
import math
from datetime import datetime
from datetime import timedelta
from pytz import timezone
import random
import string
import stripe

from flask import Flask, request, render_template, redirect, url_for
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message
# used for serializer email and error handling
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
#from flask_cors import CORS

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.security import generate_password_hash, \
     check_password_hash

from google.oauth2 import id_token
from google.auth.transport import requests as reqs


from dateutil.relativedelta import *
from decimal import Decimal
from datetime import datetime, date, timedelta
from hashlib import sha512
from math import ceil
import string
import random
# BING API KEY
# Import Bing API key into bing_api_key.py

#  NEED TO SOLVE THIS
# from env_keys import BING_API_KEY, RDS_PW

import decimal
import sys
import json
import pytz
import pymysql
import requests
import jwt
import base64

#RDS_HOST = 'pm-mysqldb.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
RDS_HOST = 'io-mysqldb8.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
#RDS_HOST = 'localhost'
RDS_PORT = 3306
#RDS_USER = 'root'
RDS_USER = 'admin'
#RDS_DB = 'feed_the_hungry'
RDS_DB = 'ar'

s3 = boto3.client('s3')

# aws s3 bucket where the image is stored
#BUCKET_NAME = os.environ.get('MEAL_IMAGES_BUCKET')
#BUCKET_NAME = 'servingnow'
# allowed extensions for uploading a profile photo file
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

#app = Flask(__name__)
app = Flask(__name__)

# Allow cross-origin resource sharing
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

#Set to false when doing a live deploy
app.config['DEBUG'] = True
#Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ptydtesting@gmail.com'
app.config['MAIL_PASSWORD'] = 'PTYDTesting1'
#app.config['MAIL_DEFAULT_SENDER'] = 'ptydtesting@gmail.com'
#app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#app.config['MAIL_USERNAME'] = os.environ.get('EMAIL')
#app.config['MAIL_PASSWORD'] = os.environ.get('PASSWORD')
#app.config['MAIL_USERNAME'] = ''
#app.config['MAIL_PASSWORD'] = ''

# Setting for mydomain.com                            
#app.config['MAIL_SERVER'] = 'smtp.mydomain.com'   
#app.config['MAIL_PORT'] = 465

# Setting for gmail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465

#app.config['MAIL_USE_TLS'] = False
#app.config['MAIL_USE_SSL'] = True


#app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY')
google_client_id = '853496996257-nhfcs13imjlglaervfgoh1abodgafctg.apps.googleusercontent.com'
mail = Mail(app)
s = URLSafeTimedSerializer('thisisaverysecretkey')
# API
api = Api(app)

# convert to UTC time zone when testing in local time zone
utc = pytz.utc
def getToday(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d")
def getNow(): return datetime.strftime(datetime.now(utc),"%Y-%m-%d %H:%M:%S")

# Get RDS password from command line argument
def RdsPw():
    if len(sys.argv) == 2:
        return str(sys.argv[1])
    return ""

# RDS PASSWORD
# When deploying to Zappa, set RDS_PW equal to the password as a string
# When pushing to GitHub, set RDS_PW equal to RdsPw()
RDS_PW = 'prashant'
# RDS_PW = RdsPw()


# aws s3 bucket where the image is stored
# BUCKET_NAME = os.environ.get('MEAL_IMAGES_BUCKET')
BUCKET_NAME = 'infinitebooks'
# allowed extensions for uploading a profile photo file



getToday = lambda: datetime.strftime(date.today(), "%Y-%m-%d")
getNow = lambda: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")



# Connect to MySQL database (API v2)
def connect():
    global RDS_PW
    global RDS_HOST
    global RDS_PORT
    global RDS_USER
    global RDS_DB

    print("Trying to connect to RDS (API v2)...")
    try:
        conn = pymysql.connect( RDS_HOST,
                                user=RDS_USER,
                                port=RDS_PORT,
                                passwd=RDS_PW,
                                db=RDS_DB,
                                cursorclass=pymysql.cursors.DictCursor)
        print("Successfully connected to RDS. (API v2)")
        return conn
    except:
        print("Could not connect to RDS. (API v2)")
        raise Exception("RDS Connection failed. (API v2)")

# Disconnect from MySQL database (API v2)
def disconnect(conn):
    try:
        conn.close()
        print("Successfully disconnected from MySQL database. (API v2)")
    except:
        print("Could not properly disconnect from MySQL database. (API v2)")
        raise Exception("Failure disconnecting from MySQL database. (API v2)")

# Serialize JSON
def serializeResponse(response):
    try:
        #print("In Serialize JSON")
        for row in response:
            for key in row:
                if type(row[key]) is Decimal:
                    row[key] = float(row[key])
                elif type(row[key]) is date or type(row[key]) is datetime:
                    row[key] = row[key].strftime("%Y-%m-%d")
        #print("In Serialize JSON response", response)
        return response
    except:
        raise Exception("Bad query JSON")








# Execute an SQL command (API v2)
# Set cmd parameter to 'get' or 'post'
# Set conn parameter to connection object
# OPTIONAL: Set skipSerialization to True to skip default JSON response serialization
def execute(sql, cmd, conn, skipSerialization = False):
    response = {}
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cmd == 'get':
                result = cur.fetchall()
                response['message'] = 'Successfully executed SQL query.'
                # Return status code of 280 for successful GET request
                response['code'] = 280
                if not skipSerialization:
                    result = serializeResponse(result)
                response['result'] = result
            elif cmd in 'post':
                conn.commit()
                response['message'] = 'Successfully committed SQL command.'
                # Return status code of 281 for successful POST request
                response['code'] = 281
            else:
                response['message'] = 'Request failed. Unknown or ambiguous instruction given for MySQL command.'
                # Return status code of 480 for unknown HTTP method
                response['code'] = 480
    except:
        response['message'] = 'Request failed, could not execute MySQL command.'
        # Return status code of 490 for unsuccessful HTTP request
        response['code'] = 490
    finally:
        response['sql'] = sql
        return response

# Close RDS connection
def closeRdsConn(cur, conn):
    try:
        cur.close()
        conn.close()
        print("Successfully closed RDS connection.")
    except:
        print("Could not close RDS connection.")

# Runs a select query with the SQL query string and pymysql cursor as arguments
# Returns a list of Python tuples
def runSelectQuery(query, cur):
    try:
        cur.execute(query)
        queriedData = cur.fetchall()
        return queriedData
    except:
        raise Exception("Could not run select query and/or return data")


#Upload a book image as jpeg to s3 and get link
def image_s3_upload(image, book_title):
    s3_resource = boto3.resource('s3')
    s3_obj = s3_resource.Object(BUCKET_NAME, book_title + '.jpg')
    s3_obj.put(ACL = 'public-read', Body = base64.b64decode(image), ContentType = 'image/jpeg')
    location = s3.get_bucket_location(Bucket = BUCKET_NAME)['LocationConstraint']
    image_url =  "https://%s.s3-%s.amazonaws.com/%s" % (BUCKET_NAME, location, book_title + '.jpg')
    return image_url

#Upload a book as pdf to s3 and get link
def book_s3_upload(book, book_title):
    s3_resource = boto3.resource('s3')
    s3_obj = s3_resource.Object(BUCKET_NAME, book_title + '_readable.pdf')
    s3_obj.put(ACL = 'public-read', Body = base64.b64decode(book), ContentType = 'application/pdf')
    location = s3.get_bucket_location(Bucket = BUCKET_NAME)['LocationConstraint']
    book_url =  "https://%s.s3-%s.amazonaws.com/%s" % (BUCKET_NAME, location, book_title + '_readable.pdf')
    return book_url

# -- Queries start here -------------------------------------------------------------------------------


# Queries for Untitled Books

class AllBooks(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.books;
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllBooks query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)
#https://ls802wuqo5.execute-api.us-west-1.amazonaws.com/dev/api/v2/AllBooks
# Example route for API test: http://127.0.0.1:4000/api/v2/BooksByAuthorEmail/pmarathay@gmail.com
class BooksByAuthorEmail(Resource):
    def get(self, user_email):
        response = {}
        items = {}
        #data = request.get_json(force=True)
        print("User Email = ",  user_email)
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.books b
                LEFT JOIN ar.users u1
                ON b.author_uid = u1.user_uid
                LEFT JOIN ar.reviews r
                ON b.book_uid = r.rev_book_uid
                LEFT JOIN ar.users u2
                ON r.reader_id = u2.user_uid
                WHERE u1.email = \'""" + user_email + """\';
                """
            items = execute(query, 'get', conn)

            response['message'] = 'BooksByAuthorEmail query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

# Example route for API test: http://127.0.0.1:4000/api/v2/BooksByAuthorUID/100-000001
class BooksByAuthorUID(Resource):
    def get(self, author_uid):
        response = {}
        items = {}
        print("author_uid", author_uid)
        try:
            conn = connect()
            query = """
                    SELECT * FROM ar.books 
                    WHERE author_uid = \'""" + author_uid + """\';
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'BooksByAuthorUID query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class BooksByName(Resource):
    def get(self, first_name, last_name):
        response = {}
        items = {}
        try:
            conn = connect()

            firstName = '\'' + first_name + '\''
            lastName = '\'' + last_name + '\''

            query = """SELECT temp.first_name
                            , temp.last_name
                            , b.book_uid
                            , b.title
                            , b.book_cover_image
                            , b.genre
                            , b.num_pages
                            , b.description
                            , b.format
                            , b.book_link 
                        FROM (SELECT user_uid
                                    , first_name
                                    , last_name 
                            FROM users WHERE first_name = %s AND last_name = %s) AS temp, 
                        books b WHERE temp.user_uid = b.author_uid;""" % (firstName, lastName)

            items = execute(query, 'get', conn)

            response['message'] = 'Successfully retrieved books for author %s %s' % (first_name, last_name)
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retrieving books for author %s %s' % (first_name, last_name))
        finally:
            disconnect(conn)


# Just returns the entire users table
class AllUsers(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users;
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllUsers query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class AllAuthors(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users
                WHERE role = "author";
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllAuthors query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class AllReaders(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users
                WHERE role = "reader";
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllReaders query successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class ReviewByUser(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            
            items = execute("""SELECT u.username
                                    , u.first_name
                                    , u.last_name
                                    , u.email
                                    , temp.counter as `Review Count` 
                                    FROM(
                                        SELECT reader_id
                                            ,  count(review_uid) as counter 
                                            FROM reviews GROUP BY reader_id) 
                                AS temp JOIN users u ON u.user_uid = temp.reader_id WHERE u.role != 'author';""", 'get', conn)

            response['message'] = 'Successfully retriving amount of reviews by user'
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error in ReviewByUser.')
        finally:
            disconnect(conn)


class ReviewByBook(Resource):
    def get(self, review_uid):
        response = {}
        items = {}
        try:
            conn = connect()

            rev_uid = '\'' + review_uid + '\';'
            query = """SELECT * FROM reviews WHERE rev_book_uid = %s""" % rev_uid

            items = execute(query, 'get', conn)
            print(items)
            response['message'] = 'Successfully retreived reviews for book UID %s' % review_uid
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retriving reviews for book UID %s' % review_uid)
        finally:
            disconnect(conn)

class ReivewByBookTitle(Resource):
    def get(self, book_title):
        response = {}
        items = {}
        try:
            conn = connect()

            bookTitle = '\'' + book_title+ '\''
            query = """SELECT temp.title
                            , r.review_uid
                            , r.comments
                            , r.rating_title
                            , r.rating_content 
                        FROM (SELECT title
                                    , book_uid 
                                FROM books WHERE title = %s) 
                        AS temp, reviews r WHERE r.rev_book_uid = temp.book_uid;""" % bookTitle
            
            items = execute(query, 'get', conn)
            response['message'] = 'Successfully retrieved reviews for book %s' % book_title
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retrieving reviews for book %s' % book_title)
        finally:
            disconnect(conn)

class ReivewByBookUID(Resource):
    def get(self, book_uid):
        response = {}
        items = {}
        try:
            conn = connect()

            bookUID = "\'" + book_uid + "\'"   
            query = """SELECT temp.title
                            , temp.book_uid
                            , r.review_uid
                            , r.comments
                            , r.rating_title
                            , r.rating_content 
                            , temp.book_cover_image
                        FROM (SELECT title
                                    , book_uid 
                                    , book_cover_image
                                FROM books WHERE book_uid = %s) 
                        AS temp, reviews r WHERE r.rev_book_uid = temp.book_uid;""" % bookUID
            
            items = execute(query, 'get', conn)

            response['message'] = 'Successfully retrived book %s' % book_uid
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retriving book %s' % book_uid)
        finally:
            disconnect(conn)

class OneUserArg(Resource):
    def get(self, user_uid):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ # Returns request from supplied user_uid arg
                SELECT * FROM ar.users 
                WHERE user_uid = \'""" + user_uid + """\';
                """
            items = execute(query, 'get', conn)
            response['message'] = 'GET OneUserArg successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class BooksUnderUser(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()

            query = """SELECT temp.username
                            , b.book_uid
                            , b.title
                            , b.author_uid
                            , b.genre
                            , b.num_pages 
                            , b.book_cover_image
                            , b.description
                            , b.book_link
                        FROM (SELECT rev_book_uid
                                    , reader_id
                                    , username 
                                FROM reviews JOIN users ON user_uid = reader_id) 
                        AS temp JOIN books b ON b.book_uid = temp.rev_book_uid;"""
            
            items = execute(query, 'get', conn)

            response['message'] = 'Successfully retrived books for user'
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retriving books for users')
        finally:
            disconnect(conn)

class AuthorForEachBook(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()

            query = """select b.title, b.genre, b.num_pages, b.format, b.book_cover_image, CONCAT(u.first_name, " ", u.last_name) AS author
                                from ar.books b, ar.users u
                                where b.author_uid = u.user_uid;"""
            
            items = execute(query, 'get', conn)

            response['message'] = 'Successfully retrived author for each book'
            response['result'] = items['result']

            return response, 200
        except:
            raise BadRequest('Bad request, error while retriving author for each book')
        finally:
            disconnect(conn)

class SignUp(Resource):
    def post(self):
        response = {}
        items = []
        try:
            conn = connect()
            data = request.get_json(force=True)

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            pen_name = data['pen_name']
            language = data['language']
            likes_writing = data['likes_writing_about']
            bio = data['bio']
            role = data['role']
            gender = data['gender']
            education = data['educationLevel']
            age = data['age']
            career = data['careerField']
            income = data['income'] 
            email = data['email']
            phone = data['phone']
            interest = data['interest']
            hours = data['hours']
            favorites = data['favorites']
            social = data['social']
            password = data['password']
            user_id = data['user_id'] if data.get('user_id') is not None else 'NULL'
            
            print(data)

            if data.get('social') is None or data.get('social') == "FALSE" or data.get('social') == False:
                social_signup = False
            else:
                social_signup = True
            

            get_user_id_query = "CALL get_user_uid();"
            NewUserIDresponse = execute(get_user_id_query, 'get', conn)

            if NewUserIDresponse['code'] == 490:
                string = " Cannot get new User id. "
                print("*" * (len(string) + 10))
                print(string.center(len(string) + 10, "*"))
                print("*" * (len(string) + 10))
                response['message'] = "Internal Server Error."
                return response, 500
            NewUserID = NewUserIDresponse['result'][0]['new_id']
            

            if social_signup == False:

                salt = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

                password = sha512((data['password'] + salt).encode()).hexdigest()
                print('password------', password)
                algorithm = "SHA512"
                access_token = 'NULL'
                refresh_token = 'NULL'
                user_social_signup = 'NULL'
            else:

                access_token = data['access_token']
                refresh_token = data['refresh_token']
                salt = 'NULL'   
                password = 'NULL'
                algorithm = 'NULL'
                user_social_signup = data['social']
            
            if user_id != 'NULL' and user_id:

                NewUserID = user_id 

                query = '''
                            SELECT user_access_token, user_refresh_token
                            FROM ar.users u
                            WHERE user_uid = \'''' + user_id + '''\';
                       '''
                it = execute(query, 'get', conn)
                print('query executed')
                print('it-------', it)

                access_token = it['result'][0]['user_access_token']
                refresh_token = it['result'][0]['user_refresh_token']


                user_insert_query =  ['''
                                    UPDATE ar.users
                                    SET 
                                    user_created_at = \'''' + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + '''\',
                                    first_name = \'''' + firstName + '''\',
                                    last_name = \'''' + lastName + '''\',
                                    phone = \'''' + phone + '''\',
                                    username = \'''' + username + '''\',
                                    pen_name = \'''' + pen_name + '''\',
                                    language = \'''' + language + '''\',
                                    likes_writing_about = \'''' + likes_writing + '''\',
                                    bio = \'''' + bio + '''\',
                                    gender = \'''' + gender + '''\',
                                    education_level = \'''' + education + '''\',
                                    age = \'''' + age + '''\',
                                    career_field = \'''' + career + '''\',
                                    income = \'''' + income + '''\',
                                    role = \'''' + role + '''\',
                                    interest = \'''' + interest + '''\',
                                    hours = \'''' + hours + '''\',
                                    favorites = \'''' + favorites + '''\',
                                    password_salt = \'''' + salt + '''\',
                                    password_hashed = \'''' + password + '''\',
                                    password_algorithm = \'''' + algorithm + '''\',
                                    user_social_media = \'''' + user_social_signup + '''\'
                                    WHERE user_uid = \'''' + user_id + '''\';
                                    ''']


            else:

                # check if there is a same customer_id existing
                query = """
                        SELECT email FROM ar.users
                        WHERE email = \'""" + email + "\';"
                print('email---------' + email)
                items = execute(query, 'get', conn)
                if items['result']:

                    items['result'] = ""
                    items['code'] = 409
                    items['message'] = "Email address has already been taken."

                    return items

                if items['code'] == 480:

                    items['result'] = ""
                    items['code'] = 480
                    items['message'] = "Internal Server Error."
                    return items

                print("inserting to db")
                # write everything to database
                user_insert_query = ["""
                                        INSERT INTO ar.users
                                        (
                                            user_uid,
                                            user_created_at,
                                            username,
                                            first_name,
                                            last_name,
                                            pen_name,
                                            language,
                                            likes_writing_about,
                                            bio,
                                            role,
                                            gender,
                                            education_level,
                                            age,
                                            career_field,
                                            income,
                                            email,
                                            phone,
                                            interest,
                                            hours,
                                            favorites,
                                            password_salt,
                                            password_hashed,
                                            password_algorithm,
                                            user_social_media,
                                            user_access_token,
                                            user_refresh_token
                                        )
                                        VALUES
                                        (
                                        
                                            \'""" + NewUserID + """\',
                                            \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
                                            \'""" + username + """\',
                                            \'""" + first_name + """\',
                                            \'""" + last_name + """\',
                                            \'""" + pen_name + """\',
                                            \'""" + language + """\',
                                            \'""" + likes_writing + """\',
                                            \'""" + bio + """\',
                                            \'""" + role + """\',
                                            \'""" + gender + """\',
                                            \'""" + education + """\',
                                            \'""" + age + """\',
                                            \'""" + career + """\',
                                            \'""" + income + """\',
                                            \'""" + email + """\',
                                            \'""" + phone + """\',
                                            \'""" + interest + """\',
                                            \'""" + hours + """\',
                                            \'""" + favorites + """\',
                                            \'""" + salt + """\',
                                            \'""" + password + """\',
                                            \'""" + algorithm + """\',
                                            \'""" + user_social_signup + """\',
                                            \'""" + access_token + """\',
                                            \'""" + refresh_token + """\');"""]
            print(user_insert_query[0])
            items = execute(user_insert_query[0], 'post', conn)

            if items['code'] != 281:
                items['result'] = ""
                items['code'] = 480
                items['message'] = "Error while inserting values in database"

                return items


            items['result'] = {
                'first_name': first_name,
                'last_name': last_name,
                'user_uid': NewUserID,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            items['message'] = 'Signup successful'
            items['code'] = 200

            # Twilio sms service

            #resp = url_for('sms_service', phone_num='+17327818408', _external=True)
            #resp = sms_service('+1'+phone, firstName)
            #print("resp --------", resp)



            print('sss-----', social_signup)

            if social_signup == False:
                token = s.dumps(email)  
                msg = Message("Email Verification", sender='ptydtesting@gmail.com', recipients=[email])

                print('MESSAGE----', msg)
                print('message complete')
                link = url_for('confirm', token=token, hashed=password, _external=True)
                print('link---', link)
                msg.body = "Click on the link {} to verify your email address.".format(link)
                print('msg-bd----', msg.body)
                print(msg)
                mail.send(msg)
            print('passed mail sending message')


            return items
        except:
            print("Error happened while Sign Up")
            if "NewUserID" in locals():
                execute("""DELETE FROM users WHERE user_uid = '""" + NewUserID + """';""", 'post', conn)
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

#http://127.0.0.1:4000/api/v2/SignUp
#https://ls802wuqo5.execute-api.us-west-1.amazonaws.com/dev/api/v2/SignUp
# {
#   "username":"testing",
#   "first_name":"te",
#   "last_name":"st",
#   "role":"testingrole",
#   "email":"xyz@gmail.com",
#   "phone":"4084084088",
#   "interest":"good books",
#   "hours":"10",
#   "favorites":"fantasy",
#   "social":"FALSE",
#   "access_token":"NULL",
#   "refresh_token":"NULL",
#   "password":"1234"
# }

# confirmation page
@app.route('/api/v2/confirm', methods=['GET'])
def confirm():
    try:
        token = request.args['token']
        hashed = request.args['hashed']
        print("hased: ", hashed)
        email = s.loads(token)  # max_age = 86400 = 1 day

        # marking email confirmed in database, then...
        conn = connect()
        query = """UPDATE ar.users SET email_verified = 1 WHERE email = \'""" + email + """\';"""
        update = execute(query, 'post', conn)
        if update.get('code') == 281:
            # redirect to login page
            # only for testing on localhost
            return redirect('http://localhost:4000/login?email={}&hashed={}'.format(email, hashed))
            #return redirect('https://infinitebooks.me/login?email={}&hashed={}'.format(email, hashed))
        else:
            print("Error happened while confirming an email address.")
            error = "Confirm error."
            err_code = 401  # Verification code is incorrect
            return error, err_code
    except (SignatureExpired, BadTimeSignature) as err:
        status = 403  # forbidden
        return str(err), status
    finally:
        disconnect(conn)

class AccountSalt(Resource):
    def post(self):
        response = {}
        try:
            conn = connect()

            data = request.get_json(force=True)
            print(data)
            email = data['email']
            query = """
                    SELECT password_algorithm, 
                            password_salt 
                    FROM ar.users u
                    WHERE email = \'""" + email + """\';
                    """
            items = execute(query, 'get', conn)
            if not items['result']:
                items['message'] = "Email doesn't exists"
                items['code'] = 404
            return items
            items['message'] = 'SALT sent successfully'
            items['code'] = 200
            return items
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

#http://127.0.0.1:4000/api/v2/AccountSalt
# {
#   "email":"xyz@gmail.com"
# }


class Login(Resource):
    def post(self):
        response = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            email = data['email']
            password = data.get('password')
            refresh_token = data.get('token')
            signup_platform = data.get('signup_platform')
            query = """
                    SELECT user_uid,
                        username,
                        first_name,
                        last_name,
                        email,
                        password_hashed,
                        email_verified,
                        user_social_media,
                        user_access_token,
                        user_refresh_token
                    FROM ar.users u
                    WHERE email = \'""" + email + """\';
                    """
            items = execute(query, 'get', conn)
            print('Password', password)
            print(items)

            if items['code'] != 280:
                response['message'] = "Internal Server Error."
                response['code'] = 500
                return response
            elif not items['result']:
                items['message'] = 'Email Not Found. Please signup'
                items['result'] = ''
                items['code'] = 404
                return items
            else:
                print(items['result'])
                print('sc: ', items['result'][0]['user_social_media'])


                # checks if login was by social media
                if password and items['result'][0]['user_social_media'] != 'NULL' and items['result'][0]['user_social_media'] != None:
                    response['message'] = "Need to login by Social Media"
                    response['code'] = 401
                    return response

               # nothing to check
                elif (password is None and refresh_token is None) or (password is None and items['result'][0]['user_social_media'] == 'NULL'):
                    response['message'] = "Enter password else login from social media"
                    response['code'] = 405
                    return response

                # compare passwords if user_social_media is false
                elif (items['result'][0]['user_social_media'] == 'NULL' or items['result'][0]['user_social_media'] == None) and password is not None:

                    if items['result'][0]['password_hashed'] != password:
                        items['message'] = "Wrong password"
                        items['result'] = ''
                        items['code'] = 406
                        return items

                    if ((items['result'][0]['email_verified']) == '0') or (items['result'][0]['email_verified'] == "FALSE"):
                        response['message'] = "Account need to be verified by email."
                        response['code'] = 407
                        return response

                # compare the refresh token because it never expire.
                elif (items['result'][0]['user_social_media']) != 'NULL':
                    '''
                    keep
                    if signup_platform != items['result'][0]['user_social_media']:
                        items['message'] = "Wrong social media used for signup. Use \'" + items['result'][0]['user_social_media'] + "\'."
                        items['result'] = ''
                        items['code'] = 401
                        return items
                    '''
                    if (items['result'][0]['user_refresh_token'] != refresh_token):
                        print(items['result'][0]['user_refresh_token'])

                        items['message'] = "Cannot Authenticated. Token is invalid"
                        items['result'] = ''
                        items['code'] = 408
                        return items

                else:
                    string = " Cannot compare the password or refresh token while log in. "
                    print("*" * (len(string) + 10))
                    print(string.center(len(string) + 10, "*"))
                    print("*" * (len(string) + 10))
                    response['message'] = string
                    response['code'] = 500
                    return response
                del items['result'][0]['password_hashed']
                del items['result'][0]['email_verified']

                query = "SELECT * from ar.users WHERE email = \'" + email + "\';"
                items = execute(query, 'get', conn)
                items['message'] = "Authenticated successfully."
                items['code'] = 200
                return items

        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

#http://127.0.0.1:4000/api/v2/Login
# {
#   "email":"xyz@gmail.com",
#   "refresh_token":"",
#   "password":"bacb033dbdf8e19ad9ab01a874d433d6c4b93bc9eaaebd81710f762830ab9abb19ba393e9e9cfac391d74d0fd7098bdb6a5f78bffc3dd4b887655e220c6ca29b",
#   "signup_platform":""
# }

class AppleLogin (Resource):

    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            token = request.form.get('id_token')
            print(token)
            if token:
                print('Starting decode')
                data = jwt.decode(token, verify=False)
                print('data-----', data)
                email = data.get('email')

                print(data, email)
                if email is not None:
                    sub = data['sub']
                    query = """
                    SELECT user_uid,
                        first_name,
                        last_name,
                        email,
                        password_hashed,
                        email_verified,
                        user_social_media,
                        user_access_token,
                        user_refresh_token
                    FROM ar.users u
                    WHERE email = \'""" + email + """\';
                    """
                    items = execute(query, 'get', conn)
                    print(items)

                    if items['code'] != 280:
                        items['message'] = "Internal error"
                        return items


                    # new customer
                    if not items['result']:
                        items['message'] = "Email doesn't exists Please go to the signup page"
                        get_user_id_query = "CALL get_user_uid();"
                        NewUserIDresponse = execute(get_user_id_query, 'get', conn)

                        if NewUserIDresponse['code'] == 490:
                            string = " Cannot get new User id. "
                            print("*" * (len(string) + 10))
                            print(string.center(len(string) + 10, "*"))
                            print("*" * (len(string) + 10))
                            response['message'] = "Internal Server Error."
                            response['code'] = 500
                            return response

                        NewUserID = NewUserIDresponse['result'][0]['new_id']
                        user_social_signup = 'APPLE'
                        print('NewUserID', NewUserID)

                        customer_insert_query = """
                                    INSERT INTO ar.users
                                    (
                                        user_uid,
                                        user_created_at,
                                        email,
                                        user_social_media,
                                        user_refresh_token
                                    )
                                    VALUES
                                    (
                                    
                                        \'""" + NewUserID + """\',
                                        \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
                                        \'""" + email + """\',
                                        \'""" + user_social_signup + """\',
                                        \'""" + sub + """\'
                                    );"""

                        item = execute(customer_insert_query, 'post', conn)

                        print('INSERT')

                        if item['code'] != 281:
                            item['message'] = 'Check insert sql query'
                            return item

                        return redirect("http://localhost:3000/socialsignup?id=" + NewUserID)

                    # Existing customer

                    if items['result'][0]['user_refresh_token']:
                        print('user_refresh_token')
                        print(items['result'][0]['user_social_media'], items['result'][0]['user_refresh_token'])

                        if items['result'][0]['user_social_media'] != "APPLE":
                            print('Wrong sign up method')
                            items['message'] = "Wrong social media used for signup. Use \'" + items['result'][0]['user_social_media'] + "\'."
                            items['code'] = 400
                            return redirect("http://localhost:3000/?media=" + items['result'][0]['user_social_media'])

                        elif items['result'][0]['user_refresh_token'] != sub:
                            print('token mismatch')
                            items['message'] = "Token mismatch"
                            items['code'] = 400
                            return redirect("http://localhost:3000/")

                        else:
                            print('successfully login with apple redirecting......')
                            return redirect("http://localhost:3000/users?id=" + items['result'][0]['user_uid'])

                else:
                    items['message'] = "Email not returned by Apple LOGIN"
                    items['code'] = 400
                    return items


            else:
                response = {
                    "message": "Token not found in Apple's Response",
                    "code": 400
                }
                return response
        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)



class GoogleLogin (Resource):

    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            token = request.form.get('id_token')
            print(token)
            if token:
                try: 
                    data = id_token.verify_oauth2_token(token, reqs.Request(), '407408718192.apps.googleusercontent.com')
                except ValueError:
                    print('Invalid token')
                    response['message'] = 'Invalid token'
                    response['code'] = 401
                    return response, 401

                print('valid token')
                email = data['email']
                if email is not None:
                    sub = data['sub']
                    query = """
                    SELECT user_uid,
                        first_name,
                        last_name,
                        email,
                        password_hashed,
                        email_verified,
                        user_social_media,
                        user_access_token,
                        user_refresh_token
                    FROM ar.users u
                    WHERE email = \'""" + email + """\';
                    """
                    items = execute(query, 'get', conn)
                    print(items)

                    if items['code'] != 280:
                        items['message'] = "Internal error"
                        return items


                    # new customer
                    if not items['result']:
                        items['message'] = "Email doesn't exists Please go to the signup page"
                        get_user_id_query = "CALL get_user_uid();"
                        NewUserIDresponse = execute(get_user_id_query, 'get', conn)

                        if NewUserIDresponse['code'] == 490:
                            string = " Cannot get new User id. "
                            print("*" * (len(string) + 10))
                            print(string.center(len(string) + 10, "*"))
                            print("*" * (len(string) + 10))
                            response['message'] = "Internal Server Error."
                            response['code'] = 500
                            return response

                        NewUserID = NewUserIDresponse['result'][0]['new_id']
                        user_social_signup = 'GOOGLE'
                        print('NewUserID', NewUserID)


                        customer_insert_query = """
                                    INSERT INTO ar.users
                                    (
                                        user_uid,
                                        user_created_at,
                                        email,
                                        email_verified,
                                        user_social_media,
                                        user_refresh_token
                                    )
                                    VALUES
                                    (
                                    
                                        \'""" + NewUserID + """\',
                                        \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
                                        \'""" + email + """\',
                                        \'""" + '1' + """\',
                                        \'""" + user_social_signup + """\',
                                        \'""" + sub + """\'
                                    );"""

                        item = execute(customer_insert_query, 'post', conn)

                        print('INSERT')

                        if item['code'] != 281:
                            item['message'] = 'Check insert sql query'
                            return item

                        return redirect("http://localhost:3000/socialsignup?id=" + NewUserID)

                    # Existing customer

                    if items['result'][0]['user_refresh_token']:
                        print('user_refresh_token')
                        print(items['result'][0]['user_social_media'], items['result'][0]['user_refresh_token'])

                        if items['result'][0]['user_social_media'] != "GOOGLE":
                            print('Wrong sign up method')
                            items['message'] = "Wrong social media used for signup. Use \'" + items['result'][0]['user_social_media'] + "\'."
                            items['code'] = 400
                            return redirect("http://localhost:3000/?media=" + items['result'][0]['user_social_media'])

                        elif items['result'][0]['user_refresh_token'] != sub:
                            print('ID mismatch')
                            items['message'] = "ID mismatch"
                            items['code'] = 400
                            return redirect("http://localhost:3000/")

                        else:
                            print('Successfully authenticated with google redirecting.......')
                            return redirect("http://localhost:3000/users?id=" + items['result'][0]['user_uid'])

                else:
                    items['message'] = "Email not returned by GOOGLE LOGIN"
                    items['code'] = 400
                    return items


            else:
                response = {
                    "message": "Google ID token does not exist",
                    "code": 400
                }
                return response
        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)



class UpdateFavoritesParam(Resource):
    def post(self, favorites):
            response = {}
            items = []
            print("favorites", favorites)
            try:
                conn = connect()
                query = """
                        UPDATE ar.users
                        SET favorites = \'""" + favorites + """\'
                        WHERE user_uid = '100-000001';
                        """
                items = execute(query, 'post', conn)
                items['message'] = 'Favorites info updated'
                items['code'] = 200
                return items
            except:
                print("Error happened while updating users table")
                raise BadRequest('Request failed, please try again later.')
            finally:
                disconnect(conn)
                print('process completed')

class UpdateFavoritesParamJSON(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            user_uid = data['user_uid']
            favorites = data['favorites']
            print("user_uid", user_uid)
            print("favorites", favorites)
            query = """
                    UPDATE ar.users
                    SET favorites = \'""" + favorites + """\'
                    WHERE user_uid = \'""" + user_uid + """\';
                    """
            items = execute(query, 'post', conn)
            response['message'] = 'JSON POST successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('JSON POST Request failed, please try again later.')
        finally:
            disconnect(conn)

        # {
        #     "user_uid":"100-000001",
        #     "favorites":"testinggg"
        # }


class InsertNewBook(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()

            data = request.get_json(force = True)
            
            title = data['title']
            book_cover_base64 = data['book_cover_image']
            author_uid = data['author_uid']
            genre = data['genre']
            num_pages = data['num_pages']
            description = data['description']
            book_format = data['format']
            book_link = data['book_link']

            NewBookUIDQuery = execute('CALL get_book_uid;', 'get', conn)
            NewBookUID = NewBookUIDQuery['result'][0]['new_id']

            book_cover_link = image_s3_upload(book_cover_base64, title)
            book_link_pdf = book_s3_upload(book_link, title)

            query = """INSERT INTO ar.books (book_uid
                                            , title
                                            , book_cover_image
                                            , author_uid
                                            , genre
                                            , num_pages
                                            , description
                                            , format
                                            , book_link)
                                    VALUES( \'""" + NewBookUID + """\'
                                            ,\'""" + title + """\'
                                            ,\'""" + book_cover_link + """\'
                                            ,\'""" + author_uid + """\'
                                            ,\'""" + genre + """\'
                                            ,\'""" + num_pages + """\'
                                            ,\'""" + description + """\'
                                            ,\'""" + book_format + """\'
                                            ,\'""" + book_link_pdf + """\');"""
            
            items = execute(query, 'post', conn)

            response['message'] = 'Successfully inserted a new book'
            response['result'] = items

            return response, 200
        except:
            raise BadRequest('Bad request, error while inserting new book')
        finally:
            disconnect(conn)
        
        #https://ls802wuqo5.execute-api.us-west-1.amazonaws.com/dev/api/v2/InsertNewBook
        {
            "title":"test",
            "book_cover_image":"needs to be base64 string",
            "author_uid":"100-000002",
            "genre":"None",
            "num_pages":"10000000000",
            "description":"testing",
            "format":"paper",
            "book_link":"blah"
        }

class InsertNewUser(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()

            data = request.get_json(force = True)

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            role = data['role']
            email = data['email']
            phone = data['phone']
            interest = data['interest']
            hours = data['hours']
            favorites = data['favorites']

            NewUserUIDQuery = execute('CALL get_user_uid;', 'get', conn)
            NewUserUID = NewUserUIDQuery['result'][0]['new_id']

            query = """INSERT INTO ar.users (user_uid
                                            , username
                                            , first_name
                                            , last_name
                                            , role
                                            , email
                                            , phone
                                            , interest
                                            , hours
                                            , favorites)
                                        VALUES(\'""" + NewUserUID + """\'
                                                ,\'""" + username + """\'
                                                ,\'""" + first_name + """\'
                                                ,\'""" + last_name + """\'
                                                ,\'""" + role + """\'
                                                ,\'""" + email + """\'
                                                ,\'""" + phone + """\'
                                                ,\'""" + interest + """\'
                                                ,\'""" + hours + """\'
                                                ,\'""" + favorites + """\');"""

            items = execute(query, 'post', conn)

            response['message'] = 'Successfully inserted new user'
            response['result'] = items

            return response, 200
        except:
            raise BadRequest('Bad request, error while inserting new user')
        finally:
            disconnect(conn)

        #https://ls802wuqo5.execute-api.us-west-1.amazonaws.com/dev/api/v2/InsertNewUser
        # {
        #     "username":"test",
        #     "first_name":"te",
        #     "last_name":"st",
        #     "role":"author",
        #     "email":"test",
        #     "phone":"33333333",
        #     "interest":"test",
        #     "hours":"1000",
        #     "favorites":"test"
        # }

class InsertNewReview(Resource):
    def post(self):
        response = {}
        items = {}
        try: 
            conn = connect()

            data = request.get_json(force = True)

            rev_book_uid = data['rev_book_uid']
            reader_id = data['reader_id']
            comments = data['comments']
            rating_title = data['rating_title']
            rating_content = data['rating_content']

            NewReviewUIDQuery = execute('CALL get_review_uid;', 'get', conn)
            NewReviewUID = NewReviewUIDQuery['result'][0]['new_id']

            query = """INSERT INTO ar.reviews (review_uid
                                               , rev_book_uid
                                               , reader_id  
                                               , comments 
                                               , rating_title
                                               , rating_content)
                                        VALUES(\'""" + NewReviewUID + """\'
                                               , \'""" + rev_book_uid + """\'
                                               , \'""" + reader_id + """\'
                                               , \'""" + comments + """\'
                                               , \'""" + rating_title + """\'
                                               , \'""" + rating_content + """\');"""

            items = execute(query, 'post', conn)

            response['message'] = 'Successfully inserted new review'
            response['result'] = items

            return response, 200
        except:
            raise BadRequest('Bad request, error while inserting new review')
        finally:
            disconnect(conn)

    #https://ls802wuqo5.execute-api.us-west-1.amazonaws.com/dev/api/v2/InsertNewReview
    # {
    #     "rev_book_uid":"200-000020",
    #     "reader_id":"100-000018",
    #     "comments":"test",
    #     "rating_title":"test",
    #     "rating_content":"test"
    # }


#----------------------------------------------------------------------------------


# Define API routes

# Gets
api.add_resource(AllBooks, '/api/v2/AllBooks')
api.add_resource(AllUsers, '/api/v2/AllUsers')
api.add_resource(AllAuthors, '/api/v2/AllAuthors')
api.add_resource(AllReaders, '/api/v2/AllReaders')
api.add_resource(BooksByAuthorEmail, '/api/v2/BooksByAuthorEmail/<string:user_email>')
api.add_resource(BooksByAuthorUID, '/api/v2/BooksByAuthorUID/<string:author_uid>')
api.add_resource(BooksByName, '/api/v2/BooksByName/<string:first_name>/<string:last_name>')
api.add_resource(ReviewByUser, '/api/v2/ReviewByUser')
api.add_resource(ReviewByBook, '/api/v2/ReviewByBook/<string:review_uid>')
api.add_resource(ReivewByBookTitle, '/api/v2/ReviewByBookTitle/<string:book_title>')
api.add_resource(ReivewByBookUID, '/api/v2/ReviewByBookUID/<string:book_uid>')
api.add_resource(OneUserArg, '/api/v2/OneUserArg/<string:user_uid>')
api.add_resource(BooksUnderUser, '/api/v2/BooksUnderUser') 
api.add_resource(AuthorForEachBook, '/api/v2/AuthorForEachBook')

#Sign Up
api.add_resource(SignUp, '/api/v2/SignUp')
api.add_resource(AccountSalt, '/api/v2/AccountSalt')
api.add_resource(Login, '/api/v2/Login')
api.add_resource(AppleLogin, '/api/v2/AppleLogin', '/')
api.add_resource(GoogleLogin, '/api/v2/GoogleLogin', '/')

#Updates 
api.add_resource(UpdateFavoritesParam, '/api/v2/UpdateFavoritesParam/<string:favorites>')   
api.add_resource(UpdateFavoritesParamJSON, '/api/v2/UpdateFavoritesParamJSON')
api.add_resource(InsertNewBook, '/api/v2/InsertNewBook')
api.add_resource(InsertNewUser, '/api/v2/InsertNewUser')
api.add_resource(InsertNewReview, '/api/v2/InsertNewReview')



# Run on below IP address and port
# Make sure port number is unused (i.e. don't use numbers 0-1023)   
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000)
