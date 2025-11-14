# modes/mode2.py
# SpelloVerse — Mode 2 

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random, time, pygame, copy
from pygame.locals import *
from systems import db_manager
from systems.audio import speak_word

# ---------------- PATH FIX FOR PYINSTALLER ----------------
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path


# ---------------- CONSTANTS ----------------
FPS = 30
WINDOWWIDTH, WINDOWHEIGHT = 900, 820
BOARDWIDTH, BOARDHEIGHT = 8, 8
TILE_SIZE = 64
MARGIN_X = int((WINDOWWIDTH - TILE_SIZE * BOARDWIDTH) / 2)
MARGIN_Y = 60
XMARGIN, YMARGIN = MARGIN_X, MARGIN_Y

# Colors
DARK_BLUE = (12, 24, 60)
LIGHT_BLUE = (140, 200, 255)
WHITE = (255, 255, 255)
HUD_BG = (35, 35, 55, 180)
GLOW_COLOR = LIGHT_BLUE
INVALID_COLOR = (220, 60, 60)

GLOW_RADIUS = 6
MIN_WORD_LEN = 3
SCORE_PER_LETTER = 10

SPACE_BG = None
PLAYER_ICON = None
BACK_ICON = None
BADSWAP_SOUND = None


# ---------------- UTIL ----------------
def _get_word_entry(word_upper):
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM words WHERE word = ?", (word_upper,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None

def _random_letter():
    return chr(random.randint(65, 90))


# ---------------- BOARD ----------------
def make_letter_board():
    return [[_random_letter() for _ in range(BOARDHEIGHT)] for _ in range(BOARDWIDTH)]

def pull_down_letters(board):
    for x in range(BOARDWIDTH):
        col = [board[x][y] for y in range(BOARDHEIGHT) if board[x][y] is not None]
        newcol = [None]*(BOARDHEIGHT - len(col)) + col
        for y in range(BOARDHEIGHT):
            if newcol[y] is None:
                newcol[y] = _random_letter()
        board[x] = newcol

def remove_positions(board, positions):
    for (x,y) in positions:
        if 0 <= x < BOARDWIDTH and 0 <= y < BOARDHEIGHT:
            board[x][y] = None


# ---------------- DRAW UTILS ----------------
def tile_rect(x, y):
    return pygame.Rect(XMARGIN + x*TILE_SIZE, YMARGIN + y*TILE_SIZE, TILE_SIZE, TILE_SIZE)

def center_of_tile(x, y):
    r = tile_rect(x,y)
    return r.center


# ---------------- MODE 2 MAIN ----------------
def main(player_name=None):
    global SPACE_BG, PLAYER_ICON, BACK_ICON, BADSWAP_SOUND
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("SpelloVerse — Mode 2 ")
    BASICFONT = pygame.font.Font('freesansbold.ttf', 20)

    # Background
    try:
        SPACE_BG = pygame.image.load(resource_path("assets/bg/space.png"))
        SPACE_BG = pygame.transform.scale(SPACE_BG, (WINDOWWIDTH, WINDOWHEIGHT))
    except:
        SPACE_BG = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT))
        SPACE_BG.fill((6,8,18))

    # Player icon
    try:
        PLAYER_ICON = pygame.image.load(resource_path("assets/images/player.png"))
        PLAYER_ICON = pygame.transform.smoothscale(PLAYER_ICON, (32,32))
    except:
        PLAYER_ICON = pygame.Surface((32,32))
        PLAYER_ICON.fill((200,200,200))

    # Back icon
    try:
        BACK_ICON = pygame.image.load(resource_path("assets/images/back.png"))
        BACK_ICON = pygame.transform.smoothscale(BACK_ICON, (36,36))
    except:
        BACK_ICON = pygame.Surface((36,36))
        BACK_ICON.fill((200,120,120))

    # Bad swap sound
    try:
        BADSWAP_SOUND = pygame.mixer.Sound(resource_path("assets/sounds/badswap.wav"))
    except:
        BADSWAP_SOUND = None

    board = make_letter_board()
    score = 0
    last_word = ""
    last_meaning = None

    run_game_loop(player_name, board, score, last_word, last_meaning)



