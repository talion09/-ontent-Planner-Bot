import asyncio
import json
import logging
import random
from collections import defaultdict
from datetime import datetime, timezone

import socks
from telethon import TelegramClient, events, types
from telethon.hints import TotalList
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Message

from telethon_bot.config import API_SERVICE_HOST, API_SERVICE_PORT, BOT_ID, API_ID, API_HASH, BOT_USERNAME
from telethon_bot.remote_api.api import Api
from telethon_bot.remote_api.channel_for_parsing_association_api import ChannelForParsingAssociationApi
from telethon_bot.remote_api.parsing_source import ParsingSourceApi
from telethon_bot.remote_api.response_dto import TelethonUserDto, Response, JoinToChannelDto, GetPostsDto, \
    ChannelForParsingAssociationSchema, GetPostsByDateDto, UserSchema
from telethon_bot.remote_api.user_api import UserApi

remote_api = Api(base_url=f"http://{API_SERVICE_HOST}:{API_SERVICE_PORT}/telethon")
channel_for_parsings_association_api = ChannelForParsingAssociationApi()
parsing_source_api = ParsingSourceApi()
user_api = UserApi()

json_telethon_users = {}
logging.basicConfig(level=logging.INFO)


async def message_handler(event: events.NewMessage.Event):
    # if event.message.message == "stop":
    #     client: TelegramClient = json_telethon_users[f'{USER_BOT_ID}']['client']
    #     client.disconnect()

    if not event.grouped_id:
        if type(event.message.peer_id) is types.PeerUser:
            await handle_message_from_harvester_bot(user_id=event.message.peer_id.user_id,
                                                    message=event.message.message)
        elif type(event.message.peer_id) is types.PeerChannel:
            await handle_message_from_channel(channel_id=event.message.peer_id.channel_id, message=event.message)


async def message_album_handler(event: events.Album.Event):
    response: Response[TelethonUserDto] = Response[TelethonUserDto].model_validate(
        await remote_api.post(endpoint="user/find", data={'active': True})
    )
    user_bot_id: int = response.data.user_id

    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']

    media_group = event.messages
    caption = ""

    for i in event.messages:
        caption += i.message

    if type(media_group[0].peer_id) is types.PeerChannel:
        data = {
            "parser_channel_id": media_group[0].peer_id.channel_id
        }
        await client.send_file(int(BOT_ID), media_group, caption=caption + "\n\n" + json.dumps(data))

        parsing_source_response = await parsing_source_api.get_one_by_key_value(params={"key": "id", "value": 1})
        await parsing_source_api.put(data={
            "id": 1,  # TELEGRAM
            "posts_quantity": parsing_source_response['data']['posts_quantity'] + 1
        })


async def handle_message_from_harvester_bot(user_id: int, message: str):
    if user_id == int(BOT_ID):
        json_data = json.loads(message)
        message = json_data['message']

        if message == "Join to channel":
            join_to_channel_dto: JoinToChannelDto = JoinToChannelDto.model_validate(json_data)
            await subscribe_to_channel(join_to_channel_dto=join_to_channel_dto)
        elif message == "Get posts length":
            get_posts_dto: GetPostsDto = GetPostsDto.model_validate(json_data)
            await get_posts_length(get_posts_dto=get_posts_dto)
        elif message == "Get posts":
            get_posts_dto: GetPostsDto = GetPostsDto.model_validate(json_data)
            await get_message_from_parser_channels(get_posts_dto=get_posts_dto)
        elif message == "Get posts by date":
            get_posts_by_date_dto: GetPostsByDateDto = GetPostsByDateDto.model_validate(json_data)
            await get_message_from_parser_channels_by_date(get_posts_by_date_dto=get_posts_by_date_dto)


async def handle_message_from_channel(channel_id: int, message: Message):
    response: Response[TelethonUserDto] = Response[TelethonUserDto].model_validate(
        await remote_api.post(endpoint="user/find", data={'active': True})
    )
    user_bot_id: int = response.data.user_id

    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']

    data = {
        "parser_channel_id": channel_id
    }
    message.message = message.message + "\n\n" + json.dumps(data)
    await client.send_message(entity=int(BOT_ID), message=message)

    parsing_source_response = await parsing_source_api.get_one_by_key_value(params={"key": "id", "value": 1})
    await parsing_source_api.put(data={
        "id": 1,  # TELEGRAM
        "posts_quantity": parsing_source_response['data']['posts_quantity'] + 1
    })


