import curses
import random
from collections import deque

# Placeholder for the error class
class TerminalTooSmallError(Exception):
    pass

# Placeholder for the game base class
class Game:
    def __init__(self):
        pass

class Car:
    CAR_WIDTH = 3
    CAR_HEIGHT = 4

    def __init__(self, y, x, game_window):
        self.y = y
        self.x = x
        self.game_window = game_window

    def body(self):
        """Returns list with coordinates on which to draw parts of car."""
        y, x = self.y, self.x
        return [
            [y, x+1], [y+1, x], [y+1, x+1], [y+1, x+2],
            [y+2, x+1], [y+3, x], [y+3, x+1], [y+3, x+2],
        ]

    def bounding_box(self):
        """Returns list with coordinates of the car bounding box."""
        y, x = self.y, self.x
        upper_left = [y, x]
        upper_right = [y, x+self.CAR_WIDTH]
        lower_left = [y+self.CAR_HEIGHT, x]
        lower_right = [y+self.CAR_HEIGHT, x+self.CAR_WIDTH]
        return [upper_left, upper_right, lower_left, lower_right]

    def is_point_in_car(self, point):
        """Checks if point is within the car coordinates."""
        [ul, ur, ll, _] = self.bounding_box()
        y, x = point
        return ul[1] <= x <= ur[1] and ul[0] <= y <= ll[0]

    def draw(self):
        for coord in self.body():
            self.game_window.addch(*coord, curses.ACS_CKBOARD)

    def clear(self):
        for coord in self.body():
            self.game_window.addch(*coord, ' ')

    def move(self, y, x):
        """Clears car from screen then adjusts the car's coordinates."""
        self.clear()
        self.y = y
        self.x = x

def check_for_collisions(hero, villains):
    """Checks if the hero and villains have hit each other."""
    hero_points = hero.bounding_box()
    for v in villains:
        for point in hero_points:
            if v.is_point_in_car(point):
                return True
    return False

class Villains:
    def __init__(self, x_positions, game_window):
        self.villains = deque()
        self.allowed_x = x_positions
        self.game_window = game_window

    def __getitem__(self, index):
        return self.villains[index]

    def __len__(self):
        return len(self.villains)

    def random_add(self, hero, difficulty=1):
        """Randomly generates villains 70% of the time per call."""
        if random.randint(0, 10) >= 7:
            return

        villain = Car(y=0, x=random.choice(self.allowed_x), game_window=self.game_window)

        try:
            last_villain = self.villains[-1]
            if check_for_collisions(villain, [last_villain]):
                return

            if len(self.villains) > 1:
                second_last_villain = self.villains[-2]
                generate_double = random.randint(0, 10) < difficulty
                if generate_double and villain.y + 9 > last_villain.y:
                    return
        except IndexError:
            pass

        self.villains.append(villain)

    def move(self):
        for v in self.villains:
            v.move(v.y + 1, v.x)

    def remove(self, window):
        """Remove first car if it's beyond window height."""
        height, _ = window.getmaxyx()
        try:
            if self.villains[0].y >= height - 4:
                self.villains.popleft().clear()
                return 1
        except IndexError:
            pass
        return 0

    def draw(self):
        for car in self.villains:
            car.draw()

class Race(Game):
    MIN_HEIGHT = 20
    MIN_WIDTH = 40
    PADDING = 1

    def __init__(self, stdscreen):
        curses.curs_set(0)
        screen_height, screen_width = stdscreen.getmaxyx()
        if screen_height < Race.MIN_HEIGHT or screen_width < Race.MIN_WIDTH:
            raise TerminalTooSmallError('The terminal window is too small.')

        self.game_window = self.create_game_window(stdscreen)
        self.score_window = self.create_score_window(stdscreen)
        self.hero = Car(y=int(self.game_window.getmaxyx()[0] * 0.6), x=random.choice(self.x_positions), game_window=self.game_window)
        self.villains = Villains(self.x_positions, self.game_window)

    @property
    def x_positions(self):
        """Returns a list containing possible positions of the cars."""
        first = self.PADDING
        second = first + Car.CAR_WIDTH + self.PADDING
        third = second + Car.CAR_WIDTH + self.PADDING
        return [first, second, third]

    def loop(self):
        key = 0
        score = 0
        level = 0

        while key != ord('q'):
            key = self.game_window.getch()
            if key == ord('p'):
                self.pause()
            if check_for_collisions(self.hero, self.villains):
                return
            self.villains.random_add(self.hero, difficulty=level)
            self.hero.draw()
            self.villains.move()
            self.villains.draw()
            score += self.villains.remove(self.game_window)
            level = score // 10
            self.game_window.timeout(max(50, 100 - level * 10))
            self.update_score(score=score, level=level)

    def create_game_window(self, stdscreen):
        height, width = stdscreen.getmaxyx()
        window = curses.newwin(height, self.x_positions[-1] + Car.CAR_WIDTH + self.PADDING * 2, 0, width // 2 - 20)
        window.keypad(True)
        window.timeout(100)
        window.border(0)
        return window

    def create_score_window(self, stdscreen):
        height, width = stdscreen.getmaxyx()
        quit_message = 'Press q to quit'
        score_width = len(quit_message) + self.PADDING * 2
        window = curses.newwin(height, score_width, 0, width // 2 + 20)
        window.border(0)
        window.addstr(height // 2 - 5, 1, quit_message)
        window.refresh()
        return window

    def pause(self):
        while self.game_window.getch() != ord('p'):
            continue

    def update_score(self, score, level=0):
        score_message = f'Score: {score}'
        level_message = f'Level: {level}'
        height, width = self.score_window.getmaxyx()
        self.score_window.addstr(height // 2 - 2, width // 2, level_message)
        self.score_window.addstr(height // 2, width // 2, score_message)
        self.score_window.refresh()

def race_game(stdscreen):
    race = Race(stdscreen)
    race.loop()

if __name__ == '__main__':
    curses.wrapper(race_game)
