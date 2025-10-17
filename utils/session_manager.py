# utils/session_manager.py
class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.user_name = None
            cls._instance.user_email = None
            cls._instance.access_token = None
        return cls._instance

    def set_user(self, name, email, token=None):
        self.user_name = name
        self.user_email = email
        self.access_token = token

    def get_user(self):
        return self.user_name, self.user_email

    def clear(self):
        self.user_name = None
        self.user_email = None
        self.access_token = None
