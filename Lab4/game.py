import random
import pygame

TILE = 28
MAZE = [
    "#####################",
    "#o........#........o#",
    "#.###.###.#.###.###.#",
    "#...................#",
    "#.###.#.#####.#.###.#",
    "#.....#...#...#.....#",
    "#####.###.#.###.#####",
    "#####.#.......#.#####",
    "#####.#.## ##.#.#####",
    "#.......#   #.......#",
    "#.###.#.#####.#.###.#",
    "#.###.#.......#.###.#",
    "#o..#...........#..o#",
    "#####################",
]
ROWS, COLS = len(MAZE), len(MAZE[0])
W, H = COLS * TILE, ROWS * TILE + 32
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
KEY_DIRS = {pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0), pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1)}
HOUSE_CELLS = {(8, 10), (9, 9), (9, 10), (9, 11)}
HOUSE_EXIT, HOUSE_CENTER = (7, 10), (9, 10)
PLAYER_START = (11, 10)
FRIGHT_SECONDS = 3.0
PLAYER_STEP, GHOST_STEP = 0.14, 0.17

# Bonus fruit and HUD notifications state
BONUS_FRUIT = {"pos": (7, 10), "active": False, "timer": 0.0, "points": 100}
HUD_MESSAGE = ""
HUD_TIMER = 0.0


def ghost_color(name, mode):
    """Return an (r, g, b) colour override for a ghost, or None to keep the default.
    Provides each ghost with a distinct frightened-mode tint instead of generic blue."""
    if mode == "frightened":
        tints = {
            "blinky": (65, 85, 245),   # Royal indigo blue
            "pinky": (185, 95, 225),   # Lilac / orchid violet tint
            "inky": (45, 200, 215),    # Cyan / seafoam turquoise tint
            "clyde": (100, 150, 235),  # Periwinkle / steel blue tint
        }
        return tints.get(name)
    return None


def on_pellet_eaten(score, pellets_left):
    """Called after every pellet is eaten; add sound, flashes, or bonus fruit here."""
    global BONUS_FRUIT, HUD_MESSAGE, HUD_TIMER
    # Spawn bonus cherry when milestone pellet counts are reached
    if pellets_left in (115, 80, 40):
        BONUS_FRUIT["active"] = True
        BONUS_FRUIT["timer"] = 8.0
        HUD_MESSAGE = f"CHERRY SPAWNED! (+{BONUS_FRUIT['points']} PTS)"
        HUD_TIMER = 2.5
    elif pellets_left == 1:
        HUD_MESSAGE = "FINAL PELLET REMAINING!"
        HUD_TIMER = 4.0


def bonus_life_threshold():
    """Return a score value at which the player earns an extra life, or None to disable bonus lives."""
    return 500  # Bonus life awarded every 500 points (calibrated for mini-maze)


def is_wall(cell):
    row, col = cell
    return not (0 <= row < ROWS and 0 <= col < COLS) or MAZE[row][col] == "#"


def target_for_pinky(player, direction):
    return (player[0] + direction[0] * 4, player[1] + direction[1] * 4)


