import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import jwt  # PyJWT
from jwt import PyJWKClient, InvalidTokenError

app = FastAPI(title="Azure-AD protected API with FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────
# Azure GovCloud Configuration
TENANT_ID = "<tenant-id>"
API_CLIENT_ID = "api://<client-id>"
REQUIRED_SCOPE = "access_as_user"
DISCOVERY_URL = f"https://login.microsoftonline.us/{TENANT_ID}/v2.0/.well-known/openid-configuration"

# ──────────────────────────────────────────────────────────────────────────
@lru_cache()
def get_discovery_doc():
    resp = requests.get(DISCOVERY_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

@lru_cache()
def get_jwk_client():
    jwks_uri = get_discovery_doc()["jwks_uri"]
    return PyJWKClient(jwks_uri)

bearer_scheme = HTTPBearer(auto_error=False)

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
        # Automatically fetch and match correct JWK key by 'kid'
        signing_key = get_jwk_client().get_signing_key_from_jwt(token).key

        # Validate token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=API_CLIENT_ID,
            issuer=get_discovery_doc()["issuer"]
        )

        print("✅ Token decoded successfully")
        print("📦 JWT Payload:", payload)

        scopes = payload.get("scp", "")
        print(f"🔍 Token scopes: {scopes}")
        if REQUIRED_SCOPE not in scopes.split():
            print(f"🚫 Required scope '{REQUIRED_SCOPE}' not found in token scopes")
            raise HTTPException(status_code=403, detail="Missing required scope")

        return payload

    except InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Token invalid or expired")

# ──────────────────────────────────────────────────────────────────────────
# Routes
@app.get("/health")
def health():
    return {"status": "ok", "time": int(time.time())}

@app.get("/protected")
def protected(payload: dict = Depends(verify_token)):
    return {
        "message": f"Hello {payload.get('name', 'unknown')}!",
        "oid": payload.get("oid"),
        "issued_at": payload.get("iat")
    }
