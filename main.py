import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, ChatMemberUpdated, Chat
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "7401774647:AAFiG2GoT3s27Ga9ih8vHNS3RcDPTm8tbPU"
GROUP_CHAT_ID = None  # Пока не знаем chat_id

# Настроим логирование
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Планировщик задач
scheduler = AsyncIOScheduler()


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Я бот для голосований!")


async def get_bot_group():
    """ Проверяет, есть ли бот уже в группе при запуске """
    global GROUP_CHAT_ID

    # Получаем список чатов, в которых бот администратор
    bot_info = await bot.get_me()

    try:
        chat_admins = await bot.get_chat_administrators(GROUP_CHAT_ID)
        if chat_admins:
            GROUP_CHAT_ID = chat_admins[0].chat.id
            logging.info(f"✅ Найдено существующее участие в группе: {GROUP_CHAT_ID}")
            return True
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при получении чатов: {e}")

    return False


@dp.chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    """ Обработчик добавления бота в группу """
    global GROUP_CHAT_ID
    if event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        GROUP_CHAT_ID = event.chat.id
        logging.info(f"✅ Бот добавлен в чат: {GROUP_CHAT_ID}")


async def start_poll():
    """ Функция запуска голосования """
    global GROUP_CHAT_ID
    if GROUP_CHAT_ID:
        question = ("На кого заказывать еду? Минимальный заказ три порции. Стоимость порции 35000$."
                    "Доставка оплачивается отдельно, стоимость 30000$ и делится на количество заказавших")
        options = [
            "Да, я буду. Срочно закажите порцию для меня",
            "Нет, в этот раз не буду заказывать, спасибо",
        ]
        await bot.send_poll(GROUP_CHAT_ID, question, options, is_anonymous=False)
        logging.info(f"📊 Голосование отправлено в чат {GROUP_CHAT_ID}")
    else:
        logging.warning("❌ Бот не состоит в группе. Голосование не отправлено.")


async def wait_for_chat_id():
    """ Ждём, пока появится `GROUP_CHAT_ID`, перед запуском шедулера """
    global GROUP_CHAT_ID
    logging.info("⏳ Ожидание chat_id...")

    # Проверяем, есть ли у бота уже группа
    if await get_bot_group():
        return

    # Если нет, ждём добавления
    while GROUP_CHAT_ID is None:
        await asyncio.sleep(1)

    logging.info(f"✅ Найден chat_id: {GROUP_CHAT_ID}")


async def schedule_poll():
    """ Запуск планировщика только если есть `GROUP_CHAT_ID` """
    await wait_for_chat_id()  # Ждём, пока появится `chat_id`
    scheduler.add_job(start_poll, "interval", minutes=1)
    scheduler.start()
    logging.info("✅ Планировщик запущен!")


async def main():
    asyncio.create_task(schedule_poll())  # Запускаем планировщик в фоне
    await dp.start_polling(bot)  # Запускаем бота


if __name__ == "__main__":
    asyncio.run(main())
