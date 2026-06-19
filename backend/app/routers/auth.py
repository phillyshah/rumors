from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.auth import create_token, get_current_user_id, hash_password, verify_password
from app.models.user import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, request: Request):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = hash_password(body.password)
        row = await conn.fetchrow(
            """INSERT INTO users (email, display_name, hashed_password, region)
               VALUES ($1, $2, $3, $4)
               RETURNING id, email, display_name, region, is_admin, created_at""",
            body.email, body.display_name, hashed, body.region,
        )
    user = UserResponse(**dict(row))
    token = create_token(user.id)
    return TokenResponse(token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, request: Request):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, display_name, region, is_admin, created_at, hashed_password FROM users WHERE email = $1",
            body.email,
        )
    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = UserResponse(
        id=row["id"], email=row["email"], display_name=row["display_name"],
        region=row["region"], is_admin=row["is_admin"], created_at=row["created_at"],
    )
    token = create_token(user.id)
    return TokenResponse(token=token, user=user)


@router.get("/me", response_model=UserResponse)
async def me(request: Request, user_id: int = Depends(get_current_user_id)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, display_name, region, is_admin, created_at FROM users WHERE id = $1",
            user_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**dict(row))