async def subscribe_to_channel(join_to_channel_dto: JoinToChannelDto):
    response: Response[TelethonUserDto] = Response[TelethonUserDto].model_validate(
        await remote_api.post(endpoint="user/find", data={'active': True})
    )
    user_bot_id: int = response.data.user_id

    user_id = join_to_channel_dto.user_id
    link = join_to_channel_dto.parser_link
    channel_id = join_to_channel_dto.channel_id

    response = await remote_api.get(endpoint=f"count_parser_channels/{user_bot_id}")
    subscribed_channels_count = response['data']

    if subscribed_channels_count < 500:
        await try_to_enter_the_channel(join_to_channel_dto=join_to_channel_dto, user_bot_id=user_bot_id)
    else:
        id: int = json_telethon_users[f'{user_bot_id}']['id']
        json_data: Response[TelethonUserDto] = await remote_api.get(endpoint=f"get_next_telethon_user/{id}")
        response: Response[TelethonUserDto] = Response[TelethonUserDto].parse_obj(json_data)

        join_to_channel_dto: JoinToChannelDto = JoinToChannelDto(user_id=user_id,
                                                                 link=link,
                                                                 channel_id=channel_id)
        await try_to_enter_the_channel(join_to_channel_dto=join_to_channel_dto, user_bot_id=response.data.user_id)


async def get_posts_length(get_posts_dto: GetPostsDto):
    channel_for_parsings_association_response: Response[ChannelForParsingAssociationSchema] = Response[
        ChannelForParsingAssociationSchema].model_validate(
        await channel_for_parsings_association_api.post_one(data={
            "id": get_posts_dto.channel_for_parsing_association_id
        })
    )

    response = await remote_api.get(
        endpoint=f"telethon_user_channel_association/{channel_for_parsings_association_response.data.channel_for_parsing_id}")
    user_bot_id = response['data']['user_id']
    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']

    parser_channel_entity = await client.get_entity(get_posts_dto.parser_link)
    messages: TotalList = await client.get_messages(
        entity=parser_channel_entity,
        limit=100,
        offset_date=datetime.now().astimezone(timezone.utc),
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0
    )

    compare_date = channel_for_parsings_association_response.data.last_time_view_posts_tapped.replace(
        tzinfo=timezone.utc)
    grouped_messages = defaultdict(list)

    for message in messages:
        if message.grouped_id:
            grouped_messages[message.grouped_id].append(message)
        else:
            grouped_messages[message.id].append(message)

    filtered_messages = [msg for msg in grouped_messages.values() if
                         msg[0].date > compare_date]

    channel_for_parsings_association_response: Response[ChannelForParsingAssociationSchema] = Response[
        ChannelForParsingAssociationSchema].model_validate(
        await channel_for_parsings_association_api.put(data={
            "id": get_posts_dto.channel_for_parsing_association_id,
            # "last_time_view_posts_tapped": datetime.utcnow().replace(tzinfo=None).isoformat(),
            "quantity_of_parsed_message": len(filtered_messages)
        })
    )

    data = {
        "id": get_posts_dto.channel_for_parsing_association_id
    }

    await send_message_to_bot(data=data, client=client, details="Get posts length")


