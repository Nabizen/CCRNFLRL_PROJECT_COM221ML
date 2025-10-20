import pygame
import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# === COLORS ===
GREEN_GRASS = (80, 200, 80)
ROAD_GRAY = (60, 60, 60)
LINE_WHITE = (255, 255, 255)
STOP_LINE = (255, 255, 255)
CAR_COLOR = (255, 191, 0)
LIGHT_GREEN = (0, 255, 0)
LIGHT_RED = (255, 0, 0)

# === CONSTANTS ===
SCREEN_W, SCREEN_H = 600, 600
ROAD_W = 150
CENTER = SCREEN_W // 2
BOX_SIZE = 200
INTERSECTION_X1 = CENTER - BOX_SIZE // 2
INTERSECTION_X2 = CENTER + BOX_SIZE // 2
INTERSECTION_Y1 = CENTER - BOX_SIZE // 2
INTERSECTION_Y2 = CENTER + BOX_SIZE // 2
MAX_CARS = 5
CAR_LEN = 25
CAR_WID = 15
CAR_GAP = 25
STOP_MARGIN = 10
FPS = 60
WAIT_LIMIT_MS = 10 * 1000       # 10 seconds
WARNING_WAIT_MS = 5 * 1000      # 5 seconds

def blend_color(base, overlay, alpha=0.5):
    return tuple(int(base[i] * (1 - alpha) + overlay[i] * alpha) for i in range(3))


# === CAR CLASS ===
class Car:
    def __init__(self, direction):
        self.direction = direction
        self.speed = random.uniform(2.5, 5.0)  # random realistic speed
        self.entered_intersection = False
        self.color = CAR_COLOR

        # Waiting state variables
        self.wait_start_time = None
        self.waiting = False

        # Spawn positions
        if direction == "N":
            self.x = CENTER - 40
            self.y = SCREEN_H + CAR_LEN
        elif direction == "S":
            self.x = CENTER + 40
            self.y = 0 - CAR_LEN
        elif direction == "E":
            self.x = 0 - CAR_LEN
            self.y = CENTER - 40
        elif direction == "W":
            self.x = SCREEN_W + CAR_LEN
            self.y = CENTER + 40

    def move(self, ns_green, ew_green, cars_in_lane):
        stop = False

        # Determine stop line based on direction and current light
        if self.direction == "S":
            stop_line = INTERSECTION_Y1 - CAR_LEN - STOP_MARGIN
            if not ns_green and self.y >= stop_line and self.y < INTERSECTION_Y1:
                stop = True
        elif self.direction == "N":
            stop_line = INTERSECTION_Y2 + STOP_MARGIN
            if not ns_green and self.y <= stop_line and self.y + CAR_LEN > INTERSECTION_Y2:
                stop = True
        elif self.direction == "E":
            stop_line = INTERSECTION_X1 - CAR_LEN - STOP_MARGIN
            if not ew_green and self.x >= stop_line and self.x < INTERSECTION_X1:
                stop = True
        elif self.direction == "W":
            stop_line = INTERSECTION_X2 + STOP_MARGIN
            if not ew_green and self.x <= stop_line and self.x + CAR_LEN > INTERSECTION_X2:
                stop = True

        # Stop for car ahead
        idx = cars_in_lane.index(self)
        if idx > 0:
            front_car = cars_in_lane[idx - 1]
            if self.direction == "S" and front_car.y - (self.y + CAR_LEN) < CAR_GAP:
                stop = True
            elif self.direction == "N" and (self.y - (front_car.y + CAR_LEN)) < CAR_GAP:
                stop = True
            elif self.direction == "E" and (front_car.x - (self.x + CAR_LEN)) < CAR_GAP:
                stop = True
            elif self.direction == "W" and ((self.x) - (front_car.x + CAR_LEN)) < CAR_GAP:
                stop = True

        # Manage waiting timer
        if stop:
            if not self.waiting:
                self.waiting = True
                self.wait_start_time = pygame.time.get_ticks()
        else:
            if self.waiting:
                self.waiting = False
                self.wait_start_time = None

            # Move car when not stopped
            if self.direction == "S":
                self.y += self.speed
            elif self.direction == "N":
                self.y -= self.speed
            elif self.direction == "E":
                self.x += self.speed
            elif self.direction == "W":
                self.x -= self.speed

        # Mark if entered intersection
        if (INTERSECTION_X1 <= self.x <= INTERSECTION_X2) and (INTERSECTION_Y1 <= self.y <= INTERSECTION_Y2):
            self.entered_intersection = True

        # Color changes: turns red if waiting more than 5 seconds
        if self.waiting and self.wait_start_time:
            elapsed_ms = pygame.time.get_ticks() - self.wait_start_time
            if elapsed_ms > WARNING_WAIT_MS:
                self.color = (255, 0, 0)
            else:
                self.color = CAR_COLOR
        else:
            self.color = CAR_COLOR

    def draw(self, screen):
        if self.direction in ["N", "S"]:
            rect = pygame.Rect(self.x, self.y, CAR_WID, CAR_LEN)
        else:
            rect = pygame.Rect(self.x, self.y, CAR_LEN, CAR_WID)
        pygame.draw.rect(screen, self.color, rect)



