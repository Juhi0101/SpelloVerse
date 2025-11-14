# modes/mode1.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random, time, pygame, sys, copy
from pygame.locals import *
from systems import db_manager
from systems.audio import speak_word

# ---------------- PATH FIX FOR PYINSTALLER ----------------
def resource_path(relative_path):
    """Get absolute path for PyInstaller or normal environment."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path


# ---------------- CONSTANTS ----------------
FPS = 30
WINDOWWIDTH, WINDOWHEIGHT = 900, 820
BOARDWIDTH, BOARDHEIGHT = 8, 8
GEMIMAGESIZE = 64
NUMGEMIMAGES = 7
NUMMATCHSOUNDS = 6
MOVERATE = 25
DEDUCTSPEED = 0.8

PURPLE = (255, 0, 255)
LIGHTBLUE = (170, 190, 255)
BLUE = (255, 255, 255)
RED = (255, 100, 100)
BLACK = (0, 0, 0)
BROWN = (85, 65, 0)
BRIGHTRED = (255, 0, 0)

HIGHLIGHTCOLOR = PURPLE
BGCOLOR = LIGHTBLUE
GRIDCOLOR = BLUE
GAMEOVERCOLOR = RED
GAMEOVERBGCOLOR = BLACK
SCORECOLOR = BROWN

XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = 60

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
EMPTY_SPACE = -1
ROWABOVEBOARD = "row above board"


# ---------------- STATIC ASSETS (Safe paths) ----------------
SPACE_BG = pygame.image.load(resource_path("assets/bg/space.png"))
SPACE_BG = pygame.transform.scale(SPACE_BG, (WINDOWWIDTH, WINDOWHEIGHT))

PLAYER_ICON = pygame.image.load(resource_path("assets/images/player.png"))
PLAYER_ICON = pygame.transform.smoothscale(PLAYER_ICON, (32, 32))

BACK_ICON = pygame.image.load(resource_path("assets/images/back.png"))
BACK_ICON = pygame.transform.smoothscale(BACK_ICON, (36, 36))


# ---------------- GLOBAL INIT ----------------
def main(player_name=None):
    global FPSCLOCK, DISPLAYSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS, BACK_BUTTON_RECT

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("SpelloVerse — Mode 1")
    BASICFONT = pygame.font.Font("freesansbold.ttf", 20)

    # ---------------- GEM IMAGES (Fixed paths) ----------------

    GEMIMAGES = []
    # fraction of tile to use for the inner gem graphic (tweak 0.5..0.85)
    INNER_FRACTION = 0.80
    inner_max = int(GEMIMAGESIZE * INNER_FRACTION)

    for i in range(1, NUMGEMIMAGES + 1):
        path = resource_path(f"assets/images/gem{i}.png")
        try:
            raw_img = pygame.image.load(path).convert_alpha()
        except Exception:
            # fallback grey tile
            tile = pygame.Surface((GEMIMAGESIZE, GEMIMAGESIZE), pygame.SRCALPHA)
            tile.fill((150, 150, 150))
            GEMIMAGES.append(tile)
            continue

        # get raw size
        rw, rh = raw_img.get_size()

        # If the source image is already exactly the tile size but the gem inside is too big,
        # we'll still shrink the inner graphic. Compute scale so the gem fits within inner_max.
        scale_factor = min(1.0, inner_max / max(rw, rh))

        target_w = max(1, int(rw * scale_factor))
        target_h = max(1, int(rh * scale_factor))

        # If the source is larger than tile (rare), clamp to GEMIMAGESIZE as absolute max
        if target_w > GEMIMAGESIZE or target_h > GEMIMAGESIZE:
            sf = min(GEMIMAGESIZE / rw, GEMIMAGESIZE / rh)
            target_w, target_h = int(rw * sf), int(rh * sf)

        # Smooth scale the inner graphic
        try:
            inner = pygame.transform.smoothscale(raw_img, (target_w, target_h))
        except Exception:
            inner = pygame.transform.scale(raw_img, (target_w, target_h))

        # Create a transparent tile and blit the inner graphic centered
        tile = pygame.Surface((GEMIMAGESIZE, GEMIMAGESIZE), pygame.SRCALPHA)
        cx = (GEMIMAGESIZE - target_w) // 2
        cy = (GEMIMAGESIZE - target_h) // 2
        tile.blit(inner, (cx, cy))

        GEMIMAGES.append(tile)


    # ---------------- SOUNDS (Fixed paths) ----------------
    GAMESOUNDS = {}
    try:
        GAMESOUNDS["bad swap"] = pygame.mixer.Sound(
            resource_path("assets/sounds/badswap.wav")
        )
        GAMESOUNDS["match"] = [
            pygame.mixer.Sound(resource_path(f"assets/sounds/match{i}.wav"))
            for i in range(NUMMATCHSOUNDS)
        ]
    except Exception:
        GAMESOUNDS["bad swap"] = None
        GAMESOUNDS["match"] = []

    # ---------------- BOARD RECTS ----------------
    BOARDRECTS = [
        [
            pygame.Rect(
                (XMARGIN + (x * GEMIMAGESIZE),
                 YMARGIN + (y * GEMIMAGESIZE),
                 GEMIMAGESIZE, GEMIMAGESIZE)
            )
            for y in range(BOARDHEIGHT)
        ]
        for x in range(BOARDWIDTH)
    ]

    runGame(player_name)





# ---------------- MAIN GAME LOOP ----------------
def runGame(player_name=None):
    gameBoard = getBlankBoard()
    score = 0
    fillBoardAndAnimate(gameBoard, [], score)
    firstSelectedGem = None
    lastMouseDownX = lastMouseDownY = None
    gameIsOver = False
    lastScoreDeduction = time.time()
    clickContinueTextSurf = None

    # HUD state
    last_word = ""
    last_meaning = None

    while True:
        clickedSpace = None
        for event in pygame.event.get():
            if event.type == QUIT:
                # on window close, save score and exit to OS
                if player_name:
                    try:
                        db_manager.update_high_score(player_name, score, mode="mode1")
                    except Exception:
                        pass
                pygame.quit(); sys.exit()

            
            elif event.type == KEYUP and event.key == K_ESCAPE:
                # Save high score then return to main menu
                if player_name:
                    try:
                        db_manager.update_high_score(player_name, score, mode="mode1")
                    except Exception:
                        pass
                return

            elif event.type == KEYUP and event.key == K_BACKSPACE:
                # Return to main menu (older behaviour)
                if player_name:
                    try:
                        db_manager.update_high_score(player_name, score, mode="mode1")
                    except Exception:
                        pass
                return

            elif event.type == MOUSEBUTTONUP:
                mx, my = event.pos
            
                # 1️ Check Back button click first
                if BACK_BUTTON_RECT.collidepoint(event.pos):
                    if player_name:
                        try:
                            db_manager.update_high_score(player_name, score, mode="mode1")
                        except:
                            pass
                    return  # go back to main menu
            
                # 2 If game finished → click returns to menu
                if gameIsOver:
                    if player_name:
                        try:
                            db_manager.update_high_score(player_name, score, mode="mode1")
                        except:
                            pass
                    return
            
                # 3️ Normal board click / drag detection
                if (mx, my) == (lastMouseDownX, lastMouseDownY):
                    clickedSpace = checkForGemClick(event.pos)
                else:
                    firstSelectedGem = checkForGemClick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForGemClick(event.pos)
                    if not firstSelectedGem or not clickedSpace:
                        firstSelectedGem = None
                        clickedSpace = None



            elif event.type == MOUSEBUTTONDOWN:
                lastMouseDownX, lastMouseDownY = event.pos

        if clickedSpace and not firstSelectedGem:
            firstSelectedGem = clickedSpace
        elif clickedSpace and firstSelectedGem:
            firstSwappingGem, secondSwappingGem = getSwappingGems(gameBoard, firstSelectedGem, clickedSpace)
            if not firstSwappingGem:
                firstSelectedGem = None; continue

            boardCopy = getBoardCopyMinusGems(gameBoard, (firstSwappingGem, secondSwappingGem))
            animateMovingGems(
                boardCopy,
                [firstSwappingGem, secondSwappingGem],
                [],
                score,
                player_name,
                last_word,
                last_meaning
            )


            ax, ay = firstSwappingGem['x'], firstSwappingGem['y']
            bx, by = secondSwappingGem['x'], secondSwappingGem['y']
            gameBoard[ax][ay], gameBoard[bx][by] = gameBoard[bx][by], gameBoard[ax][ay]

            matchedGems = findMatchingGems(gameBoard)
            if matchedGems == []:
                if GAMESOUNDS['bad swap']: GAMESOUNDS['bad swap'].play()
                animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)
                gameBoard[ax][ay], gameBoard[bx][by] = gameBoard[bx][by], gameBoard[ax][ay]
            else:
                # This was a matching move.
                while matchedGems != []:
                    points = []
                    for gemSet in matchedGems:
                        if not gemSet: continue
                        ys = [p[1] for p in gemSet]; xs = [p[0] for p in gemSet]
                        ordered = sorted(gemSet, key=lambda g: g[0] if len(set(ys)) == 1 else g[1])
                        L = len(ordered)

                        # get a word from DB of this length
                        word_info = db_manager.get_word_of_length(L)
                        if not word_info:
                            word = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(L))
                            meaning = None
                            audio_path = None
                        else:
                            word = word_info.get("word", ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(L)))
                            meaning = word_info.get("meaning")
                            audio_path = word_info.get("audio_path")

                        # show the word and speak it
                        showWordOverGems(gameBoard, ordered, word, audio_path)

                        # update score add
                        score_add = (10 + (L - 3) * 10)
                        score += score_add

                        # save score incrementally to DB so we don't lose progress
                        if player_name:
                            try:
                                db_manager.update_high_score(player_name, score, mode="mode1")
                            except Exception:
                                pass

                        # remove gems
                        for gem in gemSet:
                            gameBoard[gem[0]][gem[1]] = EMPTY_SPACE

                        last_word = word
                        last_meaning = meaning
                        points.append({'points': score_add,
                                       'x': gemSet[0][0]*GEMIMAGESIZE + XMARGIN,
                                       'y': gemSet[0][1]*GEMIMAGESIZE + YMARGIN})

                    if GAMESOUNDS['match']: random.choice(GAMESOUNDS['match']).play()
                    # Drop the new gems.
                    fillBoardAndAnimate(gameBoard, points, score)
                    # Check for chain matches
                    matchedGems = findMatchingGems(gameBoard)

            firstSelectedGem = None
            # Instead of game over → reshuffle until solvable
            if not canMakeMove(gameBoard):
                # Show reshuffle message
                reshuffleFont = pygame.font.Font('freesansbold.ttf', 36)
                reshuffleSurf = reshuffleFont.render("No moves! Reshuffling…", True, (255, 255, 0), (50, 50, 50))
                reshuffleRect = reshuffleSurf.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT//2))
                DISPLAYSURF.blit(reshuffleSurf, reshuffleRect)
                pygame.display.update()
                pygame.time.delay(900)
            
                # Perform a random reshuffle until solvable
                while True:
                    random.shuffle(gameBoard)
                    # Also shuffle inside each column for more randomness
                    for col in gameBoard:
                        random.shuffle(col)
                    if canMakeMove(gameBoard):
                        break
                    
                continue  # go back into main loop


        # Draw the board and HUD.
        _draw_full_frame(gameBoard, score, player_name, last_word, last_meaning)

        if firstSelectedGem:
            highlightSpace(firstSelectedGem['x'], firstSelectedGem['y'])

        if gameIsOver:
            if clickContinueTextSurf == None:
                clickContinueTextSurf = BASICFONT.render(
                    f'Final Score: {score} (Click to continue)', 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
                rect = clickContinueTextSurf.get_rect(center=(WINDOWWIDTH//2, WINDOWHEIGHT//2))
            DISPLAYSURF.blit(clickContinueTextSurf, rect)

            if player_name:
                try:
                    db_manager.update_high_score(player_name, score, mode="mode1")
                except Exception:
                    pass

        pygame.display.update()
        FPSCLOCK.tick(FPS)






def _draw_full_frame(board, score, player_name, last_word, last_meaning):
    # draw static background
    DISPLAYSURF.blit(SPACE_BG, (0, 0))

    # draw board
    drawBoard(board)

    # draw HUD
    drawHUD(player_name, score, last_word, last_meaning)







def flashGems(board, gemSet, flashes=3, color=(255, 215, 0), intensity=70,
              score=0, player_name=None, last_word="", last_meaning=None):
    """Flash all gems in gemSet together instead of one at a time."""
    
    overlay = pygame.Surface((GEMIMAGESIZE, GEMIMAGESIZE))
    overlay.set_alpha(intensity)
    overlay.fill(color)

    for _ in range(flashes):
        # flash ON
        _draw_full_frame(board, score, player_name, last_word, last_meaning)  
        for (x, y) in gemSet:
            DISPLAYSURF.blit(overlay, BOARDRECTS[x][y])
        pygame.display.update()
        pygame.time.delay(80)

        # flash OFF
        _draw_full_frame(board, score, player_name, last_word, last_meaning)
        pygame.display.update()
        pygame.time.delay(80)




# ---------------- WORD HELPERS ----------------
def showWordOverGems(board, gemSet, word, audio_path=None,
                     player_name=None, score=0, last_word="", last_meaning=None):

    # 1️⃣ Flash all gems (subtle)
    flashGems(board, gemSet, flashes=2, color=(255, 215, 0), intensity=70,
              score=score, player_name=player_name,
              last_word=last_word, last_meaning=last_meaning)

    # 2️⃣ Glow letter pop
    font = pygame.font.Font('freesansbold.ttf', 38)

    def draw_letters(scale=1.0):
        _draw_full_frame(board, score, player_name, last_word, last_meaning)
        for (pos, ch) in zip(gemSet, word):
            x, y = pos
            # main letter
            letter = font.render(ch, True, (255, 255, 255))

            # glow: render blurred layers
            glow = font.render(ch, True, (255, 200, 200))
            for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
                DISPLAYSURF.blit(glow, glow.get_rect(center=(BOARDRECTS[x][y].centerx+ox,
                                                              BOARDRECTS[x][y].centery+oy)))

            # scaled bounce
            w, h = letter.get_size()
            scaled = pygame.transform.smoothscale(letter, (int(w*scale), int(h*scale)))
            rect = scaled.get_rect(center=BOARDRECTS[x][y].center)
            DISPLAYSURF.blit(scaled, rect)

        pygame.display.update()

    # small bounce sequence
    for s in [0.8, 1.0, 1.15, 1.0]:
        draw_letters(scale=s)
        pygame.time.delay(90)

    # 3️⃣ Speak word
    try:
        speak_word(word, audio_path)
    except:
        pass

    # 4️⃣ Hold with glow visible (2 seconds)
    end_time = pygame.time.get_ticks() + 2000
    while pygame.time.get_ticks() < end_time:
        draw_letters(scale=1.0)
        FPSCLOCK.tick(FPS)




# ---------------- GEMGEM FUNCTIONS ----------------
def getSwappingGems(board, firstXY, secondXY):
    fx, fy = firstXY['x'], firstXY['y']
    sx, sy = secondXY['x'], secondXY['y']
    if abs(fx - sx) + abs(fy - sy) != 1: return None, None
    firstGem = {'x': fx, 'y': fy, 'imageNum': board[fx][fy]}
    secondGem = {'x': sx, 'y': sy, 'imageNum': board[sx][sy]}
    if fx == sx + 1: firstGem['direction'], secondGem['direction'] = LEFT, RIGHT
    elif fx == sx - 1: firstGem['direction'], secondGem['direction'] = RIGHT, LEFT
    elif fy == sy + 1: firstGem['direction'], secondGem['direction'] = UP, DOWN
    elif fy == sy - 1: firstGem['direction'], secondGem['direction'] = DOWN, UP
    return firstGem, secondGem

def getBlankBoard():
    return [[EMPTY_SPACE]*BOARDHEIGHT for _ in range(BOARDWIDTH)]

def canMakeMove(board):
    oneOffPatterns = (((0,1), (1,0), (2,0)),
                      ((0,1), (1,1), (2,0)),
                      ((0,0), (1,1), (2,0)),
                      ((0,1), (1,0), (2,1)),
                      ((0,0), (1,0), (2,1)),
                      ((0,0), (1,1), (2,1)),
                      ((0,0), (0,2), (0,3)),
                      ((0,0), (0,1), (0,3)))
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatterns:
                if (getGemAt(board, x+pat[0][0], y+pat[0][1]) ==
                    getGemAt(board, x+pat[1][0], y+pat[1][1]) ==
                    getGemAt(board, x+pat[2][0], y+pat[2][1]) != None) or \
                   (getGemAt(board, x+pat[0][1], y+pat[0][0]) ==
                    getGemAt(board, x+pat[1][1], y+pat[1][0]) ==
                    getGemAt(board, x+pat[2][1], y+pat[2][0]) != None):
                    return True
    return False

def drawMovingGem(gem, progress):
    movex = movey = 0
    progress *= 0.01
    if gem['direction'] == UP: movey = -int(progress * GEMIMAGESIZE)
    elif gem['direction'] == DOWN: movey = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == RIGHT: movex = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == LEFT: movex = -int(progress * GEMIMAGESIZE)
    basex, basey = gem['x'], gem['y']
    if basey == ROWABOVEBOARD: basey = -1
    pixelx = XMARGIN + (basex * GEMIMAGESIZE)
    pixely = YMARGIN + (basey * GEMIMAGESIZE)
    DISPLAYSURF.blit(GEMIMAGES[gem['imageNum']], (pixelx + movex, pixely + movey))

def pullDownAllGems(board):
    for x in range(BOARDWIDTH):
        gemsInColumn = [board[x][y] for y in range(BOARDHEIGHT) if board[x][y] != EMPTY_SPACE]
        board[x] = ([EMPTY_SPACE]*(BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn

def getGemAt(board, x, y):
    return None if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT else board[x][y]

def getDropSlots(board):
    boardCopy = copy.deepcopy(board)
    pullDownAllGems(boardCopy)
    dropSlots = [[] for _ in range(BOARDWIDTH)]
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-1, -1, -1):
            if boardCopy[x][y] == EMPTY_SPACE:
                possible = list(range(len(GEMIMAGES)))
                for ox, oy in ((0,-1),(1,0),(0,1),(-1,0)):
                    n = getGemAt(boardCopy, x+ox, y+oy)
                    if n in possible: possible.remove(n)
                newGem = random.choice(possible)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)
    return dropSlots

def findMatchingGems(board):
    gemsToRemove = []
    bcopy = copy.deepcopy(board)
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if getGemAt(bcopy,x,y)==getGemAt(bcopy,x+1,y)==getGemAt(bcopy,x+2,y)!=EMPTY_SPACE:
                t=bcopy[x][y];offset=0;rem=[]
                while getGemAt(bcopy,x+offset,y)==t:
                    rem.append((x+offset,y));bcopy[x+offset][y]=EMPTY_SPACE;offset+=1
                gemsToRemove.append(rem)
            if getGemAt(bcopy,x,y)==getGemAt(bcopy,x,y+1)==getGemAt(bcopy,x,y+2)!=EMPTY_SPACE:
                t=bcopy[x][y];offset=0;rem=[]
                while getGemAt(bcopy,x,y+offset)==t:
                    rem.append((x,y+offset));bcopy[x][y+offset]=EMPTY_SPACE;offset+=1
                gemsToRemove.append(rem)
    return gemsToRemove

def highlightSpace(x, y):
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)

def getDroppingGems(board):
    bcopy = copy.deepcopy(board)
    dropping = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-2, -1, -1):
            if bcopy[x][y+1]==EMPTY_SPACE and bcopy[x][y]!=EMPTY_SPACE:
                dropping.append({'imageNum':bcopy[x][y],'x':x,'y':y,'direction':DOWN})
                bcopy[x][y]=EMPTY_SPACE
    return dropping

def animateMovingGems(board, movingGems, pointsText, score,
                      player_name=None, last_word="", last_meaning=""):
    """
    Smooth animation: background → board → HUD → moving gems → points text.
    """
    progress = 0
    while progress < 100:
        # draw full frame (bg + board + hud + score)
        _draw_full_frame(board, score, player_name, last_word, last_meaning)

        # draw moving gems
        for gem in movingGems:
            drawMovingGem(gem, progress)

        # draw floating score text (points)
        for p in pointsText:
            ps = BASICFONT.render(str(p['points']), True, SCORECOLOR)
            pr = ps.get_rect(center=(p['x'], p['y']))
            DISPLAYSURF.blit(ps, pr)

        pygame.display.update()
        FPSCLOCK.tick(FPS)
        progress += MOVERATE



def moveGems(board, moving):
    for g in moving:
        if g['y']!=ROWABOVEBOARD:
            board[g['x']][g['y']]=EMPTY_SPACE
            dx=dy=0
            if g['direction']==LEFT:dx=-1
            elif g['direction']==RIGHT:dx=1
            elif g['direction']==DOWN:dy=1
            elif g['direction']==UP:dy=-1
            board[g['x']+dx][g['y']+dy]=g['imageNum']
        else:
            board[g['x']][0]=g['imageNum']

def fillBoardAndAnimate(board, points, score,
                        player_name=None, last_word="", last_meaning=""):
    dropSlots = getDropSlots(board)

    while dropSlots != [[]] * BOARDWIDTH:
        moving = getDroppingGems(board)

        for x in range(len(dropSlots)):
            if dropSlots[x]:
                moving.append({
                    'imageNum': dropSlots[x][0],
                    'x': x,
                    'y': ROWABOVEBOARD,
                    'direction': DOWN
                })

        boardCopy = getBoardCopyMinusGems(board, moving)

        # IMPORTANT: pass HUD state into animations
        animateMovingGems(
            boardCopy,
            moving,
            points,
            score,
            player_name,
            last_word,
            last_meaning
        )

        moveGems(board, moving)

        for x in range(len(dropSlots)):
            if dropSlots[x]:
                board[x][0] = dropSlots[x][0]
                del dropSlots[x][0]


def checkForGemClick(pos):
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0],pos[1]):
                return {'x':x,'y':y}
    return None

def drawBoard(board):
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            gem=board[x][y]
            if gem!=EMPTY_SPACE:
                DISPLAYSURF.blit(GEMIMAGES[gem], BOARDRECTS[x][y])

def getBoardCopyMinusGems(board,gems):
    bcopy=copy.deepcopy(board)
    for g in gems:
        if g['y']!=ROWABOVEBOARD:
            bcopy[g['x']][g['y']]=EMPTY_SPACE
    return bcopy




def wrap_text(text, font, max_width):
    if not text:
        return []
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines



# ---------------- HUD ----------------
def drawHUD(player_name, score, last_word, last_meaning):
    hud_height = 150
    hud_y = WINDOWHEIGHT - hud_height - 30
    padding_x = 30
    padding_y = 22
    width = WINDOWWIDTH - 40

    # Transparent glass HUD surface
    hud_surface = pygame.Surface((width, hud_height), pygame.SRCALPHA)
    pygame.draw.rect(hud_surface, (35, 35, 55, 165),
                     (0, 0, width, hud_height), border_radius=24)
    pygame.draw.rect(hud_surface, (255, 255, 255, 55),
                     (4, 4, width-8, hud_height-8), border_radius=22, width=2)

    # Fonts
    font_big = pygame.font.Font('freesansbold.ttf', 24)
    font_small = pygame.font.Font('freesansbold.ttf', 18)

    # ------------------------------------------------
    # 🌌 TOP ROW — WORD + MEANING
    # ------------------------------------------------
    top_y = padding_y

    # Word label (separate)
    word_label = font_small.render("Word:", True, (240, 240, 250))
    hud_surface.blit(word_label, (padding_x, top_y+2))

    # Word value (separate)
    word_value = font_big.render(last_word or "-", True, (255, 215, 80))
    hud_surface.blit(word_value, (padding_x + 70, top_y))

    # Meaning (wrap if needed)
    meaning = last_meaning or "Meaning not available."
    meaning_x = padding_x + 260
    wrap_width = width - meaning_x - padding_x

    # wrap meaning text
    wrapped_lines = wrap_text(meaning, font_small, wrap_width)
    for i, line in enumerate(wrapped_lines[:2]):  # allow 2 lines
        m_surf = font_small.render(line, True, (200, 200, 200))
        hud_surface.blit(m_surf, (meaning_x, top_y + (i * 22)))

    # ------------------------------------------------
    # 🌌 BOTTOM ROW — Player | Score | Back btn
    # ------------------------------------------------
    bottom_y = padding_y + 70

    # PLAYER LABEL
    # player_label = font_small.render("Player:", True, (230, 230, 240))
    hud_surface.blit(PLAYER_ICON, (padding_x, bottom_y-5))

    # PLAYER VALUE
    player_value = font_big.render(player_name or "-", True, (255, 255, 255))
    hud_surface.blit(player_value, (padding_x + 70, bottom_y))

    # SCORE LABEL
    score_label_x = padding_x + 260
    score_label = font_small.render("Score:", True, (230, 230, 240))
    hud_surface.blit(score_label, (score_label_x, bottom_y+2))

    # SCORE VALUE
    score_value = font_big.render(str(score), True, (255, 255, 255))
    hud_surface.blit(score_value, (score_label_x + score_label.get_width() + 20, bottom_y))

    # BACK BUTTON (text or will be icon)
    back_text = font_big.render("⟵ Back (ESC)", True, (240, 140, 140))
    back_x = width - back_text.get_width() - padding_x +110
    hud_surface.blit(BACK_ICON, (back_x, bottom_y - 6))
    
    global BACK_BUTTON_RECT
    BACK_BUTTON_RECT = pygame.Rect(20 + back_x,
                                hud_y + bottom_y - 6,
                                BACK_ICON.get_width(),
                                BACK_ICON.get_height())


    # Track clickable area for back button
    
    # BACK_BUTTON_RECT = pygame.Rect(20 + back_x, hud_y + bottom_y - 6,
    #                                back_text.get_width(), back_text.get_height())

    # Draw HUD
    DISPLAYSURF.blit(hud_surface, (20, hud_y))







# ---------------- RUN ----------------
if __name__ == '__main__':
    main()
