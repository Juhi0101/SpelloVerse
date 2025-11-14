# main.py — SpelloVerse Main Menu
import sys, os, threading
sys.path.append(os.path.dirname(__file__))

import pygame, time
from pygame.locals import *
from systems import db_manager

# PyInstaller-friendly asset path
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

# Window + visuals
WINDOWWIDTH, WINDOWHEIGHT = 900, 820
FPS = 60

WHITE = (255,255,255)
PASTEL_PINK = (245,180,215)
CYAN = (150,190,255)

# Simple glow text effect
def glow_text(text, font, base_color=WHITE, glow_color=PASTEL_PINK):
    main = font.render(text, True, base_color)
    glow = font.render(text, True, glow_color)
    w, h = main.get_size()
    surf = pygame.Surface((w+8, h+8), pygame.SRCALPHA)
    offsets = [(-2,0),(2,0),(0,-2),(0,2)]
    for ox, oy in offsets:
        surf.blit(glow, (ox+4, oy+4))
    surf.blit(main, (4,4))
    return surf

# Pygame setup
pygame.init()
DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
pygame.display.set_caption("SpelloVerse")
CLOCK = pygame.time.Clock()

# Fonts
TITLE_FONT = pygame.font.Font("freesansbold.ttf", 54)
MENU_FONT  = pygame.font.Font("freesansbold.ttf", 40)
INPUT_FONT = pygame.font.Font("freesansbold.ttf", 32)
SMALL_FONT = pygame.font.Font("freesansbold.ttf", 20)

# Background
try:
    SPACE_BG = pygame.image.load(resource_path("assets/bg/space.png"))
    SPACE_BG = pygame.transform.scale(SPACE_BG, (WINDOWWIDTH, WINDOWHEIGHT))
except Exception:
    SPACE_BG = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT))
    SPACE_BG.fill((10,10,20))

# ---- Dataset handling ----
def _count_words_safe():
    try:
        return db_manager.count_words()
    except:
        return 0

def _build_dataset_safe(progress_callback=None):
    try:
        from data.generate_word_dataset import build_dataset
    except Exception:
        return False
    try:
        build_dataset(progress_callback=progress_callback)
        return True
    except Exception:
        return False

# Small loading animation
def _play_quick_loading_animation(duration_ms=700):
    dots = ["", ".", "..", "...", "....", "....."]
    idx = 0
    font = pygame.font.Font("freesansbold.ttf", 36)
    end = pygame.time.get_ticks() + duration_ms

    star_x = WINDOWWIDTH//2 + 160
    star_y = WINDOWHEIGHT//2 - 40

    while pygame.time.get_ticks() < end:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        msg = "Preparing SpelloVerse" + dots[idx]
        txt = glow_text(msg, font)
        rect = txt.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT//2))
        DISPLAYSURF.blit(txt, rect)

        pygame.draw.circle(DISPLAYSURF, (255,255,180), (star_x, star_y), 1 + (idx % 3))
        pygame.display.update()
        idx = (idx + 1) % len(dots)
        pygame.time.delay(110)

# Animated DB builder
def _run_live_build_with_animation():
    done = {"val": False}

    def worker():
        _build_dataset_safe()
        done["val"] = True

    threading.Thread(target=worker, daemon=True).start()

    dots = ["", ".", "..", "...", "....", "....."]
    idx = 0
    font = pygame.font.Font("freesansbold.ttf", 34)

    while not done["val"]:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        msg = f"Floating through galaxies to fetch words{dots[idx]}"
        txt = glow_text(msg, font)
        DISPLAYSURF.blit(txt, txt.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT//2)))

        for i in range(6):
            pygame.draw.circle(
                DISPLAYSURF, (200,200,255),
                (WINDOWWIDTH//2 - 60 + i*20, WINDOWHEIGHT//2 + 60),
                2 + (idx % 2)
            )

        pygame.display.update()
        idx = (idx + 1) % len(dots)
        pygame.time.delay(120)

    _play_quick_loading_animation(400)

def ensure_word_dataset():
    count = _count_words_safe()
    if count > 0:
        _play_quick_loading_animation(700)
        return
    _run_live_build_with_animation()

# ---- Main Menu ----
CURRENT_PLAYER = None

def main_menu():
    global CURRENT_PLAYER
    options = ["Play", "Players", "Leaderboard", "Exit"]
    selected = 0
    start_y = 260; gap = 70

    while True:
        DISPLAYSURF.blit(SPACE_BG, (0,0))

        title_surf = glow_text("SpelloVerse", TITLE_FONT)
        DISPLAYSURF.blit(title_surf, title_surf.get_rect(center=(WINDOWWIDTH//2, 120)))

        cur_text = f"Current: {CURRENT_PLAYER}" if CURRENT_PLAYER else "Current: (none)"
        cur_surf = glow_text(cur_text, SMALL_FONT)
        DISPLAYSURF.blit(cur_surf, cur_surf.get_rect(topright=(WINDOWWIDTH - 28, 20)))

        for i, text in enumerate(options):
            color = WHITE if i == selected else CYAN
            surf = glow_text(text, MENU_FONT, base_color=color)
            DISPLAYSURF.blit(surf, surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap)))

        hint = glow_text("Use up / down • ENTER to choose • Mouse supported", SMALL_FONT)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT - 50)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == K_RETURN:
                    if selected == 0: mode_select_screen()
                    elif selected == 1: player_manager_screen()
                    elif selected == 2: leaderboard_screen()
                    elif selected == 3: pygame.quit(); sys.exit()

            if event.type == MOUSEBUTTONUP:
                mx,my = event.pos
                for i in range(len(options)):
                    surf = MENU_FONT.render(options[i], True, WHITE)
                    rect = surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap))
                    if rect.collidepoint(mx,my):
                        if i == 0: mode_select_screen()
                        elif i == 1: player_manager_screen()
                        elif i == 2: leaderboard_screen()
                        elif i == 3: pygame.quit(); sys.exit()