# === ENVIRONMENT ===
class TrafficEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, render_mode=False):
        super(TrafficEnv, self).__init__()

        # Define action and observation space
        # Action: 0 = keep, 1 = switch
        self.action_space = spaces.Discrete(2)

        # Observation: [num_cars_N, num_cars_S, num_cars_E, num_cars_W, light_state]
        # light_state: 0=NS green, 1=EW green
        self.observation_space = spaces.Box(
            low=0, high=10, shape=(5,), dtype=np.float32
        )

        self.render_mode = render_mode
        if self.render_mode:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
            pygame.display.set_caption("Traffic Light RL Environment")
            self.clock = pygame.time.Clock()

        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)

        self.cars_N, self.cars_S, self.cars_E, self.cars_W = [], [], [], []
        self.light_state = "NS"
        self.action_count = 0
        self.last_action_time = 0  # for cooldown (in ms)
        self.timestep = 0          # counts number of simulation steps
        self.episode_done = False
        self.start_time = pygame.time.get_ticks()

        obs = self._get_state()
        info = {}  # return empty info dict as required by Gymnasium
        return obs, info


    def _get_state(self):
        light_flag = 0 if self.light_state == "NS" else 1
        return np.array([
            len(self.cars_N),
            len(self.cars_S),
            len(self.cars_E),
            len(self.cars_W),
            light_flag
        ], dtype=np.float32)

    def step(self, action):
        reward = 0
        done = False

        # Handle action
        current_time = pygame.time.get_ticks()
        if action == 1 and (current_time - self.last_action_time) >= 2000:  # 2-sec cooldown
            self.light_state = "EW" if self.light_state == "NS" else "NS"
            self.action_count += 1
            self.last_action_time = current_time

        ns_green = self.light_state == "NS"
        ew_green = self.light_state == "EW"

        # Spawn cars
        if random.random() < 0.05 and len(self.cars_S) < MAX_CARS:
            self.cars_S.append(Car("S"))
        if random.random() < 0.05 and len(self.cars_N) < MAX_CARS:
            self.cars_N.append(Car("N"))
        if random.random() < 0.05 and len(self.cars_E) < MAX_CARS:
            self.cars_E.append(Car("E"))
        if random.random() < 0.05 and len(self.cars_W) < MAX_CARS:
            self.cars_W.append(Car("W"))

        # Move cars
        for lane_cars in [self.cars_S, self.cars_N, self.cars_E, self.cars_W]:
            for car in lane_cars:
                car.move(ns_green, ew_green, lane_cars)

        # Remove exited cars
        self.cars_S = [c for c in self.cars_S if c.y < SCREEN_H + 50]
        self.cars_N = [c for c in self.cars_N if c.y > -50]
        self.cars_E = [c for c in self.cars_E if c.x < SCREEN_W + 50]
        self.cars_W = [c for c in self.cars_W if c.x > -50]

        # ===== REWARD LOGIC =====
        crossed = sum(c.entered_intersection for c in (self.cars_S + self.cars_N + self.cars_E + self.cars_W))
        waiting = sum(1 for c in (self.cars_S + self.cars_N + self.cars_E + self.cars_W) if not c.entered_intersection)

        reward += crossed * 2           # reward for successful crossing
        reward -= waiting * 0.1         # small penalty for waiting

        # End conditions
        for lane_cars in [self.cars_S, self.cars_N, self.cars_E, self.cars_W]:
            for car in lane_cars:
                if car.waiting and car.wait_start_time:
                    elapsed_ms = pygame.time.get_ticks() - car.wait_start_time
                    if elapsed_ms >= WAIT_LIMIT_MS:
                        # done = True
                        reward -= 50  # heavy penalty for long wait
                        break
            if done:
                break


        # Smooth simulation: stop after 2000 timesteps
        self.timestep += 1
        if self.timestep >= 2000:
            done = True
            reward += 20  # bonus for smooth flow

        if self.action_count >= 20:
            # done = True
            reward -= 10  # small penalty for over-switching

        state = self._get_state()

        if self.render_mode:
            self.render()

        terminated = done
        truncated = False
        info = {}
        return state, reward, terminated, truncated, info


    def render(self):
        if not self.render_mode:
            return
        
            # === Handle window events ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                exit()  # stop the program when the window is closed
                

        self.screen.fill((255, 255, 255))

        vertical_color = blend_color(ROAD_GRAY, LIGHT_GREEN, 0.5) if self.light_state == "NS" else ROAD_GRAY
        horizontal_color = blend_color(ROAD_GRAY, LIGHT_GREEN, 0.5) if self.light_state == "EW" else ROAD_GRAY

        pygame.draw.rect(self.screen, vertical_color, (CENTER - ROAD_W // 2, 0, ROAD_W, SCREEN_H))
        pygame.draw.rect(self.screen, horizontal_color, (0, CENTER - ROAD_W // 2, SCREEN_W, ROAD_W))

        for lane_cars in [self.cars_S, self.cars_N, self.cars_E, self.cars_W]:
            for car in lane_cars:
                car.draw(self.screen)

        pygame.display.flip()
        self.clock.tick(FPS)

    def close(self):
        if self.render_mode:
            pygame.quit()
