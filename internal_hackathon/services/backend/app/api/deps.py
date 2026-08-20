from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # For Supabase, the JWT secret is needed here. 
        # Using a placeholder 'your-supabase-jwt-secret' for now, should be in config.
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'], options={"verify_aud": False})
        user_id: str = payload.get('sub')
        role: str = payload.get('role', 'authenticated')
        if user_id is None:
            raise HTTPException(status_code=401, detail='Invalid authentication credentials')
        return {'user_id': user_id, 'role': role}
    except JWTError:
        raise HTTPException(status_code=401, detail='Could not validate credentials')

def require_officer_role(user: dict = Depends(get_current_user)):
    if user.get('role') != 'officer' and user.get('role') != 'service_role':
        raise HTTPException(status_code=403, detail='Not enough permissions')
    return user

