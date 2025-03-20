from fastapi_mail import ConnectionConfig


SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

SMTP = ConnectionConfig(
    MAIL_USERNAME = "gajnetdinov333@gmail.com",
    MAIL_PASSWORD = "zfhvzcdgockrmwxu",
    MAIL_FROM = "gajnetdinov333@gmail.com",
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS  = False,
    MAIL_SSL_TLS = True,
    MAIL_FROM_NAME = "fileTrace"
)