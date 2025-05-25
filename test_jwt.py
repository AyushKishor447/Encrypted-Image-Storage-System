from dotenv import load_dotenv
load_dotenv()
import os
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
print(JWT_SECRET_KEY)


