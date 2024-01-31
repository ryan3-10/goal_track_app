from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import SlideTransition
from kivy.clock import Clock
from classes import *
import threading

user = User()
user.load_data()
    
#Define different screens
class HomeWindow(Screen):
    def on_pre_enter(self):
        user.save_data()
        Clock.schedule_once(self.update_texts, 0)
        self.goal0, self.goal1, self.goal2, self.goal3, self.goal4 = user.get_goals()
    
    def update_texts(self, time_delay):
        layout = self.ids.layout
        children = [child for child in layout.children if isinstance(child, Button)]
        children.reverse()

        for i, child in enumerate(children):
            goal = user.get_goals()[i]
            child.font_size = 26

            if goal != None:
                goal.check_current_cycle()
                child.text = goal.generate_label_text()
                child.on_release = self.switch_to_details
            
            else:
                child.text = "Add Goal"
                child.on_release = self.switch_to_add
    
    def switch_to_details(self):
        App.get_running_app().root.current = "details"
    
    def switch_to_add(self):
        App.get_running_app().root.current = "add"
        
class DetailsWindow(Screen):
    def switch_to_home(self, button):
        App.get_running_app().root.transition = SlideTransition(direction='right')
        App.get_running_app().root.current = "home"
    
    def switch_to_session(self, button):
        App.get_running_app().root.transition = SlideTransition(direction='left')
        App.get_running_app().root.current = "session"

    def on_pre_enter(self):
        SCROLL_HEIGHT = 650 if len(user.get_current_goal().get_cycles()) < 5 else 575
        user.get_current_goal().check_current_cycle()
        self.clear_widgets()

        main = BoxLayout(
                        orientation="vertical",
                        spacing = 15,
                        padding = 20
                        )
        
        scroll_view = ScrollView(
                                size_hint=(None, None), 
                                size=(550, SCROLL_HEIGHT),
                                pos_hint={"center_x": 0.5}
                                )
        
        box_layout = BoxLayout(
                            orientation="vertical",
                            size_hint_y=len(user.get_current_goal().get_cycles()) / 5,
                            spacing=10,
                            pos_hint={"center_x": 0.5}
                            )
        
        box_layout.bind(minimum_height=box_layout.setter('height'))

        main.add_widget(Label(text=user.get_current_goal().get_title(), font_size=45))
        main.add_widget(Label(text="Note that cycle end dates are exclusive", font_size=32))

        for cycle in user.get_current_goal().get_cycles()[-1::-1]:
            text = (f"""       {cycle.get_dates()}
   Time Spent this cycle: {cycle.format_time_training()}""")
            
            if cycle.get_status() == "Failed":
                color = GoalTracker.red

            elif cycle.get_status() == "Passed":
                color = GoalTracker.green

            else:
                color = GoalTracker.white

            label = Label(
                          text=text,
                          color=color, 
                          padding=(15), 
                          size_hint=(1, None), 
                          height = 100,
                          halign="left", 
                          valign="middle",
                          font_size=25
                        )
            
            label.bind(size=label.setter("text_size"))
            box_layout.add_widget(label)

        scroll_view.add_widget(box_layout)
        main.add_widget(scroll_view)

        main.add_widget(Button(
                            text="Start a session", 
                            size_hint_x = None,
                            width=550,
                            background_color=GoalTracker.green,
                            on_release=self.switch_to_session
                            ))
        
        main.add_widget(Button(
                            text="Back", 
                            size_hint_x = None,
                            width=550,
                            on_release=self.switch_to_home,
                            background_color = GoalTracker.red
                            ))
        
        main.add_widget(Button(
                            text="Remove Goal", 
                            size_hint_x = None,
                            width=550,
                            on_release=self.switch_to_confirm_deletion,
                            background_color = GoalTracker.red
                            ))
        
        self.add_widget(main)
    
    def switch_to_confirm_deletion(self, button):
        App.get_running_app().root.transition = SlideTransition(direction='left')
        App.get_running_app().root.current = "confirm deletion"
        
class ConfirmWindow(Screen):
    pass
             
