import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.filters.command import Command
import asyncio
import datetime
import random
from typing import List, Dict, Optional, Tuple
import os
import config
from database import Database

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация базы данных
db = Database()

# Определение состояний для FSM (Finite State Machine)
class RatingStates(StatesGroup):
    showing_comparisons = State()
    finished = State()

# Клавиатуры
def get_start_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для начального сообщения"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Начать", callback_data="start_comparison"))
    return builder.as_markup()

def get_comparison_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора изображения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Выбрать слева (оригинал) 👈", callback_data="select_original"),
        InlineKeyboardButton(text="Выбрать справа (вариант) 👉", callback_data="select_variant")
    )
    return builder.as_markup()

def get_finish_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для завершающего сообщения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Начать заново 🔄", callback_data="start_comparison"),
        InlineKeyboardButton(text="Закончить 🚫", callback_data="finish")
    )
    return builder.as_markup()

# Функция для отправки сравнения двух изображений
async def send_image_comparison(chat_id: int, state: FSMContext) -> None:
    """Отправляет сравнение двух изображений пользователю"""
    data = await state.get_data()
    
    variable_images = data.get("variable_images", [])
    current_index = data.get("current_index", 0)
    shown_comparisons = data.get("shown_comparisons", [])
    
    if current_index >= len(variable_images) or current_index >= config.IMAGES_PER_SESSION:
        # Все сравнения показаны
        await bot.send_message(
            chat_id=chat_id,
            text="🏆 Спасибо за помощь!\nТы помог(ла) сделать модель лучше. Хочешь попробовать ещё раз? 🚀",
            reply_markup=get_finish_keyboard()
        )
        await state.set_state(RatingStates.finished)
        
        # Статистика
        selections = data.get("selections", {})
        original_count = sum(1 for v in selections.values() if v)
        total = len(selections)
        if total > 0:
            original_percentage = int((original_count / total) * 100)
            variant_percentage = 100 - original_percentage
            await bot.send_message(
                chat_id=chat_id,
                text=f"📊 Статистика: ты выбрал(а) оригинал {original_count} из {total} раз ({original_percentage}%) и вариант {total-original_count} раз ({variant_percentage}%)!"
            )
        return
    
    current_variable_image = variable_images[current_index]
    variable_image_path = os.path.join(config.IMAGES_FOLDER, current_variable_image)
    
    # Проверяем существуют ли оба файла
    if not os.path.exists(config.FIXED_IMAGE_PATH):
        logging.error(f"Fixed image not found: {config.FIXED_IMAGE_PATH}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Ошибка: оригинальное изображение не найдено. Обратитесь к администратору."
        )
        return
    
    if not os.path.exists(variable_image_path):
        logging.error(f"Variable image not found: {variable_image_path}")
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка: вариант изображения {current_variable_image} не найден. Пропускаем."
        )
        # Переходим к следующему изображению
        await state.update_data(current_index=current_index + 1)
        await send_image_comparison(chat_id, state)
        return
    
    try:
        # Отправляем оба изображения в одном сообщении с медиагруппой
        media = [
            InputMediaPhoto(
                media=types.FSInputFile(config.FIXED_IMAGE_PATH),
                caption="Какой вариант вам нравится больше?"
            ),
            InputMediaPhoto(
                media=types.FSInputFile(variable_image_path)
            )
        ]
        
        # Отправляем группу изображений
        await bot.send_media_group(chat_id=chat_id, media=media)
        
        # Отправляем текст с кнопками выбора отдельным сообщением
        await bot.send_message(
            chat_id=chat_id,
            text=f"📷 Сравнение {current_index + 1}/{min(len(variable_images), config.IMAGES_PER_SESSION)}\n\n"
                 f"Слева: Оригинал (afro.jpg)\n"
                 f"Справа: Вариант ({current_variable_image})\n\n"
                 f"Какое изображение вам нравится больше? 🤔",
            reply_markup=get_comparison_keyboard()
        )
        
        # Обновляем список показанных сравнений
        shown_comparisons.append((os.path.basename(config.FIXED_IMAGE_PATH), current_variable_image))
        
        # Обновляем данные состояния
        await state.update_data(
            current_index=current_index, 
            shown_comparisons=shown_comparisons
        )
        
        # Установка таймера на указанный в конфиге промежуток времени
        timer_task = asyncio.create_task(auto_skip_comparison(chat_id, state, current_index))
        await state.update_data(timer_task=timer_task)
    
    except Exception as e:
        logging.error(f"Error sending comparison: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Произошла ошибка при отправке сравнения: {e}"
        )
        # Пропускаем к следующему сравнению
        await state.update_data(current_index=current_index + 1)
        await send_image_comparison(chat_id, state)