# ---- Mode Selection ----
def mode_select_screen():
    options = ["Mode 1 — Gem Reveal", "Mode 2 — Trail Spell", "Back"]
    selected = 0
    start_y = 260; gap = 70

    while True:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        title = glow_text("Choose a Mode", TITLE_FONT)
        DISPLAYSURF.blit(title, title.get_rect(center=(WINDOWWIDTH//2, 140)))

        for i, t in enumerate(options):
            color = WHITE if i == selected else CYAN
            surf = glow_text(t, MENU_FONT, base_color=color)
            DISPLAYSURF.blit(surf, surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap)))

        hint = glow_text("up / down • ENTER select • ESC back", SMALL_FONT, base_color=CYAN)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT - 70)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == K_RETURN:
                    if selected == 0: _start_mode("mode1")
                    elif selected == 1: _start_mode("mode2")
                    elif selected == 2: return
                elif event.key == K_ESCAPE:
                    return
            if event.type == MOUSEBUTTONUP:
                mx,my = event.pos
                for i in range(len(options)):
                    surf = MENU_FONT.render(options[i], True, WHITE)
                    rect = surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap))
                    if rect.collidepoint(mx,my):
                        if i == 0: _start_mode("mode1")
                        elif i == 1: _start_mode("mode2")
                        elif i == 2: return

def _start_mode(mode_name):
    global CURRENT_PLAYER
    if CURRENT_PLAYER is None:
        picked = select_player_screen()
        if not picked:
            return
        CURRENT_PLAYER = picked

    try:
        if mode_name == "mode1":
            from modes import mode1
            mode1.main(CURRENT_PLAYER)
        elif mode_name == "mode2":
            from modes import mode2
            mode2.main(CURRENT_PLAYER)
    except Exception as e:
        print("Failed launching mode:", e)

# ---- Player Selection + Manager ----
def _safe_get_players():
    try:
        rows = db_manager.get_all_players()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append(r)
            elif isinstance(r, (list,tuple)):
                name = r[0]
                hs = r[1] if len(r) > 1 else 0
                out.append({"name": name, "high_score": hs})
            else:
                out.append({"name": str(r), "high_score": 0})
        return out
    except:
        return []

def select_player_screen():
    players = _safe_get_players()
    if not players:
        prompt_no_players()
        return None

    selected = 0
    start_y = 240; gap = 56

    while True:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        title = glow_text("Select Player", TITLE_FONT)
        DISPLAYSURF.blit(title, title.get_rect(center=(WINDOWWIDTH//2, 120)))

        for i,p in enumerate(players):
            color = WHITE if i==selected else CYAN
            surf = glow_text(p["name"], MENU_FONT, base_color=color)
            DISPLAYSURF.blit(surf, surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap)))

        hint = glow_text("ENTER select • A add • D delete • ESC back", SMALL_FONT, base_color=CYAN)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT - 50)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                return None
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected - 1) % len(players)
                elif event.key == K_DOWN:
                    selected = (selected + 1) % len(players)
                elif event.key == K_RETURN:
                    return players[selected]["name"]
                elif event.key == K_a:
                    add_player_screen()
                    players = _safe_get_players()
                    selected = min(selected, max(0, len(players)-1))
                elif event.key == K_d:
                    name = players[selected]["name"]
                    db_manager.delete_player(name)
                    players = _safe_get_players()
                    if not players:
                        prompt_no_players()
                        return None
                    selected = min(selected, len(players)-1)
                elif event.key == K_ESCAPE:
                    return None

