from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import re
from typing import Dict
from config import settings

security = HTTPBearer()

# Try to extract Supabase project ref from DATABASE_URL to build JWKS URL
project_ref_match = re.search(r"@db\.([^.]+)\.supabase\.co", settings.DATABASE_URL)
project_ref = project_ref_match.group(1) if project_ref_match else None
jwks_url = f"https://{project_ref}.supabase.co/rest/v1/jwks" if project_ref else None
jwks_client = PyJWKClient(jwks_url) if jwks_url else None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")

        if alg == "RS256" and jwks_client:
            # RS256 (Asymmetric JWT) used in newer Supabase projects
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
        else:
            # Fallback to HS256/HS384/HS512 (Symmetric JWT)
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256", "HS384", "HS512"],
                options={"verify_aud": False}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        import logging
        alg_val = alg if 'alg' in locals() else "unknown"
        logging.error(f"JWT Validation Error: {e} (Token alg: {alg_val})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
