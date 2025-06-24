import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

app = FastAPI(title="Azure-AD protected API with FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ──────────────────────────────────────────────────────────────────────────
# FastAPI app to protect with Azure AD
TENANT_ID = "<tenant-id>"  # Replace with your Azure AD tenant ID
API_CLIENT_ID = "api://<client-id>"
REQUIRED_SCOPE = "access_as_user"
ISSUER = f"https://sts.windows.net/{TENANT_ID}/"
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

bearer_scheme = HTTPBearer(auto_error=False)

@lru_cache()
def get_jwks():
    resp = requests.get(JWKS_URI, timeout=10)
    resp.raise_for_status()
    return resp.json()

async def verify_token(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict:
    if creds is None:
        print("🔒 No Authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials
    print(f"🔑 Received token (first 100 chars): {token[:100]}...")

    try:
        payload = jwt.decode(
            token,
            get_jwks(),
            algorithms=["RS256"],
            audience=API_CLIENT_ID,
            issuer=ISSUER,
            options={"verify_at_hash": False},  # skip optional hash check
        )

        print("✅ Token decoded successfully")
        print("📦 JWT Payload:", payload)

        # Validate required scope
        scopes = payload.get("scp", "")
        print(f"🔍 Token scopes: {scopes}")
        if REQUIRED_SCOPE not in scopes.split():
            print(f"🚫 Required scope '{REQUIRED_SCOPE}' not found in token scopes")
            raise HTTPException(status_code=403, detail="Missing required scope")

        return payload

    except ExpiredSignatureError:
        print("⏰ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTClaimsError as e:
        print(f"❌ Invalid claims: {e}")
        raise HTTPException(status_code=401, detail=f"Bad claims: {e}")
    except JWTError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Token invalid")


# ──────────────────────────────────────────────────────────────────────────
# FastAPI app + routes
# ──────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": int(time.time())}

@app.get("/protected")
def protected(payload: dict = Depends(verify_token)):
    """
    Example protected endpoint.
    Returns the caller's name & oid from the access token.
    """
    return {
        "message": f"Hello {payload.get('name', 'unknown')}!",
        "oid": payload.get("oid"),
        "issued_at": payload.get("iat")
    }

# ──────────────────────────────────────────────────────────────────────────
# Run:  uvicorn main:app --reload
# ──────────────────────────────────────────────────────────────────────────
