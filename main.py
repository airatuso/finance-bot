import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router

from config import BOT_TOKEN
from db import init_db, insert_income, get_last_incomes, get_summary

logging.basicConfig(level=logging.INFO)

# Создаём объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)

# В новой архитектуре Aiogram 3.x часто используют Router
router = Router()

# Проценты распределения (пример — подстраивайте под себя)
PERCENTAGES = {
    "daily_expenses": 0.50,
    "investments": 0.20,
    "cushion": 0.20,
    "dream": 0.10
}

# Словарь для временного хранения данных до подтверждения
pending_data = {}


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Приветственное сообщение по команде /start
    """
    await message.answer(
        "Привет! 😊 Я помогу учесть твои поступления.\n\n"
        "Просто отправь мне сообщение в формате:\n"
        "<b>СУММА</b> <i>ИСТОЧНИК</i>\n\n"
        "Например: <code>10000 Зарплата</code> 💰\n\n"
        "Чтобы посмотреть сводку, набери /report 📊"
    )


@router.message(Command("report"))
async def cmd_report(message: Message):
    """
    Команда /report — показать последние записи и общую статистику.
    """
    rows = get_last_incomes(limit=5)
    if not rows:
        await message.answer(
            "Пока нет никаких записей 😢\n"
            "Отправь что-нибудь в формате <code>10000 Продажа дивана</code>!"
        )
        return

    text_lines = ["<b>Последние 5 записей:</b>\n"]
    for row in rows:
        created_at, source, total, d_exp, inv, cush, dr = row
        text_lines.append(
            f"📆 <i>{created_at}</i>\n"
            f"🔖 Источник: <b>{source}</b>\n"
            f"💰 Сумма: {round(total, 2)}\n"
            f"    • Расходы: {round(d_exp, 2)}\n"
            f"    • Инвестиции: {round(inv, 2)}\n"
            f"    • Подушка: {round(cush, 2)}\n"
            f"    • Мечта: {round(dr, 2)}\n"
        )

    # Общая статистика
    total_sum, d_sum, i_sum, c_sum, dream_sum = get_summary()
    text_lines.append("<b>Суммарно по всем поступлениям:</b> 🌟")
    text_lines.append(
        f"🔹 Общая сумма: {round(total_sum, 2)}\n"
        f"🔹 Ежедневные расходы: {round(d_sum, 2)}\n"
        f"🔹 Инвестиции: {round(i_sum, 2)}\n"
        f"🔹 Подушка: {round(c_sum, 2)}\n"
        f"🔹 Мечта: {round(dream_sum, 2)}"
    )

    await message.answer("\n".join(text_lines))


@router.message()
async def handle_income_message(message: Message):
    """
    Обработка обычных текстовых сообщений как возможного поступления.
    Формат: "<СУММА> <ИСТОЧНИК>"
    """
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Упс! 🧐 Нужно ввести <b>сумму</b> и <b>источник</b> одним сообщением.\n"
            "Например: <code>10000 Зарплата</code>."
        )
        return

    amount_str, source = parts
    try:
        amount = float(amount_str)
    except ValueError:
        await message.answer("Сумма должна быть числом! 😅\nПример: <code>10000 Зарплата</code>")
        return

    # Считаем распределение
    d_expenses = amount * PERCENTAGES["daily_expenses"]
    investments = amount * PERCENTAGES["investments"]
    cushion = amount * PERCENTAGES["cushion"]
    dream = amount * PERCENTAGES["dream"]

    user_id = message.from_user.id
    pending_data[user_id] = {
        "source": source,
        "total_amount": amount,
        "daily_expenses": d_expenses,
        "investments": investments,
        "cushion": cushion,
        "dream": dream
    }

    # Inline-кнопки
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2)

    response_text = (
        f"Сумма: <b>{amount}</b> 💸\n"
        f"Источник: <b>{source}</b>\n\n"
        f"• Ежедневные расходы: {round(d_expenses, 2)}\n"
        f"• Инвестиции: {round(investments, 2)}\n"
        f"• Подушка: {round(cushion, 2)}\n"
        f"• Мечта: {round(dream, 2)}\n\n"
        "Подтверждаем запись? 🤔"
    )
    await message.answer(response_text, reply_markup=kb.as_markup())


@router.callback_query(F.data.in_(['confirm', 'cancel']))
async def process_confirm_cancel(callback: CallbackQuery):
    """
    Обработка нажатия inline-кнопок "Подтвердить" или "Отмена".
    """
    user_id = callback.from_user.id
    action = callback.data

    if user_id not in pending_data:
        await callback.message.edit_text("Нет данных для сохранения. Начните заново 😅")
        await callback.answer()
        return

    data = pending_data[user_id]
    if action == "confirm":
        insert_income(
            source=data["source"],
            total_amount=data["total_amount"],
            daily_expenses=data["daily_expenses"],
            investments=data["investments"],
            cushion=data["cushion"],
            dream=data["dream"]
        )
        await callback.message.edit_text("Отлично! Всё записано в базу 🥳")
    else:
        await callback.message.edit_text("Хорошо, отменяем операцию 🙅‍♂️")

    pending_data.pop(user_id, None)
    await callback.answer()


async def main():
    """
    Точка входа в приложение. Запускаем бота и диспетчер.
    """
    # Инициализируем базу (создаём таблицу, если нет)
    init_db()

    # Создаём Dispatcher и подключаем Router
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
