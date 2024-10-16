from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select

from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.parsing_source.models import ParsingSource
from api_service.payment.models import Payment
from api_service.post.models import Post
from api_service.user.dao import UserDao
from api_service.user_channel.models import UserChannel
from api_service.user_channel_settings.models import UserChannelSettings


class AdminStatisticsDao(BaseDao):

    @classmethod
    def generate_user_categories(cls, activity, renewal_status, duration_categories):
        return {f"{activity}{renewal_status}{duration}" for duration in duration_categories}

    @classmethod
    async def statistics(cls):
        # ОБЩАЯ АУДИТОРИЯ
        users_quantity = await UserDao.count_all()

        current_date = datetime.utcnow().date()

        async with async_session_maker() as session:
            # КОЛ_ВО ПОДПИСОК
            # FREE
            result = await session.execute(
                select(func.count(UserChannelSettings.id))
                .where(UserChannelSettings.subscription_id == 1)
            )
            free_subscriptions_quantity = result.scalar()

            #PREMIUM
            result = await session.execute(
                select(func.count(UserChannelSettings.id))
                .where(UserChannelSettings.subscription_id == 2)
            )
            premium_subscriptions_quantity = result.scalar()

            # АКТИВНЫ ЗА ПОСЛЕДНИЕ 24 ЧАСА
            # FREE
            result = await session.execute(
                select(func.count(func.distinct(Post.user_id)))
                .join(UserChannel, Post.channel_id == UserChannel.channel_id)
                .join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id)
                .where(
                    UserChannelSettings.subscription_id == 1,
                    func.date(Post.date) == current_date
                )
            )
            active_user_quantity_free = result.scalar()

            # PREMIUM
            result = await session.execute(
                select(func.count(func.distinct(Post.user_id)))
                .join(UserChannel, Post.channel_id == UserChannel.channel_id)
                .join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id)
                .where(
                    UserChannelSettings.subscription_id == 2,
                    func.date(Post.date) == current_date
                )
            )
            active_user_quantity_premium = result.scalar()

            # ИСПОЛЬЗОВАНИЕ ПРОДУКТА
            current_date = datetime.utcnow()
            start_date = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + relativedelta(months=+1)

            # FREE
            result = await session.execute(
                select(
                    Post.user_id,
                    func.count(Post.id).label('post_count')
                ).join(
                    UserChannel,
                    Post.channel_id == UserChannel.channel_id
                ).join(
                    UserChannelSettings,
                    UserChannel.user_channel_settings_id == UserChannelSettings.id
                ).filter(
                    Post.date >= start_date,
                    Post.date < end_date,
                    UserChannelSettings.subscription_id == 1
                ).group_by(
                    Post.user_id
                )
            )
            posts_data_free = result.all()

            user_activity_free = {}
            for user_id, post_count in posts_data_free:
                if post_count >= 30:
                    category = 1  # Постоянное использование
                elif 15 <= post_count < 30:
                    category = 2  # Периодическое использование
                else:
                    category = 3  # Редкое использование
                user_activity_free[user_id] = category

            category_free_counts = {
                'constant_active': 0,
                'leaving': 0,
                'sleeping': 0
            }

            for classifications in user_activity_free.values():
                if classifications == 1:
                    category_free_counts['constant_active'] += 1
                if classifications == 2:
                    category_free_counts['leaving'] += 1
                if classifications == 3:
                    category_free_counts['sleeping'] += 1

            # PREMIUM
            result = await session.execute(
                select(
                    Post.user_id,
                    func.count(Post.id).label('post_count')
                ).join(
                    UserChannel,
                    Post.channel_id == UserChannel.channel_id
                ).join(
                    UserChannelSettings,
                    UserChannel.user_channel_settings_id == UserChannelSettings.id
                ).filter(
                    Post.date >= start_date,
                    Post.date < end_date,
                    UserChannelSettings.subscription_id == 2
                ).group_by(
                    Post.user_id
                )
            )
            posts_data_premium = result.all()

            user_activity_premium = {}
            for user_id, post_count in posts_data_premium:
                if post_count >= 30:
                    category = 1  # Постоянное использование
                elif 15 <= post_count < 30:
                    category = 2  # Периодическое использование
                else:
                    category = 3  # Редкое использование
                user_activity_premium[user_id] = category

            # ПРОДЛЕНИЕ
            # ТОЛЬКО ДЛЯ PREMIUM
            result = await session.execute(
                select(
                    Payment.user_id,
                    func.count(Payment.id).label('purchase_count')
                ).group_by(
                    Payment.user_id
                )
            )
            purchase_data = result.all()

            user_renewal_status = {}
            for user_id, purchase_count in purchase_data:
                if purchase_count > 1:
                    status = 1  # Было продление
                elif purchase_count == 1:
                    status = 2  # Первая покупка
                else:
                    status = 3  # Не было продления
                user_renewal_status[user_id] = status

            # СРОК ПРОДЛЕНИЯ
            result = await session.execute(
                select(
                    Payment.user_id,
                    Payment.duration
                )
            )
            payments = result.all()

            user_duration_categories = {}
            for user_id, duration in payments:
                if duration in [6, 12]:
                    category = 1  # Длинный срок
                elif duration == 3:
                    category = 2  # Средний срок
                elif duration == 1:
                    category = 3  # Минимальный срок
                else:
                    continue

                if user_id in user_duration_categories:
                    user_duration_categories[user_id].add(category)
                else:
                    user_duration_categories[user_id] = {category}

        common_user_ids = set(user_activity_premium.keys()) & set(user_renewal_status.keys()) & set(
            user_duration_categories.keys())

        final_user_classification = {}
        for user_id in common_user_ids:
            activity = user_activity_premium[user_id]
            renewal_status = user_renewal_status[user_id]
            duration_categories = user_duration_categories[user_id]

            user_categories = cls.generate_user_categories(activity, renewal_status, duration_categories)
            classifications = set()

            for category in user_categories:
                if category in ['331', '332', '333', '321', '322', '323', '311', '312', '313']:
                    classifications.add('leaving')
                if category in ['221', '222', '223', '231', '232', '233', '213', '212', '211']:
                    classifications.add('sleeping')
                if category in ['131', '132', '133', '121', '122', '123', '111', '112', '113']:
                    classifications.add('constant_active')

            final_user_classification[user_id] = classifications

        category_counts = {
            'constant_active': 0,
            'leaving': 0,
            'sleeping': 0
        }

        for classifications in final_user_classification.values():
            if 'constant_active' in classifications:
                category_counts['constant_active'] += 1
            if 'leaving' in classifications:
                category_counts['leaving'] += 1
            if 'sleeping' in classifications:
                category_counts['sleeping'] += 1

        result = await session.execute(
            select(ParsingSource.posts_quantity)
            .where(ParsingSource.type == "Telegram")
        )
        telegram_parsed_posts = result.scalar()

        data = {
            "users_quantity":users_quantity,
            "free_subscriptions_quantity": free_subscriptions_quantity,
            "free_subscription_rfm": category_free_counts,
            "active_user_quantity_free": active_user_quantity_free,
            "premium_subscriptions_quantity": premium_subscriptions_quantity,
            "premium_subscription_rfm": category_counts,
            "active_user_quantity_premium": active_user_quantity_premium,
            "telegram_parsed_posts":telegram_parsed_posts
        }
        return data