async def get_message_from_parser_channels_by_date(get_posts_by_date_dto: GetPostsByDateDto):
    channel_for_parsings_association_response: Response[ChannelForParsingAssociationSchema] = Response[
        ChannelForParsingAssociationSchema].model_validate(
        await channel_for_parsings_association_api.post_one(data={
            "id": get_posts_by_date_dto.channel_for_parsing_association_id
        })
    )

    response = await remote_api.get(
        endpoint=f"telethon_user_channel_association/{channel_for_parsings_association_response.data.channel_for_parsing_id}")
    user_bot_id = response['data']['user_id']
    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']

    start_date = datetime.strptime(get_posts_by_date_dto.start_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(get_posts_by_date_dto.end_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    parser_channel_entity = await client.get_entity(get_posts_by_date_dto.parser_link)
    messages: TotalList = await client.get_messages(
        entity=parser_channel_entity,
        offset_date=start_date,
        reverse=True,
        wait_time=1
    )

    messages = messages[::-1]
    grouped_messages = defaultdict(list)

    for message in messages:
        if message.grouped_id:
            grouped_messages[message.grouped_id].append(message)
        else:
            grouped_messages[message.id].append(message)

    filtered_messages = []

    messages_list = list(grouped_messages.values())

    # Сортировка каждого списка сообщений в обратном порядке по дате
    for msg_list in messages_list:
        msg_list.sort(key=lambda x: x.date, reverse=True)

    # Теперь messages_list содержит списки сообщений, отсортированные в обратном порядке
    for msg_group in messages_list:
        for msg in msg_group:
            if msg.date < end_date:
                filtered_messages.append(msg_group)
            else:
                break

    data = {
        "channel_for_parsing_association_id": channel_for_parsings_association_response.data.id
    }

    message_count = 0
    for result in filtered_messages:
        if len(result) == 1:
            result[0].message = result[0].message + "\n\n" + json.dumps(data)
            message: Message = await client.send_message(entity=int(BOT_ID),
                                                         message=result[0])
            await asyncio.sleep(1.5)
        else:
            caption = ""
            for i in result:
                caption += i.message
            message: Message = await client.send_file(int(BOT_ID), result,
                                                      caption=caption + "\n\n" + json.dumps(data))
            await asyncio.sleep(1.5)

        user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.post_one(
            data={'id': channel_for_parsings_association_response.data.user_id}
        ))
        if user_response.data.parsing_stopped is not None:
            if user_response.data.parsing_stopped:
                user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.put(
                    data={
                        'id': channel_for_parsings_association_response.data.user_id,
                        'parsing_stopped': None
                    }
                ))
                break

        message_count += 1

    parsing_source_response = await parsing_source_api.get_one_by_key_value(params={"key": "id", "value": 1})
    await parsing_source_api.put(data={
        "id": 1,  # TELEGRAM
        "posts_quantity": parsing_source_response['data']['posts_quantity'] + message_count
    })


async def get_message_from_parser_channels(get_posts_dto: GetPostsDto):
    channel_for_parsings_association_response: Response[ChannelForParsingAssociationSchema] = Response[
        ChannelForParsingAssociationSchema].model_validate(
        await channel_for_parsings_association_api.post_one(data={
            "id": get_posts_dto.channel_for_parsing_association_id
        })
    )

    response = await remote_api.get(
        endpoint=f"telethon_user_channel_association/{channel_for_parsings_association_response.data.channel_for_parsing_id}")
    user_bot_id = response['data']['user_id']
    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']

    parser_channel_entity = await client.get_entity(get_posts_dto.parser_link)
    messages: TotalList = await client.get_messages(
        entity=parser_channel_entity,
        limit=100,
        offset_date=datetime.now().astimezone(timezone.utc),
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0
    )

    compare_date = channel_for_parsings_association_response.data.last_time_view_posts_tapped.replace(
        tzinfo=timezone.utc)
    messages = messages[::-1]
    grouped_messages = defaultdict(list)

    for message in messages:
        if message.grouped_id:
            grouped_messages[message.grouped_id].append(message)
        else:
            grouped_messages[message.id].append(message)

    filtered_messages = [msg for msg in grouped_messages.values() if
                         msg[0].date > compare_date]

    channel_for_parsings_association_response: Response[ChannelForParsingAssociationSchema] = Response[
        ChannelForParsingAssociationSchema].model_validate(
        await channel_for_parsings_association_api.put(data={
            "id": get_posts_dto.channel_for_parsing_association_id,
            "last_time_view_posts_tapped": datetime.utcnow().isoformat(),
            "quantity_of_parsed_message": None
        })
    )

    data = {
        "channel_for_parsing_association_id": channel_for_parsings_association_response.data.id
    }

    message_count = 0
    for result in filtered_messages:
        if len(result) == 1:
            result[0].message = result[0].message + "\n\n" + json.dumps(data)
            message: Message = await client.send_message(entity=int(BOT_ID),
                                                         message=result[0])
            await asyncio.sleep(1.5)
        else:
            caption = ""
            for i in result:
                caption += i.message
            message: Message = await client.send_file(int(BOT_ID), result,
                                                      caption=caption + "\n\n" + json.dumps(data))
            await asyncio.sleep(1.5)

        user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.post_one(
            data={'id': channel_for_parsings_association_response.data.user_id}
        ))
        if user_response.data.parsing_stopped is not None:
            if user_response.data.parsing_stopped:
                user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.put(
                    data={
                        'id': channel_for_parsings_association_response.data.user_id,
                        'parsing_stopped': None
                    }
                ))
                break

        message_count += 1

    parsing_source_response = await parsing_source_api.get_one_by_key_value(params={"key": "id", "value": 1})
    await parsing_source_api.put(data={
        "id": 1,  # TELEGRAM
        "posts_quantity": parsing_source_response['data']['posts_quantity'] + message_count
    })


