import pygame
import random

pygame.init()
SCREEN_W, SCREEN_H = 600, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Traffic Light RL Environment")
clock = pygame.time.Clock()

# === COLORS ===
GREEN_GRASS = (80, 200, 80) # background color
ROAD_GRAY = (60, 60, 60)
LINE_WHITE = (255, 255, 255)
STOP_LINE = (255, 255, 255)
CAR_COLOR = (255, 191, 0)
LIGHT_GREEN = (0, 255, 0)
LIGHT_RED = (255, 0, 0)

# === CONSTANTS ===
ROAD_W = 150
CENTER = SCREEN_W // 2
BOX_SIZE = 200
INTERSECTION_X1 = CENTER - BOX_SIZE // 2
INTERSECTION_X2 = CENTER + BOX_SIZE // 2
INTERSECTION_Y1 = CENTER - BOX_SIZE // 2
INTERSECTION_Y2 = CENTER + BOX_SIZE // 2
MAX_CARS = 4
CAR_LEN = 25
CAR_WID = 15
CAR_GAP = 25  # gap between cars
STOP_MARGIN = 10

def blend_color(base, overlay, alpha=0.5):
    """Blend two RGB colors with transparency factor alpha (0–1)."""
    return tuple(int(base[i] * (1 - alpha) + overlay[i] * alpha) for i in range(3))


# === CAR CLASS ===
class Car:
    def __init__(self, direction):
        self.direction = direction
        self.speed = 2
        self.active = True  # if False, the car is stopped

        if direction == "N":  # coming from bottom going up
            self.x = CENTER - 40
            self.y = SCREEN_H + CAR_LEN
        elif direction == "S":  # from top going down
            self.x = CENTER + 40
            self.y = 0 - CAR_LEN
        elif direction == "E":  # from left to right
            self.x = 0 - CAR_LEN
            self.y = CENTER - 40
        elif direction == "W":  # from right to left
            self.x = SCREEN_W + CAR_LEN
            self.y = CENTER + 40

    def move(self, ns_green, ew_green, cars_in_lane):
        stop = False
        STOP_MARGIN = 10  # distance before intersection border to stop

        # 1️⃣ Light rule: stop at border if red light
        if self.direction == "S":  # top → bottom
            stop_line = INTERSECTION_Y1 - CAR_LEN - STOP_MARGIN
            if not ns_green and self.y >= stop_line and self.y < INTERSECTION_Y1:
                stop = True

        elif self.direction == "N":  # bottom → top
            stop_line = INTERSECTION_Y2 + STOP_MARGIN
            if not ns_green and self.y <= stop_line and self.y + CAR_LEN > INTERSECTION_Y2:
                stop = True

        elif self.direction == "E":  # left → right
            stop_line = INTERSECTION_X1 - CAR_LEN - STOP_MARGIN
            if not ew_green and self.x >= stop_line and self.x < INTERSECTION_X1:
                stop = True

        elif self.direction == "W":  # right → left
            stop_line = INTERSECTION_X2 + STOP_MARGIN
            if not ew_green and self.x <= stop_line and self.x + CAR_LEN > INTERSECTION_X2:
                stop = True

        # 2️⃣ Distance rule: stop if car in front too close
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

        # 3️⃣ Move or stay
        if not stop:
            if self.direction == "S":
                self.y += self.speed
            elif self.direction == "N":
                self.y -= self.speed
            elif self.direction == "E":
                self.x += self.speed
            elif self.direction == "W":
                self.x -= self.speed


    def draw(self):
        if self.direction in ["N", "S"]:
            rect = pygame.Rect(self.x, self.y, CAR_WID, CAR_LEN)
        else:
            rect = pygame.Rect(self.x, self.y, CAR_LEN, CAR_WID)
        pygame.draw.rect(screen, CAR_COLOR, rect)


# === STATE ===
cars_N, cars_S, cars_E, cars_W = [], [], [], []
light_timer = 0
light_state = "NS"

# === MAIN LOOP ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # === LIGHT CONTROL ===
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Toggle light manually
                light_state = "EW" if light_state == "NS" else "NS"
                print(f"Light switched to: {light_state}")

    # === DRAW BACKGROUND ===
    screen.fill((255, 255, 255))  # white background

    # === ROAD COLORS ===
    vertical_color = blend_color(ROAD_GRAY, LIGHT_GREEN, 0.5) if light_state == "NS" else ROAD_GRAY
    horizontal_color = blend_color(ROAD_GRAY, LIGHT_GREEN, 0.5) if light_state == "EW" else ROAD_GRAY

    # Draw vertical and horizontal roads
    pygame.draw.rect(screen, vertical_color, (CENTER - ROAD_W // 2, 0, ROAD_W, SCREEN_H))
    pygame.draw.rect(screen, horizontal_color, (0, CENTER - ROAD_W // 2, SCREEN_W, ROAD_W))


    # Lane dividers
    for y in range(0, SCREEN_H, 40):
        if y + 20 < INTERSECTION_Y1 or y > INTERSECTION_Y2:
            pygame.draw.line(screen, LINE_WHITE, (CENTER - 30, y), (CENTER - 30, y + 20), 2)
            pygame.draw.line(screen, LINE_WHITE, (CENTER + 30, y), (CENTER + 30, y + 20), 2)
    for x in range(0, SCREEN_W, 40):
        if x + 20 < INTERSECTION_X1 or x > INTERSECTION_X2:
            pygame.draw.line(screen, LINE_WHITE, (x, CENTER - 30), (x + 20, CENTER - 30), 2)
            pygame.draw.line(screen, LINE_WHITE, (x, CENTER + 30), (x + 20, CENTER + 30), 2)

    # pygame.draw.rect(screen, STOP_LINE, (INTERSECTION_X1, INTERSECTION_Y1, BOX_SIZE, BOX_SIZE), 3)  # Intersection box


    ns_green = light_state == "NS"
    ew_green = light_state == "EW"

    # === SPAWN CARS ===
    if random.random() < 0.02 and len(cars_S) < MAX_CARS:
        cars_S.append(Car("S"))
    if random.random() < 0.02 and len(cars_N) < MAX_CARS:
        cars_N.append(Car("N"))
    if random.random() < 0.02 and len(cars_E) < MAX_CARS:
        cars_E.append(Car("E"))
    if random.random() < 0.02 and len(cars_W) < MAX_CARS:
        cars_W.append(Car("W"))

    # === MOVE AND DRAW CARS ===
    for lane_cars in [cars_S, cars_N, cars_E, cars_W]:
        for car in lane_cars:
            car.move(ns_green, ew_green, lane_cars)
            car.draw()

    # === REMOVE EXITED CARS ===
    cars_S = [c for c in cars_S if c.y < SCREEN_H + 50]
    cars_N = [c for c in cars_N if c.y > -50]
    cars_E = [c for c in cars_E if c.x < SCREEN_W + 50]
    cars_W = [c for c in cars_W if c.x > -50]

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
