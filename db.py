import sqlite3
from datetime import datetime

DB_PATH = "finance.db"

def init_db():
    """
    Инициализация базы данных. Создаём таблицу incomes при необходимости.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL,
            total_amount REAL NOT NULL,
            daily_expenses REAL NOT NULL,
            investments REAL NOT NULL,
            cushion REAL NOT NULL,
            dream REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_income(source, total_amount, daily_expenses, investments, cushion, dream):
    """
    Вставляет одну запись в таблицу incomes.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO incomes (
            created_at,
            source,
            total_amount,
            daily_expenses,
            investments,
            cushion,
            dream
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (created_at, source, total_amount, daily_expenses, investments, cushion, dream))

    conn.commit()
    conn.close()


def get_last_incomes(limit=5):
    """
    Возвращает последние 'limit' записей из таблицы incomes (сортируем по id DESC).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT created_at, source, total_amount, daily_expenses, investments, cushion, dream
        FROM incomes
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_summary():
    """
    Пример суммарного отчёта по всем записям: суммируем total_amount, daily_expenses и т.д.
    Возвращает кортеж (total_amount_sum, daily_expenses_sum, investments_sum, cushion_sum, dream_sum).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            SUM(total_amount),
            SUM(daily_expenses),
            SUM(investments),
            SUM(cushion),
            SUM(dream)
        FROM incomes
    """)

    row = cursor.fetchone()
    conn.close()

    # Если в таблице нет записей, row будет (None, None, None, None, None)
    return row if row else (0, 0, 0, 0, 0)