async def try_to_enter_the_channel(join_to_channel_dto: JoinToChannelDto, user_bot_id: int):
    user_id = join_to_channel_dto.user_id
    link = join_to_channel_dto.parser_link
    channel_id = join_to_channel_dto.channel_id

    client: TelegramClient = json_telethon_users[f'{user_bot_id}']['client']
    id: int = json_telethon_users[f'{user_bot_id}']['id']

    if "/+" in link:
        '''
        Joining to private channel
        '''
        import_chat_invite_request = link.split("+")[-1]
        try:
            await client(ImportChatInviteRequest(import_chat_invite_request))

            parser_channel = await client.get_entity(link)
            parser_id = parser_channel.id

            data = {"user_id": user_id,
                    "channel_id": channel_id,
                    "parser_id": parser_id,
                    "parser_link": link,
                    "parser_title": parser_channel.title}

            await send_message_to_bot(data=data,
                                      client=client,
                                      details="user_bot subscribed to channel")

            response = await remote_api.post(endpoint="channel",
                                             data={"user_id": user_bot_id, "parser_id": parser_id, "parser_link": link})

            if response["status"] == "error":
                logging.error(f"{response['details']}")

            return
        except Exception as ex:
            logging.error(f"private channel{ex}")
            data = {"user_id": user_id, "parser_link": link, "channel_id": channel_id}

            if str(ex) == "You have successfully requested to join this chat or channel (caused by ImportChatInviteRequest)":
                await send_message_to_bot(data=data,
                                          client=client,
                                          details="successfully requested to join channel")
                asyncio.create_task(
                    application_approved(data=data, client=client))

            elif str(ex) == ("telethon.errors.rpcerrorlist.InviteHashExpiredError: The chat the user tried to join has "
                             "expired and is not valid anymore (caused by ImportChatInviteRequest)"):
                await send_message_to_bot(data=data, client=client,
                                          details="channel doesnt exist")

            elif str(
                    ex) == "The authenticated user is already a participant of the chat (caused by ImportChatInviteRequest)":
                parser_channel = await client.get_entity(link)
                parser_id = parser_channel.id

                data = {"user_id": user_id,
                        "channel_id": channel_id,
                        "parser_id": parser_id,
                        "parser_link": link,
                        "parser_title": parser_channel.title}

                await send_message_to_bot(data=data, client=client,
                                          details="user_bot subscribed to channel")

            elif "telethon.errors.rpcerrorlist.FloodWaitError" in str(ex):
                json_data: Response[TelethonUserDto] = await remote_api.get(
                    endpoint=f"get_next_telethon_user/{id}"
                )
                response: Response[TelethonUserDto] = Response[TelethonUserDto].parse_obj(json_data)

                if response.data:
                    join_to_channel_dto: JoinToChannelDto = JoinToChannelDto(user_id=user_id,
                                                                             channel_id=channel_id,
                                                                             parser_link=link)

                    sleep_time = random.randint(1, 5)
                    await asyncio.sleep(sleep_time)
                    await try_to_enter_the_channel(join_to_channel_dto=join_to_channel_dto,
                                                   user_bot_id=response.data.user_id)

    else:
        '''
        Joining to public channel
        '''

        try:
            parser_channel = await client.get_entity(link)
            parser_id = parser_channel.id

            await client(JoinChannelRequest(parser_channel))

            data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "parser_id": parser_id,
                "parser_link": link,
                "parser_title": parser_channel.title
            }

            await send_message_to_bot(data=data,
                                      client=client,
                                      details="user_bot subscribed to channel")

            response = await remote_api.post(endpoint="channel",
                                             data={"user_id": user_bot_id, "parser_id": parser_id, "parser_link": link})

            if response["status"] == "error":
                logging.error(f"{response['details']}")
            return
        except Exception as ex:
            logging.error(f"public channel {ex}")
            data = {"user_id": user_id, "parser_link": link, "channel_id": channel_id}

            if str(ex) == (
                    "telethon.errors.rpcerrorlist.UsernameNotOccupiedError: The username is not in use by anyone "
                    "else yet (caused by ResolveUsernameRequest)"):
                await send_message_to_bot(data=data,
                                          client=client,
                                          details="channel doesnt exist")

            elif "telethon.errors.rpcerrorlist.FloodWaitError" in str(ex):
                json_data: Response[TelethonUserDto] = await remote_api.get(endpoint=f"get_next_telethon_user/{id}")
                response: Response[TelethonUserDto] = Response[TelethonUserDto].parse_obj(json_data)

                if response.data:
                    join_to_channel_dto: JoinToChannelDto = JoinToChannelDto(user_id=user_id,
                                                                             parser_link=link,
                                                                             channel_id=channel_id)

                    sleep_time = random.randint(1, 5)
                    await asyncio.sleep(sleep_time)
                    await try_to_enter_the_channel(join_to_channel_dto=join_to_channel_dto,
                                                   user_bot_id=response.data.user_id)

            elif str(
                    ex) == "The channel specified is private and you lack permission to access it. Another reason may be that you were banned from it (caused by JoinChannelRequest)":
                await send_message_to_bot(data=data,
                                          client=client,
                                          details="User banned")