# ---------------- GAME LOOP ----------------
def run_game_loop(player_name, board, score, last_word, last_meaning):
    dragging = False
    path = []
    path_set = set()

    global BACK_BUTTON_RECT_GLOBAL
    BACK_BUTTON_RECT_GLOBAL = pygame.Rect(0,0,0,0)

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                if player_name:
                    try:
                        db_manager.update_high_score(player_name, score, mode="mode2")
                    except: pass
                pygame.quit(); sys.exit()

            elif event.type == KEYUP and event.key == K_ESCAPE:
                if player_name:
                    try:
                        db_manager.update_high_score(player_name, score, mode="mode2")
                    except: pass
                return

            elif event.type == MOUSEBUTTONDOWN:
                if _back_button_collide(event.pos):
                    if player_name:
                        try:
                            db_manager.update_high_score(player_name, score, mode="mode2")
                        except: pass
                    return

                pos = _tile_at_pixel(event.pos)
                if pos:
                    dragging = True
                    path = [pos]
                    path_set = {pos}

            elif event.type == MOUSEMOTION and dragging:
                pos = _tile_at_pixel(event.pos)
                if pos and pos not in path_set:
                    lx,ly = path[-1]
                    x,y = pos
                    if max(abs(lx-x), abs(ly-y)) <= 1:  # adjacent
                        path.append(pos); path_set.add(pos)

            elif event.type == MOUSEBUTTONUP and dragging:
                # Submit word
                word = "".join(board[x][y] for (x,y) in path if board[x][y])
                if len(word) >= 3:
                    entry = _get_word_entry(word.upper())
                    if entry:
                        score += SCORE_PER_LETTER * len(word)
                        try: speak_word(word, entry.get("audio_path"))
                        except: pass

                        remove_positions(board, path)
                        pull_down_letters(board)

                        last_word = word.upper()
                        last_meaning = entry.get("meaning")

                        if player_name:
                            try:
                                db_manager.update_high_score(player_name, score, mode="mode2")
                            except: pass
                    else:
                        if BADSWAP_SOUND:
                            try: BADSWAP_SOUND.play()
                            except: pass
                        _flash_invalid(path)
                else:
                    if BADSWAP_SOUND:
                        try: BADSWAP_SOUND.play()
                        except: pass
                    _flash_invalid(path)

                dragging = False
                path = []
                path_set = set()

        # DRAW
        _draw_frame(board, score, player_name, last_word, last_meaning)
        if path:
            _draw_path(path)

        pygame.display.update()
        FPSCLOCK.tick(FPS)


# ---------------- DRAWING ----------------
def _tile_at_pixel(pos):
    mx,my = pos
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if tile_rect(x,y).collidepoint(mx,my):
                return (x,y)
    return None

def _draw_frame(board, score, player_name, last_word, last_meaning):
    DISPLAYSURF.blit(SPACE_BG, (0,0))

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            r = tile_rect(x,y)
            pygame.draw.rect(DISPLAYSURF, DARK_BLUE, r, border_radius=8)
            pygame.draw.rect(DISPLAYSURF, LIGHT_BLUE, r, 2, border_radius=8)

            letter = board[x][y]
            if letter:
                font = pygame.font.Font('freesansbold.ttf', 28)
                surf = font.render(letter, True, WHITE)
                DISPLAYSURF.blit(surf, surf.get_rect(center=r.center))

    drawHUD_local(player_name, score, last_word, last_meaning)


# ---------------- PATH GLOW ----------------
def _draw_path(path):
    if len(path) >= 2:
        pts = [center_of_tile(x,y) for (x,y) in path]
        pygame.draw.lines(DISPLAYSURF, GLOW_COLOR, False, pts, 6)

    for (x,y) in path:
        r = tile_rect(x,y)
        glow = pygame.Surface((TILE_SIZE+12, TILE_SIZE+12), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*GLOW_COLOR, 70), (0,0,glow.get_width(),glow.get_height()))
        DISPLAYSURF.blit(glow, (r.x-6, r.y-6))


# ---------------- INVALID FLASH ----------------
def _flash_invalid(path):
    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
    overlay.set_alpha(160)
    overlay.fill(INVALID_COLOR)

    for _ in range(3):
        for (x,y) in path:
            DISPLAYSURF.blit(overlay, tile_rect(x,y))
        pygame.display.update()
        pygame.time.delay(80)
        pygame.display.update()
        pygame.time.delay(60)


# ---------------- HUD ----------------
def wrap_text(text, font, maxw):
    if not text: return []
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur+" "+w).strip()
        if font.size(test)[0] <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def drawHUD_local(player_name, score, last_word, last_meaning):
    hud_h = 150
    hud_y = WINDOWHEIGHT - hud_h - 30
    px = 30; py = 22
    width = WINDOWWIDTH - 40

    surf = pygame.Surface((width, hud_h), pygame.SRCALPHA)
    pygame.draw.rect(surf, HUD_BG, (0,0,width,hud_h), border_radius=24)
    pygame.draw.rect(surf, (255,255,255,40), (4,4,width-8,hud_h-8), border_radius=22, width=2)

    fb = pygame.font.Font("freesansbold.ttf", 24)
    fs = pygame.font.Font("freesansbold.ttf", 18)

    # Word + meaning
    surf.blit(fs.render("Word:", True, (240,240,250)), (px, py+2))
    surf.blit(fb.render(last_word or "-", True, (255,215,80)), (px+70, py))

    meaning = last_meaning or "Meaning not available."
    mx = px + 260
    lines = wrap_text(meaning, fs, width - mx - px)
    for i, line in enumerate(lines[:2]):
        surf.blit(fs.render(line, True, (200,200,200)), (mx, py + i*22))

    # Player + score + back
    by = py + 70
    surf.blit(PLAYER_ICON, (px, by-5))
    surf.blit(fb.render(player_name or "-", True, WHITE), (px+70, by))

    surf.blit(fs.render("Score:", True, WHITE), (px+260, by+2))
    surf.blit(fb.render(str(score), True, WHITE), (px+330, by))

    # back icon
    back_x = width - 60
    surf.blit(BACK_ICON, (back_x, by-6))

    DISPLAYSURF.blit(surf, (20, hud_y))

    global BACK_BUTTON_RECT_GLOBAL
    BACK_BUTTON_RECT_GLOBAL = pygame.Rect(20+back_x, hud_y+by-6, BACK_ICON.get_width(), BACK_ICON.get_height())


def _back_button_collide(pos):
    try:
        return BACK_BUTTON_RECT_GLOBAL.collidepoint(pos)
    except:
        return False


# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
