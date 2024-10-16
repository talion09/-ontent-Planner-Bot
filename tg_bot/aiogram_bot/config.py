from dataclasses import dataclass
from pathlib import Path

from environs import Env

I18N_DOMAIN = "harvest_bot"
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / "locales"


@dataclass
class TgBot:
    token: str
    admin_ids: int


@dataclass
class Db:
    db_user: str
    db_pass: str
    db_name: str
    db_host: str
    db_port: str


@dataclass
class Api:
    api_db: str
    api_db_port: int

    api_payment: str
    api_payment_port: int

    api_chat_gpt: str
    api_chat_gpt_port: int

    api_mail: str
    api_mail_port: int


@dataclass
class Paywave:
    prefix: str
    pass1: str
    system:str


@dataclass
class Config:
    tg_bot: TgBot
    db: Db
    api: Api
    paywave: Paywave


def load_config():
    env = Env()
    env.read_env()

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=env.int("ADMINS")
        ),
        db=Db(
            db_user=env.str("DB_USER"),
            db_pass=env.str("DB_PASS"),
            db_name=env.str("DB_NAME"),
            db_host=env.str("DB_HOST"),
            db_port=env.str("DB_PORT")
        ),
        api=Api(
            api_db=env.str("API_DB"),
            api_db_port=env.str("API_DB_PORT"),
            api_payment=env.str("API_PAYMENT"),
            api_payment_port=env.str("API_PAYMENT_PORT"),
            api_chat_gpt=env.str("API_CHAT_GPT"),
            api_chat_gpt_port=env.str("API_CHAT_GPT_PORT"),
            api_mail=env.str("API_MAIL"),
            api_mail_port=env.str("API_MAIL_PORT")
        ),
        paywave=Paywave(
            prefix=env.str("PAYWAVE_PREFIX"),
            pass1=env.str("PAYWAVE_PASS1"),
            system=env.str("PAYWAVE_SYSTEM")
        )
    )
