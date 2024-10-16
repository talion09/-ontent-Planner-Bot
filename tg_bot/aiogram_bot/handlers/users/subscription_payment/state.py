from aiogram.dispatcher.filters.state import StatesGroup, State


class SubscriptionPaymentState(StatesGroup):
    Get_Message = State()
    Change_Email = State()


class SubscriptionPaymentFreeState(StatesGroup):
    Get_Message = State()

class SubscriptionPaymentTrialState(StatesGroup):
    Get_Message = State()