async def auto_skip_comparison(chat_id: int, state: FSMContext, expected_index: int) -> None:
    """Автоматически пропускает сравнение, если пользователь не отвечает"""
    await asyncio.sleep(config.RESPONSE_TIMEOUT)  # Ждем указанное в конфиге время
    
    # Проверяем, не выбрал ли пользователь уже
    current_data = await state.get_data()
    current_index = current_data.get("current_index", 0)
    
    if current_index == expected_index:  # Пользователь не сделал выбор
        logging.info(f"User {chat_id} didn't select in comparison {expected_index}, skipping to next")
        
        # Обновляем индекс
        await state.update_data(current_index=current_index + 1)
        
        # Отправляем сообщение о пропуске
        await bot.send_message(
            chat_id=chat_id,
            text="⏱️ Время вышло! Переходим к следующему сравнению."
        )
        
        # Отправляем следующее сравнение
        await send_image_comparison(chat_id, state)

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    # Сохраняем информацию о пользователе
    await db.save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(
        "👋 Привет!\n"
        "Я показываю разные варианты изображений. Помоги мне выбрать лучший, сравнивая оригинал с вариантами! 😎\n\n"
        "Жми \"Начать\", чтобы приступить. 🚀",
        reply_markup=get_start_keyboard()
    )
    
    # Сбрасываем состояние, если оно было
    await state.clear()

# Обработчики колбэков
@dp.callback_query(F.data == "start_comparison")
async def on_start_comparison(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку 'Начать'"""
    # Получаем данные о пользователе
    user_id = callback.from_user.id
    
    # Получаем данные из состояния
    data = await state.get_data()
    shown_comparisons = data.get("shown_comparisons", [])
    
    # Проверяем наличие фиксированного изображения
    if not os.path.exists(config.FIXED_IMAGE_PATH):
        logging.error(f"Fixed image not found: {config.FIXED_IMAGE_PATH}")
        await callback.message.edit_text("❌ Ошибка: основное изображение не найдено. Обратитесь к администратору.")
        await callback.answer()
        return
    
    # Получаем переменные изображения (все кроме фиксированного)
    # Исключаем ранее показанные переменные изображения
    shown_variable_images = [pair[1] for pair in shown_comparisons]
    variable_images = await db.get_random_images(
        config.IMAGES_PER_SESSION, 
        exclude_for_user_id=user_id,
        exclude_images=shown_variable_images
    )
    
    # Проверяем, получили ли мы изображения
    if not variable_images:
        # Если нет вариантов в базе, попробуем загрузить их из папки
        try:
            all_images = []
            for filename in os.listdir(config.IMAGES_FOLDER):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')) and filename != os.path.basename(config.FIXED_IMAGE_PATH):
                    all_images.append(filename)
            
            if all_images:
                # Добавляем все изображения в базу данных
                image_paths = [os.path.join(config.IMAGES_FOLDER, img) for img in all_images]
                await db.add_images(image_paths)
                
                # Получаем случайные изображения
                variable_images = random.sample(all_images, min(len(all_images), config.IMAGES_PER_SESSION))
            else:
                await callback.message.edit_text("❌ Ошибка: нет доступных вариантов изображений. Обратитесь к администратору.")
                await callback.answer()
                return
        except Exception as e:
            logging.error(f"Error loading images from folder: {e}")
            await callback.message.edit_text("❌ Ошибка при загрузке изображений. Обратитесь к администратору.")
            await callback.answer()
            return
    
    # Сохраняем данные в состояние
    await state.update_data(
        variable_images=variable_images,
        current_index=0,
        shown_comparisons=shown_comparisons,
        selections={}
    )
    
    # Устанавливаем состояние
    await state.set_state(RatingStates.showing_comparisons)
    
    # Отправляем сообщение о начале процесса
    await callback.message.edit_text("🚀 Начинаем показ сравнений! Выбери изображение, которое тебе нравится больше.")
    
    # Отправляем первую пару изображений
    await send_image_comparison(callback.message.chat.id, state)
    
    # Отвечаем на callback, чтобы убрать состояние загрузки у кнопки
    await callback.answer()

@dp.callback_query(F.data.in_(["select_original", "select_variant"]), RatingStates.showing_comparisons)
async def on_comparison_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора изображения"""
    # Получаем данные из состояния
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    variable_images = data.get("variable_images", [])
    selections = data.get("selections", {})
    
    # Если есть активный таймер, отменяем его
    timer_task = data.get("timer_task")
    if timer_task and not timer_task.done():
        timer_task.cancel()
    
    # Текущее переменное изображение
    current_variable_image = variable_images[current_index]
    
    # Определяем выбор (оригинал или вариант)
    selected_original = callback.data == "select_original"
    
    # Сохраняем выбор
    comparison_key = f"{os.path.basename(config.FIXED_IMAGE_PATH)}_{current_variable_image}"
    selections[comparison_key] = selected_original
    
    # Сохраняем выбор в базу данных
    await db.save_comparison_result(
        user_id=callback.from_user.id,
        fixed_image_path=config.FIXED_IMAGE_PATH,
        variable_image_path=os.path.join(config.IMAGES_FOLDER, current_variable_image),
        selected_original=selected_original
    )
    
    # Обновляем данные состояния
    await state.update_data(
        current_index=current_index + 1,
        selections=selections
    )
    
    # Отвечаем на callback
    await callback.answer("Выбор сохранен!")
    
    # Отправляем сообщение с результатом выбора
    selected_text = "оригинал (слева)" if selected_original else f"вариант {current_variable_image} (справа)"
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"Вы выбрали: {selected_text} ✅"
    )
    
    # Отправляем следующее сравнение
    await send_image_comparison(callback.message.chat.id, state)

