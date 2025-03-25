import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import logging
from typing import List, Dict, Optional, Tuple
import datetime
import config
import random

class Database:
    def __init__(self):
        """Инициализация соединения с Firebase Firestore"""
        try:
            # Проверяем, не инициализирован ли уже Firebase
            if not firebase_admin._apps:
                # Путь к файлу учетных данных Firebase
                credentials_path = config.FIREBASE_CREDENTIALS_PATH
                
                # Проверяем существование файла с учетными данными
                if not os.path.exists(credentials_path):
                    # Если не найден, пробуем найти в корневой директории проекта
                    project_root = os.path.dirname(__file__)
                    credentials_path = os.path.join(project_root, os.path.basename(credentials_path))
                    
                    if not os.path.exists(credentials_path):
                        logging.error(f"Firebase credentials file not found: {config.FIREBASE_CREDENTIALS_PATH}")
                        raise FileNotFoundError(f"Firebase credentials file not found: {config.FIREBASE_CREDENTIALS_PATH}")
                
                # Инициализация Firebase с учетными данными
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': config.FIREBASE_PROJECT_ID,
                })
                logging.info("Firebase initialized successfully")
            
            # Получение клиента Firestore
            self.db = firestore.client()
            logging.info("Firestore client created")
        
        except Exception as e:
            logging.error(f"Error initializing Firebase: {e}")
            raise
    
    async def connect(self):
        """Метод для совместимости с существующим кодом"""
        logging.info("Firebase connection is managed automatically")
        return True
    
    async def close(self):
        """Метод для совместимости с существующим кодом"""
        logging.info("Firebase connection is closed automatically")
        return True
    
    async def save_user(self, user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
        """Сохраняет информацию о пользователе в Firestore"""
        try:
            # Преобразуем ID пользователя в строку для использования в качестве ID документа
            user_ref = self.db.collection(config.USERS_COLLECTION).document(str(user_id))
            
            # Создаем или обновляем документ пользователя
            user_ref.set({
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'created_at': firestore.SERVER_TIMESTAMP  # Автоматическая метка времени
            }, merge=True)  # merge=True работает как UPSERT
            
            logging.info(f"User saved/updated: {user_id}, {username}")
            return True
        
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            return False
    
    async def add_images(self, image_paths: List[str]):
        """Добавляет изображения в базу данных Firestore"""
        try:
            # Используем пакетную запись для эффективности
            batch = self.db.batch()
            added_count = 0
            
            for path in image_paths:
                filename = os.path.basename(path)
                
                # Проверяем, существует ли изображение с таким именем
                images_query = self.db.collection(config.IMAGES_COLLECTION).where('filename', '==', filename).limit(1)
                existing_images = list(images_query.stream())
                
                if not existing_images:
                    # Если изображение не существует, добавляем его
                    new_image_ref = self.db.collection(config.IMAGES_COLLECTION).document()
                    batch.set(new_image_ref, {
                        'filename': filename,
                        'upload_date': firestore.SERVER_TIMESTAMP
                    })
                    added_count += 1
            
            # Выполняем пакетную операцию только если есть что добавлять
            if added_count > 0:
                batch.commit()
                logging.info(f"Added {added_count} new images to database")
            else:
                logging.info("No new images to add")
            
            return True
        
        except Exception as e:
            logging.error(f"Error adding images: {e}")
            return False
    
    async def get_image_id(self, filename: str) -> Optional[str]:
        """Получает ID изображения по имени файла"""
        try:
            # Запрос для поиска изображения по имени файла
            query = self.db.collection(config.IMAGES_COLLECTION).where('filename', '==', filename).limit(1)
            results = list(query.stream())
            
            if results:
                return results[0].id
            return None
        
        except Exception as e:
            logging.error(f"Error getting image ID: {e}")
            return None
    
    async def get_random_images(self, count: int, exclude_for_user_id=None, exclude_images=None) -> List[str]:
        """Возвращает случайные изображения из базы данных Firestore"""
        try:
            # Получаем имя фиксированного изображения
            fixed_image_name = os.path.basename(config.FIXED_IMAGE_PATH)
            
            # Получаем доступные изображения из файловой системы
            available_images = []
            if os.path.exists(config.IMAGES_FOLDER):
                for filename in os.listdir(config.IMAGES_FOLDER):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')) and filename != fixed_image_name:
                        if os.path.isfile(os.path.join(config.IMAGES_FOLDER, filename)):
                            available_images.append(filename)
            
            if not available_images:
                logging.error("No available images found in the images folder")
                return []
            
            # Исключаем указанные изображения
            if exclude_images and len(exclude_images) > 0:
                available_images = [img for img in available_images if img not in exclude_images]
            
            # Если нужно исключить изображения, уже показанные пользователю
            if exclude_for_user_id:
                # Получаем сравнения для этого пользователя
                comparison_docs = self.db.collection(config.COMPARISONS_COLLECTION).where('user_id', '==', exclude_for_user_id).stream()
                
                # Получаем имена переменных изображений из сравнений
                shown_images = []
                for doc in comparison_docs:
                    data = doc.to_dict()
                    variable_image_id = data.get('variable_image_id')
                    if variable_image_id:
                        image_doc = self.db.collection(config.IMAGES_COLLECTION).document(variable_image_id).get()
                        if image_doc.exists:
                            image_filename = image_doc.to_dict().get('filename')
                            if image_filename:
                                shown_images.append(image_filename)
                
                # Исключаем показанные изображения
                available_images = [img for img in available_images if img not in shown_images]
            
            # Перемешиваем и ограничиваем количество
            random.shuffle(available_images)
            selected_images = available_images[:min(count, len(available_images))]
            
            # Добавляем выбранные изображения в базу данных, если их там еще нет
            image_paths = [os.path.join(config.IMAGES_FOLDER, img) for img in selected_images]
            await self.add_images(image_paths)
            
            return selected_images
        
        except Exception as e:
            logging.error(f"Error getting random images: {e}")
            return []
    
    async def save_comparison_result(self, user_id: int, fixed_image_path: str, variable_image_path: str, selected_original: bool):
        """Сохраняет результат сравнения в Firestore"""
        try:
            # Получаем имена файлов из путей
            fixed_filename = os.path.basename(fixed_image_path)
            variable_filename = os.path.basename(variable_image_path)
            
            # Проверяем существование файлов
            if not os.path.exists(fixed_image_path):
                logging.error(f"Fixed image not found: {fixed_image_path}")
                return False
                
            if not os.path.exists(variable_image_path):
                logging.error(f"Variable image not found: {variable_image_path}")
                return False
            
            # Получаем ID изображений
            fixed_image_id = await self.get_image_id(fixed_filename)
            variable_image_id = await self.get_image_id(variable_filename)
            
            # Если изображения еще не в базе, добавляем их
            if not fixed_image_id or not variable_image_id:
                await self.add_images([fixed_image_path, variable_image_path])
                fixed_image_id = await self.get_image_id(fixed_filename)
                variable_image_id = await self.get_image_id(variable_filename)
            
            # Сохраняем результат сравнения
            self.db.collection(config.COMPARISONS_COLLECTION).add({
                'user_id': user_id,
                'fixed_image_id': fixed_image_id,
                'variable_image_id': variable_image_id,
                'selected_original': selected_original,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            logging.info(f"Saved comparison: user={user_id}, fixed={fixed_filename}, variable={variable_filename}, selected_original={selected_original}")
            return True
        
        except Exception as e:
            logging.error(f"Error saving comparison: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Возвращает статистику выборов пользователя из Firestore"""
        try:
            # Получаем все сравнения пользователя
            comparison_docs = self.db.collection(config.COMPARISONS_COLLECTION).where('user_id', '==', user_id).stream()
            comparisons = list(comparison_docs)
            
            # Подсчитываем статистику
            total = len(comparisons)
            original_selected = sum(1 for comp in comparisons if comp.to_dict().get('selected_original', False))
            variant_selected = total - original_selected
            
            # Вычисляем процент выбора оригинала
            original_percentage = (original_selected / total * 100) if total > 0 else 0
            
            return {
                "total": total,
                "original_selected": original_selected,
                "variant_selected": variant_selected,
                "original_percentage": original_percentage
            }
        
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return {
                "total": 0,
                "original_selected": 0,
                "variant_selected": 0,
                "original_percentage": 0
            }