class AddWindow(Screen):
    def on_pre_enter(self):
        thread = threading.Thread(target=self.check_fields)
        thread.start()

        #Reset all fields
        self.ids.hours.text = "0"
        self.ids.goal_title.text = ""
        self.ids.error_label.color = (0, 0, 0, 0)
        for toggle in self.ids.toggles.children:
            toggle.state = "normal"
    
    def on_text(self, instance, value):
        #Prevents title from being longer than 20 characters
        if len(value) > 20:
            instance.text = value[:20]

    def check_fields(self):
        while App.get_running_app().root.current == "add":
            if (self.one_active_toggle() and self.ids.goal_title.text.strip() != "" and
                int(self.ids.hours.text) > 0):
                self.ids.add_goal.disabled = False
            
            else:
                self.ids.add_goal.disabled = True

    def set_cycle_length(self, number):
        self.cycle_length = number

    def one_active_toggle(self):
        for toggle in self.ids.toggles.children:
            if toggle.state == "down":
                return True
        
        return False
    
    def update_hours(self, number):
        label = self.ids.hours

        if 0 <= (int(label.text) + number) <= 300:
            label.text = str(int(label.text) + number)
        
        elif int(label.text) + number < 0:
            label.text = "0"
        
        else:
            label.text = "300"
    
    def try_add_goal(self):
        title = self.ids.goal_title.text.strip()
        cycle_length = self.cycle_length
        target = int(self.ids.hours.text)
        goal = Goal(title, cycle_length, target)

        if user.add_goal(goal) == -1:
            return self.show_error()
        
        Cycle(goal) #automatically adds the cycle to the goal 
        App.get_running_app().root.current = "success"
    
    def show_error(self):
        self.ids.error_label.color = GoalTracker.red

class SuccessWindow(Screen):
    pass
    
class SessionWindow(Screen):
    def on_pre_enter(self):
        self.goal = user.get_current_goal()
        self.goal.check_current_cycle()
        self.session = self.goal.get_current_cycle().get_session()

        self.ids.start_stop.disabled = False
        self.ids.goal_name.text = self.goal.get_title()
        self.ids.cycle_range.text = self.goal.get_current_cycle().get_dates()
        self.ids.target_time.text = ("Target Time\n"
        f"   {format_time(self.goal.get_target() * 3600)}")

        self.ids.current_progress.text = ("Current Progress\n"
        f"       {self.goal.get_current_cycle().format_time_training()}")

        #Button needs to be updated pre_enter in case the window was left mid-session
        self.ids.start_stop.text = "Start"
        self.ids.start_stop.background_color = GoalTracker.green

    def start_or_stop(self):
        if not self.session.is_active():
            self.session.start()
            self.ids.start_stop.background_color = GoalTracker.red
            self.ids.start_stop.text = "Stop (Save current progress)"
            self.ids.back.disabled = True
            
            #Keep time updated
            while self.session.is_active():
                self.ids.current_progress.text = ("Current Progress\n"
        f"       {self.goal.get_current_cycle().format_time_training()}")
                
                #Check if cycle has ended
                if self.goal.check_current_cycle() == 1:
                    print("test")
                    self.ids.cycle_range.text = ("This cycle has ended.\n"
                                                "Please exit the session window")
                    
                    self.ids.start_stop.disabled = True
                    self.session.stop()
            
        else:
            self.session.stop()
            self.ids.start_stop.background_color = GoalTracker.green
            self.ids.start_stop.text = "Start"
            self.ids.back.disabled = False
            user.save_data()
    
    def start_thread(self):
        #Thread is needed for constantly updating the time as it is running
        thread = threading.Thread(target = self.start_or_stop)
        thread.start()
            
class WindowManager(ScreenManager):
    pass

class GoalTracker(App):
    user = user

    green = (35/255, 153/255, 31/255, 1)
    blue  = (13/255, 72/255, 133/255)
    red   = (200/255, 32/255, 32/255, 1)
    white = (1, 1, 1, 1)

    def build(self):
        self.root = Builder.load_file("GoalTracker.kv")
        #Window.size = (500, 900)
        Window.clearcolor = (0, 0, 0, 0)
        return self.root
       
    def on_pause(self):
        user.save_data()
        return True
    
    def on_stop(self):
        if user.get_current_goal() != None:
            user.get_current_goal().get_current_cycle().get_session().stop()
        
        user.save_data()


__version__ = "1.0.0"

if __name__ == '__main__':
    GoalTracker().run()
