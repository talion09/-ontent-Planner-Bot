from aiogram.dispatcher.filters.state import StatesGroup, State


class Parsing(StatesGroup):
    Link = State()
    DateRangePickerStart = State()
    DateRangePickerEnd = State()


class Settings(StatesGroup):
    Sign = State()
    Add_prompt = State()
    GPT4 = State()
    Change_prompt = State()


class Create(StatesGroup):
    Get_Message = State()
    Get_Description = State()
    Get_URL = State()
    Add_Media = State()
    Replace_Media = State()
    Sign = State()
    AddPrompt = State()
    GeneratePrompt = State()


class Content(StatesGroup):
    Get_Message = State()
    Get_Description = State()
    Get_URL = State()
    Edit_Media = State()


class CreatePost(StatesGroup):
    Message_Is_Channel = State()


class Admins(StatesGroup):
    Get_Message = State()
    Get_URL = State()


class User(StatesGroup):
    Lang = State()
    Next = State()

