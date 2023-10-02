from fastapi import FastAPI, UploadFile, HTTPException,Response
from pydantic import BaseModel
import psycopg2
from pymongo import MongoClient
from bson.binary import Binary
import uuid

# creating the instance for the fastapi class
app = FastAPI()

# Connect to PostgreSQL database
conn_postgres = psycopg2.connect(
    dbname="registration",
    user="postgres",
    password="ragh",
    host="localhost",
    port="5432"
)
cursor_postgres = conn_postgres.cursor()

# Connect to Mongodb database
client_mongo = MongoClient("mongodb://localhost:27017")
db_mongo = client_mongo["test_db"]
collection_mongo = db_mongo["images"]

# Defining the pydantic models
class UserRegistration(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str

# creating the endpoint for registering the user details in postgresql db
@app.post("/register/")
def register_user(user: UserRegistration):
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # creating the table in postgreSQL db
    cursor_postgres.execute("CREATE TABLE IF NOT EXISTS users(user_id VARCHAR, full_name VARCHAR, email VARCHAR, password VARCHAR, phone VARCHAR)")
   
    # Check if email exists in PostgreSQL
    cursor_postgres.execute("SELECT * FROM users WHERE email = %s;", (user.email))
    existing_user = cursor_postgres.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with email is already exists")

    # Insert user details into PostgreSQL Users table with the generated user_id
    cursor_postgres.execute(
        "INSERT INTO users (user_id, full_name, email, password, phone) VALUES (%s, %s, %s, %s, %s);",
        (user_id, user.full_name, user.email, user.password, user.phone)
    )
    conn_postgres.commit()

    return {"message": "User registered successfully"}

# creating the endpoint for uploading the profile of the user in Mongo db
@app.post("/upload/")
def upload_image(file: UploadFile, user_id: str):
    # Read the file content
    image_binary = file.file.read()

    # Store the image in MongoDB along with user id
    image_data = {"user_id": user_id, "filename": file.filename,  "image": Binary(image_binary)}
    result = collection_mongo.insert_one(image_data)

    return {"message": "Image uploaded successfully"}

# creating the endpoint for getting the user details by giving user id from postgreSQL db
@app.get("/user_details/{user_id}")
def get_user(user_id: str):
    # Fetch user details from PostgreSQL
    cursor_postgres.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    user_data_postgres = cursor_postgres.fetchone()
    if not user_data_postgres:
        raise HTTPException(status_code=404, detail="User not found in PostgreSQL")
    
    user_details = {
        "user_id": user_data_postgres[0],
        "name": user_data_postgres[1],
        "email": user_data_postgres[2],
        "phone": user_data_postgres[4],
    } 
    return user_details

# creating the endpoint for getting the profile picture of the specific user by giving user id from the mongo db
@app.get("/user_profile/{user_id}")
def get_profile(user_id: str):
        # Find the document with the specified user ID
    document = collection_mongo.find_one({"user_id": user_id})

    if document and "image" in document:
            # Get the image data from the document
            image_data = document["image"]

            # Set the content type to image/jpeg (adjust based on your image format)
            headers = {"Content-Type": "image/jpeg"}

            # Return the image data as the response
            return Response(content=image_data, headers=headers)
    else:

           return {"message": "Image not found for the specified user ID"}


# creating the endpoint for getting all the user details 
@app.get("/get_all_user_details/")
def get_all_details():
     
     cursor_postgres.execute("SELECT * FROM users")
     users_info = cursor_postgres.fetchall();
     return users_info
