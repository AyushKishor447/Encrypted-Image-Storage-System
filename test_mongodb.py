from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
load_dotenv()
# uri = "mongodb+srv://Admin:oI9iuf9fN4I1CS4o@ess-database.h7aiwa6.mongodb.net/?retryWrites=true&w=majority&appName=ESS-DATABASE"
uri = os.getenv("MONGO_URI")
print(uri)
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)