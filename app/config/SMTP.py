from pydantic import BaseModel

class Settings(BaseModel):
    MAIL_USERNAME = "алмаз",
    MAIL_PASSWORD = "Emilooo1",
    MAIL_FROM = "gajnetdinov333@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS  = True,
    MAIL_SSL_TLS = False,
    MAIL_FROM_NAME = "fileTrace"

settings = Settings()