def player_manager_screen():
    global CURRENT_PLAYER
    selected = 0

    while True:
        players = _safe_get_players()
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        title = glow_text("Player Manager", TITLE_FONT)
        DISPLAYSURF.blit(title, title.get_rect(center=(WINDOWWIDTH//2, 120)))

        if not players:
            txt = glow_text("No players yet. Press A to add.", MENU_FONT)
            DISPLAYSURF.blit(txt, txt.get_rect(center=(WINDOWWIDTH//2, 380)))
        else:
            start_y = 240; gap = 52
            for i,p in enumerate(players):
                label = p["name"]
                if CURRENT_PLAYER == p["name"]:
                    label = f"{label}  (current)"
                color = WHITE if i==selected else CYAN
                surf = glow_text(label, MENU_FONT, base_color=color)
                DISPLAYSURF.blit(surf, surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap)))

        hint = glow_text("ENTER select • A add • D delete • ESC back", SMALL_FONT, base_color=CYAN)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT - 50)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN:
                players = _safe_get_players()
                if event.key == K_UP and players:
                    selected = (selected - 1) % len(players)
                elif event.key == K_DOWN and players:
                    selected = (selected + 1) % len(players)
                elif event.key == K_RETURN and players:
                    CURRENT_PLAYER = players[selected]["name"]
                    return
                elif event.key == K_a:
                    add_player_screen()
                elif event.key == K_d and players:
                    db_manager.delete_player(players[selected]["name"])
                elif event.key == K_ESCAPE:
                    return

def add_player_screen():
    name = ""
    cursor = True
    tick = 0

    while True:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        title = glow_text("New Player Name", TITLE_FONT)
        DISPLAYSURF.blit(title, title.get_rect(center=(WINDOWWIDTH//2, 120)))

        box_rect = pygame.Rect(WINDOWWIDTH//2 - 260, 300, 520, 64)
        box_surf = pygame.Surface((box_rect.w, box_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (20,20,30,200), (0,0,box_rect.w, box_rect.h), border_radius=10)
        DISPLAYSURF.blit(box_surf, (box_rect.x, box_rect.y))

        tick += 1
        if tick % 30 == 0:
            cursor = not cursor

        display_name = name + ("|" if cursor else "")
        txt = glow_text(display_name, INPUT_FONT)
        DISPLAYSURF.blit(txt, txt.get_rect(center=(WINDOWWIDTH//2, 330)))

        hint = glow_text("ENTER save • ESC cancel", SMALL_FONT, base_color=CYAN)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, 420)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN:
                if event.key == K_RETURN and name.strip():
                    db_manager.add_player(name.strip())
                    return
                elif event.key == K_BACKSPACE:
                    name = name[:-1]
                elif event.key == K_ESCAPE:
                    return
                else:
                    if len(name) < 20 and event.unicode.isprintable():
                        name += event.unicode

def prompt_no_players():
    timer = pygame.time.get_ticks() + 700
    while pygame.time.get_ticks() < timer:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        msg = glow_text("No players found. Use Player Manager to add.", MENU_FONT)
        DISPLAYSURF.blit(msg, msg.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT//2)))
        pygame.display.update()
        CLOCK.tick(FPS)

# ---- Leaderboard ----
def leaderboard_screen():
    try:
        players = db_manager.get_all_players()
    except:
        players = []

    players = sorted(
        players,
        key=lambda p: (p.get("mode1_high_score") or 0) + (p.get("mode2_high_score") or 0),
        reverse=True
    )

    while True:
        DISPLAYSURF.blit(SPACE_BG, (0,0))
        title = glow_text("Leaderboard", TITLE_FONT)
        DISPLAYSURF.blit(title, title.get_rect(center=(WINDOWWIDTH//2, 120)))

        if not players:
            txt = glow_text("No players yet.", MENU_FONT)
            DISPLAYSURF.blit(txt, txt.get_rect(center=(WINDOWWIDTH//2, 400)))
        else:
            start_y = 240; gap = 55
            for i,p in enumerate(players[:10]):
                name = p.get("name", "Unknown")
                m1 = p.get("mode1_high_score") or 0
                m2 = p.get("mode2_high_score") or 0
                line = f"{i+1}. {name} — M1: {m1}   M2: {m2}"
                surf = glow_text(line, MENU_FONT)
                DISPLAYSURF.blit(surf, surf.get_rect(center=(WINDOWWIDTH//2, start_y + i*gap)))

        hint = glow_text("ESC to return", SMALL_FONT, base_color=CYAN)
        DISPLAYSURF.blit(hint, hint.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT - 80)))

        pygame.display.update()
        CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

# ---- Startup ----
if __name__ == "__main__":
    _play_quick_loading_animation(700)

    try:
        ensure_word_dataset()
    except Exception as e:
        print("Dataset init failed:", e)

    main_menu()