@dp.callback_query(F.data == "finish")
async def on_finish(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку 'Закончить'"""
    await callback.message.edit_text(
        "Спасибо за участие! Если захочешь сравнить ещё изображения, просто отправь команду /start."
    )
    await state.clear()
    await callback.answer()

# Обработчик команды статистики
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Показывает статистику выборов пользователя"""
    user_id = message.from_user.id
    
    try:
        stats = await db.get_user_stats(user_id)
        
        await message.answer(
            f"📊 Твоя статистика:\n\n"
            f"Всего сравнений: {stats['total']}\n"
            f"Выбран оригинал: {stats['original_selected']} ({stats['original_percentage']:.1f}%)\n"
            f"Выбран вариант: {stats['variant_selected']} ({100 - stats['original_percentage']:.1f}%)"
        )
    except Exception as e:
        logging.error(f"Failed to get user stats: {e}")
        await message.answer("К сожалению, не удалось получить статистику. Попробуйте позже.")

# Главная функция для запуска бота
async def main():
    try:
        # Инициализируем базу данных Firebase
        logging.info("Initializing Firebase database...")
        await db.connect()  # Для совместимости, хотя Firebase инициализируется в __init__
        
        # Проверяем изображения
        logging.info(f"Using images folder: {config.IMAGES_FOLDER}")
        if os.path.exists(config.IMAGES_FOLDER):
            # Добавляем изображения в базу данных
            image_paths = []
            try:
                for filename in os.listdir(config.IMAGES_FOLDER):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        full_path = os.path.join(config.IMAGES_FOLDER, filename)
                        if os.path.isfile(full_path):
                            image_paths.append(full_path)
                
                if image_paths:
                    logging.info(f"Adding {len(image_paths)} images to Firebase database")
                    await db.add_images(image_paths)
                else:
                    logging.warning(f"No image files found in folder: {config.IMAGES_FOLDER}")
            except Exception as e:
                logging.error(f"Error scanning image directory: {e}")
        else:
            logging.error(f"Images folder does not exist: {config.IMAGES_FOLDER}")
            try:
                os.makedirs(config.IMAGES_FOLDER, exist_ok=True)
                logging.info(f"Created images folder: {config.IMAGES_FOLDER}")
            except Exception as e:
                logging.error(f"Failed to create images folder: {e}")
        
        # Проверяем наличие фиксированного изображения
        if not os.path.exists(config.FIXED_IMAGE_PATH):
            logging.error(f"Fixed image not found: {config.FIXED_IMAGE_PATH}")
        else:
            logging.info(f"Fixed image found: {config.FIXED_IMAGE_PATH}")
            # Добавляем фиксированное изображение в базу данных
            await db.add_images([config.FIXED_IMAGE_PATH])
        
        # Запускаем бота
        logging.info("Starting the bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        logging.info("Bot stopped!")
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())