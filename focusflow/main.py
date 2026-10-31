import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import platform
if platform.system() in ("Windows", "Darwin", "Linux"):
    from kivy.config import Config
    Config.set("graphics", "width",  "390")
    Config.set("graphics", "height", "844")
    Config.set("graphics", "resizable", True)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

# UI Screens
from ui.login_screen        import LoginScreen
from ui.interest_screen     import InterestScreen
from ui.settings_screen     import SettingsScreen
from ui.home_screen         import HomeScreen
from ui.session_screen      import SessionScreen
from ui.result_screen       import ResultScreen
from ui.todo_screen         import TodoScreen
from ui.study_room_screen   import StudyRoomScreen
from ui.room_screen         import RoomScreen 

# Data
from data.settings import load_settings
from data.theme import T


class FocusFlowApp(App):

    def build(self):
        Window.clearcolor = T("bg")

        sm = ScreenManager(transition=SlideTransition())

        # Screens
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(InterestScreen(name="interest"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SessionScreen(name="session"))
        sm.add_widget(ResultScreen(name="result"))
        sm.add_widget(StudyRoomScreen(name="study_room"))
        sm.add_widget(RoomScreen(name="room"))        
        sm.add_widget(TodoScreen(name="todo"))

    
        sm.current = "login"

        return sm

    def on_start(self):
        """
        Handle automatic navigation AFTER login screen loads
        """
        settings = load_settings()

        login_screen = self.root.get_screen("login")

        if hasattr(login_screen, "is_authenticated") and login_screen.is_authenticated():
            # First-time user
            if settings.get("interest") is None:
                self.root.current = "interest"
            else:
                self.root.current = "home"

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    FocusFlowApp().run()
