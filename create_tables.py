from database import init_db

print("Начинаю создание таблиц...")
try:
    init_db()
    print("✅ УСПЕХ: Таблицы 'school_users' и 'meals' созданы!")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")