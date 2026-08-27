from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import re
from typing import Dict
from config import settings

security = HTTPBearer()

jwks_clients: Dict[str, PyJWKClient] = {}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")

        if alg in ["RS256", "ES256"]:
            # Extract issuer to get the JWKS URL
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            iss = unverified_payload.get("iss")
            
            if not iss:
                raise HTTPException(status_code=401, detail="Missing issuer in token")
            
            if iss.endswith("/auth/v1"):
                jwks_url = iss.replace("/auth/v1", "/.well-known/jwks.json")
            else:
                jwks_url = f"{iss.rstrip('/')}/.well-known/jwks.json"

            # Cache the client to avoid repeated HTTP requests
            if jwks_url not in jwks_clients:
                jwks_clients[jwks_url] = PyJWKClient(jwks_url)
            
            jwks_client = jwks_clients[jwks_url]
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
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
