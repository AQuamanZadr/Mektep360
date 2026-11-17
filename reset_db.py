from database import engine, Base

print("Удаление старых таблиц...")
try:
    # Удаляем старые таблицы (где нет пароля)
    Base.metadata.drop_all(bind=engine)
    print("✅ УСПЕХ: Таблицы удалены.")
    
    # Создаем новые таблицы (с паролем)
    Base.metadata.create_all(bind=engine)
    print("✅ УСПЕХ: Новые таблицы созданы.")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")