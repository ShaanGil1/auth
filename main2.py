import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from authlib.jose import JsonWebToken, jwk
from authlib.jose.errors import JoseError
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
# Azure GovCloud Configuration
TENANT_ID = "<tenant-id>"
API_CLIENT_ID = "api://<client-id>"
REQUIRED_SCOPE = "access_as_user"
DISCOVERY_URL = f"https://login.microsoftonline.us/{TENANT_ID}/v2.0/.well-known/openid-configuration"
jwt_obj = JsonWebToken(["RS256"])

# ──────────────────────────────────────────────────────────────────────────
# Discovery + JWKS helpers
@lru_cache()
def get_discovery_doc():
    resp = requests.get(DISCOVERY_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

@lru_cache()
def get_jwks():
    jwks_uri = get_discovery_doc()["jwks_uri"]
    resp = requests.get(jwks_uri, timeout=10)
    resp.raise_for_status()
    return resp.json()["keys"]

bearer_scheme = HTTPBearer(auto_error=False)

# ──────────────────────────────────────────────────────────────────────────
# Authlib-based token validator
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
        header = jwt_obj.peek_header(token)
        kid = header.get("kid")
        keys = get_jwks()

        signing_key = None
        for key in keys:
            if key.get("kid") == kid:
                signing_key = jwk.loads(key)
                break

        if signing_key is None:
            print("❌ No matching signing key found")
            raise HTTPException(status_code=401, detail="Invalid token key")

        claims = jwt_obj.decode(token, signing_key)
        claims.validate(
            aud=API_CLIENT_ID,
            iss=get_discovery_doc()["issuer"],
        )

        print("✅ Token decoded successfully")
        print("📦 JWT Payload:", claims)

        scopes = claims.get("scp", "")
        print(f"🔍 Token scopes: {scopes}")
        if REQUIRED_SCOPE not in scopes.split():
            print(f"🚫 Required scope '{REQUIRED_SCOPE}' not found in token scopes")
            raise HTTPException(status_code=403, detail="Missing required scope")

        return claims

    except JoseError as e:
        print(f"❌ Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Token invalid")

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
