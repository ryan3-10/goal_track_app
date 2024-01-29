import time
import math
import os
from datetime import datetime, timedelta

SECONDS_PER_HOUR = 3600

def format_time(seconds):
    seconds = math.floor(seconds)

    hours = int(seconds // SECONDS_PER_HOUR)
    seconds -= hours * SECONDS_PER_HOUR

    minutes = int(seconds // 60)
    seconds -= minutes * 60

    strings = [str(hours), str(minutes), str(seconds)]
    
    for i, element in enumerate(strings):
        if len(element) == 1:
            strings[i] = "0" + element

    hours, minutes, seconds = strings

    return f"{hours}:{minutes}:{seconds}" 

class Goal:
    def __init__(self, title, cycle_length: int, target: int, cycles_passed=0, cycles_failed=0):
        self.__title = title
        self.__cycle_length = cycle_length              # Number of days in each cycle
        self.__target = target                          # Target number of hours to train for the cycle
        self.__cycles_passed = cycles_passed
        self.__cycles_failed = cycles_failed
        self.__cycles: list[Cycle] = []
    
    def __gt__(self, other):    
        return self.get_title().lower() > other.get_title().lower()
    
    def check_current_cycle(self):
        output = 0 #Will be returned if no cycle was added upon calling this function

        #Check if the cycle has ended. If yes, start a new cycle. 
        while self.get_current_cycle().get_end_date() <= datetime.now():
            self.post_cycle()
            new_cycle = Cycle(self, self.get_current_cycle().get_end_date())
            output = 1 #Will be returned if any cycles were added
        
        return output
    
    def get_title(self):
        return self.__title
    
    def get_cycles(self):
        return self.__cycles
    
    def get_cycle_length(self):
        return self.__cycle_length

    def get_target(self):
        return self.__target

    def get_cycles_passed(self):
        return self.__cycles_passed

    def get_cycles_failed(self):
        return self.__cycles_failed
    
    def get_current_cycle(self):
        if self.__cycles:
            return self.__cycles[-1]
    
    def generate_label_text(self):
        time_periods = {1: "Day", 7: "Week", 30: "Month"}
        plural_check = "hour" if self.get_target() == 1 else "hours"
        output = ""

        output += self.get_title().upper() + "\n"
        output += f"{self.get_target()} {plural_check} per {time_periods[self.get_cycle_length()]}\n"
        output += f"Passed: {self.get_cycles_passed()} Failed: {self.get_cycles_failed()}\n\n"
        output += f"Current Cycle: {self.get_current_cycle().get_dates()}\n"
        output += f"Time spent on current cycle: {format_time(self.get_current_cycle().get_time_training())}\n"

        return output

    def add_cycle(self, cycle):
        self.__cycles.append(cycle)
    
    def post_cycle(self):
        self.get_current_cycle().get_session().stop()

        if self.get_current_cycle().get_time_training() // SECONDS_PER_HOUR >= self.__target:
            self.get_current_cycle().passes()
            self.__cycles_passed += 1
        
        else:
            self.get_current_cycle().fails()
            self.__cycles_failed += 1

class Cycle:
    def __init__(self, goal: Goal, start_date=datetime.now(), time_training = 0, status = "In Progress"):
        self.__time_training = time_training
        self.__start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.__end_date = start_date + timedelta(days=goal.get_cycle_length())
        self.__session = Session(self)
        self.__status = status
        goal.add_cycle(self)
    
    def get_session(self):
        return self.__session
    
    def get_status(self):
        return self.__status
    
    def passes(self):
        self.__status = "Passed"
    
    def fails(self):
        self.__status = "Failed"
    
    def get_start_date(self):
        return self.__start_date

    def get_end_date(self):
        return self.__end_date
    
    def get_dates(self):
        formatted_start = self.__start_date.strftime("%b %d, %Y")
        formatted_end = self.__end_date.strftime("%b %d, %Y")
        return f"{formatted_start} - {formatted_end}"
    
    def get_time_training(self):
        return self.__time_training + self.get_session().time_elapsed()
    
    def format_time_training(self):
        return format_time(self.get_time_training())
    
    def add_session_time(self, seconds):
        self.__time_training += seconds

class Session:
    def __init__(self, cycle: Cycle):
        self.__cycle = cycle
        self.__is_active = False
        self.__start_time = None
    
    def is_active(self):
        return self.__is_active
    
    def start(self):
        self.__is_active = True
        self.__start_time = time.time()
    
    def stop(self):
        self.__cycle.add_session_time(self.time_elapsed())
        self.__is_active = False

    def time_elapsed(self):
        if not self.__is_active:
            return 0
        
        return time.time() - self.__start_time
    
class User:
    def __init__(self):
        self.__goals: list[Goal] = [None, None, None, None, None]
        self.__current_goal = self.__goals[0] #Goal being viewed at a given time
    
    def add_goal(self, goal):
        for element in self.__goals:
            if element != None and element.get_title().lower() == goal.get_title().lower():
                return -1
        
        self.__goals[self.__goals.index(None)] = goal
        self.sort_goals()
    
    def sort_goals(self):
        goals = [goal for goal in self.__goals if goal != None]
        goals.sort()

        for i in range(len(goals)):
            self.__goals[i] = goals[i]
  
    def set_current_goal(self, goal):
        self.__current_goal = goal
    
    def remove_goal(self, goal):
        self.__goals.remove(goal)
        os.remove(f"Goals/{goal.get_title()}")
        self.__goals.append(None)
        self.sort_goals()
    
    def get_goals(self):
        return self.__goals

    def get_current_goal(self) -> Goal:
        return self.__current_goal
    
    def find_goal_by_title(self, title) -> Goal:
        for goal in self.__goals:
            if goal.get_title() == title:
                return goal
            
            return -1
    
    def save_data(self):
        for goal in self.__goals:
            if goal == None:
                continue
            
            with open(f"Goals/{goal.get_title()}", "w") as output:
                print(f"{goal.get_title()},{goal.get_cycle_length()},{goal.get_target()},{goal.get_cycles_passed()},{goal.get_cycles_failed()}", file=output)

                for cycle in goal.get_cycles():
                    print(f"{cycle.get_status()},{cycle.get_start_date()},{cycle.get_time_training()}", file=output)
    
    def load_data(self):
        for filename in os.listdir("Goals"):
            with open(f"Goals/{filename}", "r") as file:
                for i, line in enumerate(file):
                    if i == 0:
                        title, length, target, passed, failed = line.split(",")
                        goal = Goal(title, int(length), int(target), int(passed), int(failed))
                        self.add_goal(goal)
                    
                    else:
                        status, start_date, time_training = line.split(",")
                        y, m, d= start_date[0:11].split("-")
                        Cycle(goal, datetime(int(y), int(m), int(d)), float(time_training), status)