async def application_approved(data: dict, client: TelegramClient):
    while True:
        try:
            sleep_time = random.randint(60, 300)
            await asyncio.sleep(sleep_time)
            parser_channel = await client.get_entity(data["parser_link"])
            data['parser_id'] = parser_channel.id
            data['parser_title'] = parser_channel.title
            await send_message_to_bot(data=data, client=client,
                                      details="user_bot subscribed to channel")
            return
        except Exception as ex:
            logging.error(f"application_approved {ex}")


async def send_message_to_bot(data: dict, client: TelegramClient, details: str):
    sleep_time = random.randint(1, 5)
    await asyncio.sleep(sleep_time)
    data = {
        "status": "success",
        "data": data,
        "details": details
    }
    username = await client.get_entity(BOT_USERNAME)
    await client.send_message(entity=username, message=json.dumps(data))


async def run_client(client: TelegramClient):
    await client.start()
    client.add_event_handler(message_handler, events.NewMessage(incoming=True))
    client.add_event_handler(message_album_handler, events.Album())
    await client.run_until_disconnected()


async def main():
    json_data = await remote_api.get(endpoint="telethon_users")
    response: Response[list[TelethonUserDto]] = Response[list[TelethonUserDto]].model_validate(json_data)

    if response.status == "success":
        for telethon_user in response.data:
            if 'addr' in telethon_user.proxy:
                client = TelegramClient(f"telethon_bot/sessions/{telethon_user.number}",
                                        API_ID,
                                        API_HASH,
                                        proxy=(socks.SOCKS5,
                                               telethon_user.proxy['addr'],
                                               telethon_user.proxy['port'],
                                               True,
                                               telethon_user.proxy['username'],
                                               telethon_user.proxy['password']),
                                        system_version="4.16.30-vxCUSTOM")

            else:
                client = TelegramClient(f"telethon_bot/sessions/{telethon_user.number}",
                                        API_ID,
                                        API_HASH)

            json_telethon_users[f'{telethon_user.user_id}'] = {"id": telethon_user.id, "client": client}
            await run_client(client)
            # TODO wait for all_tasks
            # asyncio.create_task(run_client(client))


asyncio.set_event_loop(asyncio.SelectorEventLoop())
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
