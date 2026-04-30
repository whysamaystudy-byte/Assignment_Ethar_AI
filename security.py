from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "13553467589" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    # Calculate expiration time
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # FIX 1: Convert expire to Unix timestamp and include 'sub' claim
    to_encode.update({
        "exp": expire.timestamp(), # Use timestamp format
        "sub": str(data.get("user_id")) # Use 'sub' claim for user ID (from the expected data)
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, credentials_exception: Any) -> int:
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # We expect the user ID to be stored under the 'sub' claim
        user_id_str: str = payload.get("sub") 
        
        if user_id_str is None:
            # Token is valid but missing the user ID claim
            raise credentials_exception
            
        return int(user_id_str)
        
    except (JWTError, ValueError):
        # Catches JWT errors (expired, invalid signature) and ValueError if 'sub' isn't convertible to int
        raise credentials_exception