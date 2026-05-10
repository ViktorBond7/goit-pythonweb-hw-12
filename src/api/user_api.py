from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
    Response,
    BackgroundTasks,
    UploadFile,
    File,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.limiter import limiter
from src.models.user import User
from src.schemas.user import (
    TokenModel,
    UserRead,
    UserCreate,
    RequestEmail,
    RequestPasswordReset,
    ResetPassword,
)
from src.db.session import open_session
from src.services import user_service
from src.services.auth import (
    get_current_user,
    get_email_from_token,
    get_current_admin_user,
    get_email_from_reset_token,
)
from src.services.email import send_email, send_reset_password_email
from src.services.upload_file import UploadFileService
from src.config.app_config import settings

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(open_session),
):
    create_user = await user_service.create_user(db, user)
    background_tasks.add_task(
        send_email, create_user.email, create_user.username, request.base_url
    )

    return UserRead.model_validate(create_user)


@router.post("/login", response_model=TokenModel)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(open_session),
):
  
    return await user_service.authenticate_user(db, form_data)


@router.get("/me", response_model=UserRead)
@limiter.limit("5/minute")
async def read_current_user(
    request: Request, current_user: User = Depends(get_current_user)
):

    return UserRead.model_validate(current_user)


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(open_session)):
    email = await get_email_from_token(token)
    user = await user_service.get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Email is already confirmed."}
    await user_service.confirmed_email(email, db)
    return {"message": "Email has been confirmed."}


@router.post("/request_email", status_code=status.HTTP_200_OK)
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(open_session),
):

    user = await user_service.get_user_by_email(db, body.email)

    if user and user.confirmed:
        return {"message": "Our email is already confirmed."}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for confirmation."}


@router.post("/refresh", response_model=TokenModel, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    refresh_token: str = Form(...), db: AsyncSession = Depends(open_session)
):
    return await user_service.refresh_token_service(refresh_token)


@router.post("/request_password_reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    body: RequestPasswordReset,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(open_session),
):
    user = await user_service.get_user_by_email(db, body.email)
    
    if user and user.confirmed:
        background_tasks.add_task(
            send_reset_password_email,
            user.email,
            user.username,
            request.base_url,
        )
    
    return {"message": "If the account exists, password reset instructions were sent."}


@router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPassword,
    db: AsyncSession = Depends(open_session),
):
    email = await get_email_from_reset_token(body.token)
    await user_service.reset_password(email, body.new_password, db)
    return {"message": "Password has been reset successfully."}


@router.patch("/avatar", response_model=UserRead)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(open_session),
):
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user = await user_service.update_avatar_url(user.email, avatar_url, db)

    return user