def distance_sq(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


class Ghost:
    def __init__(self, name, color, start, corner, release):
        self.name, self.color, self.start, self.corner, self.release = name, color, start, corner, release
        self.reset()

    def reset(self):
        self.pos = self.start
        self.direction = (0, 0)
        self.eaten = False
        self.skip = False
        self.timer = 0.0

    def target(self, player, direction, blinky, chase):
        if self.eaten:
            return HOUSE_CENTER
        if self.pos in HOUSE_CELLS:
            return HOUSE_EXIT
        if not chase:
            return self.corner
        if self.name == "pinky":
            return target_for_pinky(player, direction)
        if self.name == "inky":
            ahead = (player[0] + direction[0] * 2, player[1] + direction[1] * 2)
            return (2 * ahead[0] - blinky.pos[0], 2 * ahead[1] - blinky.pos[1])
        if self.name == "clyde":
            return self.corner if distance_sq(self.pos, player) < 64 else player
        return player

    def options(self):
        result = []
        for d in DIRS:
            cell = (self.pos[0] + d[0], self.pos[1] + d[1])
            if is_wall(cell):
                continue
            if cell in HOUSE_CELLS and self.pos not in HOUSE_CELLS and not self.eaten:
                continue
            result.append(d)
        back = (-self.direction[0], -self.direction[1])
        forward = [d for d in result if d != back]
        return forward or result

    def step(self, target, frightened):
        choices = self.options()
        if not choices:
            return
        if frightened and not self.eaten:
            self.direction = random.choice(choices)
        else:
            self.direction = min(choices, key=lambda d: distance_sq((self.pos[0] + d[0], self.pos[1] + d[1]), target))
        self.pos = (self.pos[0] + self.direction[0], self.pos[1] + self.direction[1])
        if self.eaten and self.pos == HOUSE_CENTER:
            self.eaten = False

    def reverse(self):
        self.direction = (-self.direction[0], -self.direction[1])


class Game:
    def __init__(self):
        self.ghosts = [
            Ghost("blinky", (255, 40, 40), (7, 9), (0, COLS - 1), 0.0),
            Ghost("pinky", (255, 150, 200), (9, 10), (0, 0), 2.0),
            Ghost("inky", (60, 220, 230), (9, 9), (ROWS - 1, COLS - 1), 5.0),
            Ghost("clyde", (255, 170, 40), (9, 11), (ROWS - 1, 0), 8.0),
        ]
        self.reset()

    def reset(self):
        self.pellets = {(r, c) for r, line in enumerate(MAZE) for c, v in enumerate(line) if v in ".o"}
        self.player, self.direction, self.desired = list(PLAYER_START), (0, 1), (0, 1)
        self.score, self.lives, self.state = 0, 3, "play"
        self.bonus_awarded = 0
        self.clock_time = self.fright_left = self.player_acc = self.ghost_acc = 0.0
        global BONUS_FRUIT, HUD_MESSAGE, HUD_TIMER
        BONUS_FRUIT["active"] = False
        BONUS_FRUIT["timer"] = 0.0
        HUD_MESSAGE = ""
        HUD_TIMER = 0.0
        for ghost in self.ghosts:
            ghost.reset()

    def respawn(self):
        self.player, self.direction, self.desired = list(PLAYER_START), (0, 1), (0, 1)
        self.fright_left = 0.0
        for ghost in self.ghosts:
            ghost.reset()
        self.clock_time = 0.0

    def chasing(self):
        return (self.clock_time % 27) >= 7

    def move_player(self):
        for d in (self.desired, self.direction):
            cell = (self.player[0] + d[0], self.player[1] + d[1])
            if not is_wall(cell) and cell not in HOUSE_CELLS:
                self.direction = d
                self.player[:] = cell
                self.eat(tuple(cell))
                # Bonus fruit collision check
                global BONUS_FRUIT, HUD_MESSAGE, HUD_TIMER
                if BONUS_FRUIT["active"] and tuple(cell) == BONUS_FRUIT["pos"]:
                    BONUS_FRUIT["active"] = False
                    self.score += BONUS_FRUIT["points"]
                    HUD_MESSAGE = f"FRUIT COLLECTED! +{BONUS_FRUIT['points']}"
                    HUD_TIMER = 2.5
                return

    def eat(self, cell):
        if cell not in self.pellets:
            return
        self.pellets.remove(cell)
        self.score += 10
        # Task 1 Fix: check lowercase 'o' (and uppercase 'O') for power pellet
        if MAZE[cell[0]][cell[1]] in ("o", "O"):
            self.score += 40
            self.fright_left = FRIGHT_SECONDS
            for ghost in self.ghosts:
                if not ghost.eaten:
                    ghost.reverse()
        on_pellet_eaten(self.score, len(self.pellets))
        if not self.pellets:
            self.state = "win"

    def check_collisions(self):
        for ghost in self.ghosts:
            if ghost.pos != tuple(self.player) or ghost.eaten:
                continue
            if self.fright_left > 0:
                ghost.eaten = True
                self.score += 200
            else:
                self.lives -= 1
                self.respawn()
                if self.lives <= 0:
                    self.state = "lose"
                return

    def update(self, dt):
        if self.state != "play":
            return
        self.clock_time += dt
        self.fright_left = max(0.0, self.fright_left - dt)
        
        # Fruit & HUD timers update
        global HUD_TIMER, BONUS_FRUIT
        if HUD_TIMER > 0:
            HUD_TIMER = max(0.0, HUD_TIMER - dt)
        if BONUS_FRUIT["active"]:
            BONUS_FRUIT["timer"] -= dt
            if BONUS_FRUIT["timer"] <= 0:
                BONUS_FRUIT["active"] = False

        threshold = bonus_life_threshold()
        if threshold and self.score // threshold > self.bonus_awarded:
            self.bonus_awarded = self.score // threshold
            self.lives += 1
            global HUD_MESSAGE
            HUD_MESSAGE = "BONUS LIFE AWARDED!"
            HUD_TIMER = 3.0

        self.player_acc += dt
        while self.player_acc >= PLAYER_STEP:
            self.player_acc -= PLAYER_STEP
            self.move_player()
            self.check_collisions()
        self.ghost_acc += dt
        while self.ghost_acc >= GHOST_STEP:
            self.ghost_acc -= GHOST_STEP
            for ghost in self.ghosts:
                if self.clock_time < ghost.release:
                    continue
                scared = self.fright_left > 0 and not ghost.eaten
                if scared:
                    ghost.skip = not ghost.skip
                    if ghost.skip:
                        continue
                ghost.step(ghost.target(tuple(self.player), self.direction, self.ghosts[0], self.chasing()), scared)
            self.check_collisions()

    def draw(self, screen, font):
        screen.fill((5, 5, 30))
        for r, line in enumerate(MAZE):
            for c, value in enumerate(line):
                rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                if value == "#":
                    pygame.draw.rect(screen, (20, 80, 180), rect.inflate(-4, -4), border_radius=6)
                elif (r, c) in self.pellets:
                    pygame.draw.circle(screen, (255, 220, 120), rect.center, 3 if value == "." else 7)
        
        # Draw bonus fruit if active
        global BONUS_FRUIT, HUD_MESSAGE, HUD_TIMER
        if BONUS_FRUIT["active"]:
            fx = BONUS_FRUIT["pos"][1] * TILE + TILE // 2
            fy = BONUS_FRUIT["pos"][0] * TILE + TILE // 2
            pygame.draw.circle(screen, (220, 20, 40), (fx - 4, fy + 2), 5)
            pygame.draw.circle(screen, (220, 20, 40), (fx + 4, fy + 4), 5)
            pygame.draw.line(screen, (50, 180, 50), (fx - 4, fy - 2), (fx, fy - 7), 2)
            pygame.draw.line(screen, (50, 180, 50), (fx + 4, fy), (fx, fy - 7), 2)

        px, py = self.player[1] * TILE + TILE // 2, self.player[0] * TILE + TILE // 2
        pygame.draw.circle(screen, (255, 220, 20), (px, py), TILE // 2 - 2)
        mouth = pygame.Vector2(self.direction[1], self.direction[0]) * (TILE // 2)
        if int(self.clock_time * 6) % 2 == 0 and mouth.length() > 0:
            side = pygame.Vector2(-mouth.y, mouth.x) * 0.6
            pygame.draw.polygon(screen, (5, 5, 30), [(px, py), (px + mouth.x + side.x, py + mouth.y + side.y),
                                                      (px + mouth.x - side.x, py + mouth.y - side.y)])
        for ghost in self.ghosts:
            gx, gy = ghost.pos[1] * TILE + TILE // 2, ghost.pos[0] * TILE + TILE // 2
            color = ghost.color
            if self.fright_left > 0:
                color = (240, 240, 240) if self.fright_left < 1 and int(self.fright_left * 6) % 2 else (40, 60, 230)
            mode = "eaten" if ghost.eaten else "frightened" if self.fright_left > 0 else "normal"
            color = ghost_color(ghost.name, mode) or color
            if ghost.eaten:
                pygame.draw.circle(screen, (240, 240, 240), (gx - 4, gy), 3)
                pygame.draw.circle(screen, (240, 240, 240), (gx + 4, gy), 3)
            else:
                pygame.draw.circle(screen, color, (gx, gy - 2), TILE // 2 - 3)
                pygame.draw.rect(screen, color, (gx - TILE // 2 + 3, gy - 2, TILE - 6, TILE // 2 - 2))
                pygame.draw.circle(screen, (255, 255, 255), (gx - 4, gy - 4), 3)
                pygame.draw.circle(screen, (255, 255, 255), (gx + 4, gy - 4), 3)

        hud_text = f"Score {self.score}   Lives {self.lives}   R = reset"
        if HUD_TIMER > 0 and HUD_MESSAGE:
            hud_text += f"   [{HUD_MESSAGE}]"
        hud_color = (255, 230, 80) if (HUD_TIMER > 0 and int(HUD_TIMER * 4) % 2) else (240, 240, 240)
        hud = font.render(hud_text, True, hud_color)
        screen.blit(hud, (8, ROWS * TILE + 6))

        if self.state != "play":
            text = "YOU WIN! Press R" if self.state == "win" else "GAME OVER - Press R"
            label = font.render(text, True, (255, 255, 120))
            screen.blit(label, label.get_rect(center=(W // 2, H // 2)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Pac-Man")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    game = Game()
    running = True
    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_DIRS:
                    game.desired = KEY_DIRS[event.key]
                elif event.key == pygame.K_r:
                    game.reset()
        game.update(dt)
        game.draw(screen, font)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
