import sqlite3
from typing import Optional, Dict, Any, List
from core.config.settings import settings  # Добавим импорт настроек

class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.admin_id = settings.bots.admin_id  # Сохраним admin_id
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Проверяем существование таблиц
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = cur.fetchone() is not None
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
        roles_exists = cur.fetchone() is not None

        # Сохраняем данные пользователей
        old_users = []
        if users_exists:
            cur.execute("""SELECT telegram_id, username, display_name, email, 
                        organization, social_link, registration_date, points, role_id 
                        FROM users""")  # Добавляем role_id в выборку
            old_users = cur.fetchall()
            cur.execute("DROP TABLE users")
        
        # Удаляем старую таблицу ролей
        if roles_exists:
            cur.execute("DROP TABLE roles")

        # Создаем таблицу ролей с display_name
        cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL
        )
        """)
        
        # Добавляем базовые роли с отображаемыми именами
        cur.execute("""
            INSERT OR IGNORE INTO roles (id, name, display_name) 
            VALUES 
                (1, 'user', 'Пользователь'),
                (2, 'admin', 'Администратор')
        """)
        
        # Создаем новую таблицу пользователей
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            email TEXT,
            organization TEXT,
            social_link TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            points INTEGER DEFAULT 0,
            role_id INTEGER DEFAULT 1,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
        """)

        # Восстанавливаем данные пользователей
        if old_users:
            for user in old_users:
                # Проверяем, является ли пользователь админом
                role_id = user[8] if len(user) > 8 else (2 if user[0] == self.admin_id else 1)
                cur.execute("""
                    INSERT INTO users (
                        telegram_id, username, display_name, email, 
                        organization, social_link, registration_date, points, role_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (*user[:8], role_id))  # Используем сохраненный role_id или определяем по admin_id
        
        # Создаем таблицу команд
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY,
            tag TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """)
        
        # Создаем таблицу выполненных команд пользователями
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_commands (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            command_id INTEGER,
            voice_file_id TEXT,
            voice_path TEXT,
            transcript TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id),
            FOREIGN KEY (command_id) REFERENCES commands(id)
        )
        """)
        
        conn.commit()
        conn.close()

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT users.*, COALESCE(roles.display_name, 'Пользователь') as role_display_name,
                   roles.name as role_name
            FROM users 
            LEFT JOIN roles ON users.role_id = roles.id 
            WHERE telegram_id = ?
        """, (telegram_id,))
        user = cur.fetchone()
        
        conn.close()
        
        if user:
            return {
                "telegram_id": user[0],
                "username": user[1],
                "display_name": user[2],
                "email": user[3],
                "organization": user[4],
                "social_link": user[5],
                "registration_date": user[6],
                "points": user[7],
                "role": user[10],  # role_name для системных проверок
                "role_display": user[9]  # role_display_name для отображения
            }
        return None

    def create_user(self, telegram_id: int, username: str) -> None:
        """
        Создает нового пользователя.
        Если telegram_id совпадает с admin_id из настроек, назначает роль админа
        """
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Определяем роль: 2 для админа, 1 для обычного пользователя
        role_id = 2 if telegram_id == self.admin_id else 1
        
        # Проверяем, существует ли пользователь
        cur.execute("SELECT role_id FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cur.fetchone()
        
        if existing_user:
            # Если пользователь существует, обновляем его роль
            if telegram_id == self.admin_id and existing_user[0] != 2:
                cur.execute(
                    "UPDATE users SET role_id = 2 WHERE telegram_id = ?",
                    (telegram_id,)
                )
        else:
            # Создаем нового пользователя
            cur.execute(
                "INSERT INTO users (telegram_id, username, role_id) VALUES (?, ?, ?)",
                (telegram_id, username, role_id)
            )
        
        conn.commit()
        conn.close()

    def update_user(self, telegram_id: int, **kwargs) -> None:
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = tuple(kwargs.values()) + (telegram_id,)
        
        cur.execute(f"UPDATE users SET {fields} WHERE telegram_id = ?", values)
        
        conn.commit()
        conn.close()

    def delete_user(self, telegram_id: int) -> None:
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        
        conn.commit()
        conn.close()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей из базы данных"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        
        conn.close()
        
        return [
            {
                "telegram_id": user[0],
                "username": user[1],
                "display_name": user[2],
                "email": user[3],
                "organization": user[4],
                "social_link": user[5],
                "registration_date": user[6],
                "points": user[7]
            }
            for user in users
        ]

    def set_admin_role(self, telegram_id: int) -> None:
        """Устанавливает роль администратора для пользователя"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("UPDATE users SET role_id = 2 WHERE telegram_id = ?", (telegram_id,))
        
        conn.commit()
        conn.close()

    def is_admin(self, telegram_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        user = self.get_user(telegram_id)
        return user is not None and user['role'] == 'admin'

    def add_command(self, tag: str, description: str) -> bool:
        """Добавляет новую команду"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO commands (tag, description) VALUES (?, ?)",
                (tag.lower(), description)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Получает список всех команд"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, tag, description, created_at, is_active 
            FROM commands 
            ORDER BY created_at DESC
        """)
        commands = cur.fetchall()
        
        conn.close()
        
        return [
            {
                "id": cmd[0],
                "tag": cmd[1],
                "description": cmd[2],
                "created_at": cmd[3],
                "is_active": bool(cmd[4])
            }
            for cmd in commands
        ]

    def delete_command(self, command_id: int) -> bool:
        """Удаляет команду"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM commands WHERE id = ?", (command_id,))
        deleted = cur.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted

    def get_command_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """Получает команду по тегу"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id, tag, description, created_at, is_active FROM commands WHERE tag = ?",
            (tag.lower(),)
        )
        cmd = cur.fetchone()
        
        conn.close()
        
        if cmd:
            return {
                "id": cmd[0],
                "tag": cmd[1],
                "description": cmd[2],
                "created_at": cmd[3],
                "is_active": bool(cmd[4])
            }
        return None

    def get_pending_commands(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список команд, которые пользователь еще не выполнил"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT c.id, c.tag, c.description 
            FROM commands c
            WHERE c.is_active = TRUE 
            AND NOT EXISTS (
                SELECT 1 FROM user_commands uc 
                WHERE uc.command_id = c.id 
                AND uc.user_id = ?
            )
            ORDER BY c.created_at DESC
        """, (user_id,))
        
        commands = cur.fetchall()
        conn.close()
        
        return [
            {
                "id": cmd[0],
                "tag": cmd[1],
                "description": cmd[2]
            }
            for cmd in commands
        ]

    def add_user_command(self, user_id: int, command_id: int, voice_file_id: str, voice_path: str, transcript: str) -> bool:
        """Добавляет выполненную пользователем команду"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO user_commands (
                    user_id, command_id, voice_file_id, 
                    voice_path, transcript, status
                )
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (user_id, command_id, voice_file_id, voice_path, transcript))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_user_commands(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список выполненных пользователем команд"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT c.tag, c.description, uc.voice_file_id, uc.created_at, uc.status
            FROM user_commands uc
            JOIN commands c ON c.id = uc.command_id
            WHERE uc.user_id = ?
            ORDER BY uc.created_at DESC
        """, (user_id,))
        
        commands = cur.fetchall()
        conn.close()
        
        return [
            {
                "tag": cmd[0],
                "description": cmd[1],
                "voice_file_id": cmd[2],
                "created_at": cmd[3],
                "status": cmd[4]
            }
            for cmd in commands
        ]

    def get_command_by_id(self, command_id: int) -> Optional[Dict[str, Any]]:
        """Получает команду по ID"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id, tag, description, created_at, is_active FROM commands WHERE id = ?",
            (command_id,)
        )
        cmd = cur.fetchone()
        
        conn.close()
        
        if cmd:
            return {
                "id": cmd[0],
                "tag": cmd[1],
                "description": cmd[2],
                "created_at": cmd[3],
                "is_active": bool(cmd[4])
            }
        return None

    def get_pending_recordings(self) -> List[Dict[str, Any]]:
        """Получает список всех записей, ожидающих проверки"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                uc.id, uc.user_id, uc.voice_file_id, uc.voice_path,
                uc.transcript, uc.created_at, c.tag, c.description,
                u.username, u.display_name
            FROM user_commands uc
            JOIN commands c ON c.id = uc.command_id
            JOIN users u ON u.telegram_id = uc.user_id
            WHERE uc.status = 'pending'
            ORDER BY uc.created_at ASC
        """)
        
        recordings = cur.fetchall()
        conn.close()
        
        return [
            {
                "id": rec[0],
                "user_id": rec[1],
                "voice_file_id": rec[2],
                "voice_path": rec[3],
                "transcript": rec[4],
                "created_at": rec[5],
                "command_tag": rec[6],
                "command_description": rec[7],
                "username": rec[8],
                "display_name": rec[9]
            }
            for rec in recordings
        ]

    def update_recording_status(self, recording_id: int, status: str, points: int = 0) -> bool:
        """Обновляет статус записи и начисляет баллы пользователю"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        try:
            # Обновляем статус записи
            cur.execute(
                "UPDATE user_commands SET status = ? WHERE id = ?",
                (status, recording_id)
            )
            
            # Если запись одобрена, начисляем баллы
            if status == 'approved':
                cur.execute("""
                    UPDATE users 
                    SET points = points + ? 
                    WHERE telegram_id = (
                        SELECT user_id FROM user_commands WHERE id = ?
                    )
                """, (points, recording_id))
            
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_recordings_statistics(self) -> Dict[str, Any]:
        """Получает статистику по записям"""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Получаем общую статистику
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM user_commands
        """)
        stats = cur.fetchone()
        
        # Получаем топ пользователей
        cur.execute("""
            SELECT u.username, u.display_name, COUNT(*) as count
            FROM user_commands uc
            JOIN users u ON u.telegram_id = uc.user_id
            WHERE uc.status = 'approved'
            GROUP BY uc.user_id
            ORDER BY count DESC
            LIMIT 5
        """)
        top_users = cur.fetchall()
        
        conn.close()
        
        # Форматируем топ пользователей
        top_users_text = "\n".join(
            f"{i+1}. @{user[0]} ({user[1]}): {user[2]} записей"
            for i, user in enumerate(top_users)
        )
        
        return {
            "total": stats[0],
            "pending": stats[1],
            "approved": stats[2],
            "rejected": stats[3],
            "top_users": top_users_text
        } 