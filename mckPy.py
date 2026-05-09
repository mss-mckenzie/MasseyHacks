"""
mckPy.py
-----------
Author: Mr. Ron McKenzie
Date Created: August 2025
Revisions: Many and minor

- This is designed to make learning graphics as easy as possible. It's just a wrapper
for pygame.
"""

# Import all pygame modules and system module
from pygame import *
from random import *
from math import *
from glob import *
import os
import sys
from pygame._sdl2.video import Window

if not get_init():
    # Initialize pygame
    init()

    allFonts = {}
    fnt = font.SysFont("Helvetica", 24)
    allFonts[("Helvetica", 24)] = fnt

    # Set up the display window
    screen = display.set_mode((800, 600))

    # Create a clock object to manage frame rate
    myClock = time.Clock()

    # Track mouse button clicks: [left, middle, right, upwheel, downwheel]
    clicked = [False, False, False, False, False]

    # Default frames per second
    FPS = 60

    # used only for the findRect function. _ is used because we don't want to collide
    # with variables the user is using. (user can't change these in an import anyways)
    _x1 = 0
    _y1 = 0
    _x2 = 0
    _y2 = 0

    maskImage = None
    maskValues = {}
    # ----------------------------------------------------------------------------
    # -------                   Barrier System                           ---------
    # ----------------------------------------------------------------------------
    """
    The Barrier system allows students to create simple 2D games with walls and
    other barriers. The name isn't the best. It was originally designed for walls,
    doors, mud .... It works well for coins and keys as weel, but the name no longer
    makes sense. I thought about changing it to Object or GameObject but they seem
    too vague.
    """

    barriers = []           # list of Barrier objects

"""
Most of the code for the Barrier class is just turning it into a pygame.Rect
object.

left, top, width, height
- basic values to make a Rect object

colour="black"
- This will be used in drawBarriers when image, animation and tile are all None

kind="wall"
- I wanted to call this "class" but that is a keyword. Having a kind allows to
target a group of barriers with the other functions. hitBarrier deals with kind a little
differently. For hitBarrier if the kind is "water wall" it will be both water and wall.
This makes it easier to have doors, among other advantages.

image=None
- If you set this to an image there are 4 possibilities:
1. If the image and barrier are the same size, just set the image.
2. If the image is smaller in width or height, stretch the image.
3. If the barrier, in its location fits on the image, take that portion
   of the image.
4. Take the portion of the image from 0,0

animation = None
- this should be loaded with my loadAnimation() function

tile = None
- this allows you to use a small image and it tile it over the barrier
"""
class Barrier(Rect):
    def __init__(self, left, top, width, height, colour="black", kind="wall", image=None, animation = None, tile = None):
        super().__init__(left, top, width, height)
        self.colour = colour
        self.kind = kind   
        
        if image != None:
            img_rect = image.get_rect()
            iw, ih = image.get_size()
            if iw != width or ih != height:
                if img_rect.contains(self):
                    image = image.subsurface(self)
                elif img_rect.contains((0,0,width, height)):
                    image = image.subsurface((0,0,width, height))
                else:
                    image = transform.smoothscale(image,(width, height))
        if tile != None:
            image = Surface((width, height))
            tw, th = tile.get_size()
            for tx in range(0, width, tw):
                for ty in range(0, height, th):
                    image.blit(tile, (tx, ty)) 
        self.image=image
        self.animation = animation
        
    """
        This is a dangerous method. You can use this to make a side-scroller,
        but when you move a barrier, you need to check all game objects to
        make sure they are in a valid state.
    """
    def move(self, dx, dy):
        self.left += dx
        self.top += dy

    """ just a variation of move"""
    def setXY(self, x, y):
        self.left = x
        self.top = y

    """
        draw
        If there is an image or animation draw that, otherwise draw a rectangle.
    """
    def draw(self, surface, outline, outlineColour):
        if self.image != None:
            screen.blit(self.image, (self.left, self.top))
        elif self.animation != None:
            drawAnimation(self.animation, self.left, self.top, True)
        else:
            draw.rect(surface, self.colour, self)
        if outline > 0:
            draw.rect(surface, outlineColour, self, outline)

    def drawNum(self, pos):
        drawTextInRect(0, str(pos), self)

"""
finds all of the barriers of the kind specified and calls their draw method.
"""
def drawBarriers(outline = 0, outlineColour=0, kind = "", debug=False):
    if kind == "":
        barrOfKind = barriers
    else:
        barrOfKind = [b for b in barriers if b.kind == kind]
    for b in barrOfKind:
        b.draw(screen, outline, outlineColour)

    # draw t            
    pos = 1
    if debug:
        for b in barrOfKind:
            b.drawNum(pos)
            pos += 1
            
"""
This is dangerous. It can move barriers onto characters.
"""
def moveBarriers(dx, dy, kind = ""):
    if kind == "":
        barrOfKind = barriers
    else:
        barrOfKind = [b for b in barriers if b.kind == kind]
    
    for b in barrOfKind:
        b.move(dx, dy)

# makes a Barrier object and adds it to my barrier list. I have considered not allowing it to
# add the same barrier twice. I don't because I think it will lead to poorer style programs.
def addBarrier(x, y, w, h, colour = "black", kind = "wall", image=None, animation = None, tile=None):
    b = Barrier(x, y, w, h, colour, kind, image, animation, tile)
    barriers.append(b)

# Allows you to clear all (by default) or all of a particular kind.  
def clearBarriers(kind=None):
    global barriers
    if kind==None:
        barriers.clear()
    else:
        barriers = [b for b in barriers if b.kind != kind]
        

# Allows you to remove one barrier by giving its x,y,width,height  
def removeBarrier(x, y, w, h):
    rem = None
    for b in barriers:
        if b.left == x and b.top == y and b.width == w and b.height ==h:
            rem = b
    if rem != None:
        barriers.remove(rem)

# Allows you to find the barrier that the mouse is on
def findBarrier(x, y):
    ans = ""
    pos = 1
    for b in barriers:
        if b.collidepoint((x,y)):
            ans += str(pos)+" "
        pos += 1
    if ans =="":
        print("None")
    else:
        print(ans)

# checks the rectangle (x,y,w,h) against all barriers of the type specified.
# If a Barrier has multiple kinds (indicated with a space e.g., "wall door1")
# then it will be True if it matches any of the kinds 
def hitBarrier(x, y, w, h, kind = "wall", debug = False):
    r = Rect(x, y, w, h)
    barrOfKind = [b for b in barriers if kind in b.kind.split(" ")]

    return r.collidelist(barrOfKind) > -1

# Allows you to remove one barrier that is hit by the rect given x,y,width,height.
# This makes it easy to pick up coins and other objects.
def removeHitBarrier(x, y, w, h, kind = "wall"):
    r = Rect(x, y, w, h)
    barrOfKind = [b for b in barriers if b.kind == kind]
    hit = r.collidelist(barrOfKind)
    if hit > -1:
        barriers.remove(barrOfKind[hit])

# ----------------------------------------------------------------------------
# -------                   Animation System                           ---------
# ----------------------------------------------------------------------------
"""
This animation is designed to be used with mckSplit.py. You should have a folder that is
the name of the animation and subfolders with the moves. e.g.,

/mario
----/left
---- left0.png
---- left1.png
---- left2.png
----/right
---- right0.png
---- right1.png
---- right2.png

name - name of the folder that has the animation

newWidth=0, newHeight=0, delay = 4, startFrame = 0, centerX=False, centerY=False
"""

def loadAnimation(name, newWidth=0, newHeight=0, delay = 4, startFrame = 0, centerX=False, centerY=False):
    ani = {}    
    folders = [f for f in os.listdir(name) if os.path.isdir(os.path.join(name, f))]
    moves = {}
    maxW = {}
    maxH = {}
    for f in folders:
        moves[f] = [ ]
        maxW[f] = 0
        maxH[f] = 0
        for fn in os.listdir(os.path.join(name, f)):
            nname = os.path.join(name, f, fn)
            pic = loadImage(nname, newWidth, newHeight)
            wid, hei = pic.get_size()
            maxW[f] = max(maxW[f], wid)
            maxH[f] = max(maxH[f], hei)
            moves[f].append(pic)

    ani["frame"] = startFrame
    ani["move"] = folders[0]
    ani["delay"] = 0
    ani["maxDelay"] = delay
    ani["moves"] = moves
    ani["centerX"] = centerX
    ani["centerY"] = centerY
    ani["maxW"] = maxW
    ani["maxH"] = maxH
    
    return ani
    


def drawAnimation(ani, x, y, advance = True):
    """ ani must be loaded with loadAnimation. Draws character at its
        current location showing current move.
    """
    move = ani["move"]
    pics = ani["moves"][move]
    maxW = ani["maxW"][move]
    maxH = ani["maxH"][move]
    if advance:
        ani["delay"] += 1
        if ani["delay"] == ani["maxDelay"]:
            ani["delay"] = 0
            ani["frame"] += 1
            if ani["frame"] == len(pics):
                ani["frame"] = 0
    pic = pics[ani["frame"]]
    offx = 0
    offy = 0
    if ani["centerX"]:
        wid, hei = pic.get_size()
        offx = (maxW - wid) // 2
        offy = (maxH - hei) // 2
        
    screen.blit(pic, (x+offx, y+offy))

def changeMove(ani, newMove):
    """name must be loaded with loadCharacter. Changes to a valid move"""
    if ani["move"] == newMove: return
    if newMove in ani["moves"]:
        ani["move"] = newMove
        ani["frame"] = 0
        
def addFlippedMove(ani, move, newName):
    """name must be loaded with loadCharacter. Changes to a valid move"""
    moves = ani["moves"]
    moves[newName] = [transform.flip(pic, True, False) for pic in moves[move]]
    ani["maxW"][newName] = ani["maxW"][move]
    ani["maxH"][newName] = ani["maxH"][move]

# ----------------------------------------------------------------------------
# -------                   Sounds / Music                           ---------
# ----------------------------------------------------------------------------

def loadSound(name):
    """You should be loading *.wav files. Use playSound to play. e.g.
        shot = loadSound("shot.wav") # once, before while running():
        playSound(shot)      # whenever you want the sound to play
    """
    return mixer.Sound(name)

def playSound(snd):
    """ Sound should be loaded with loadSound
        shot = loadSound("shot.wav") # once, before while running():
        playSound(shot)      # whenever you want the sound to play
    """
    snd.play()

def playMusic(name, loops = -1):
    """Should be loading *.mp3 files. By default it will keep looping.
        You can specify how many times you would like it to loop.
    """
    lps = loops
    mixer.music.stop()
    mixer.music.load(name)
    mixer.music.play(loops = lps)

def stopMusic():
    """Stops current song"""
    mixer.music.stop()
    
def pauseMusic():
    """Pauses current song"""
    mixer.music.pause()
    
def unpauseMusic():
    """Unpauses current song"""
    mixer.music.unpause()

# ----------------------------------------------------------------------------
# -------                   Mouse Interactions                           ---------
# ----------------------------------------------------------------------------
    
def justClicked(btn=None):
    """
    Returns True if a mouse button was pressed during the last frame.
    
    Parameters:
    btn (None or int): The button to check.
        - None: check if any button was pressed
        - 0: left button
        - 1: middle button
        - 2: right button
    
    Returns:
    bool: True if specified button was just pressed, False otherwise
    """
    if btn is None:
        return any(clicked)
    else:
        return clicked[btn]

def mouseXY():
    """Returns the current position of the mouse as a tuple (x, y)."""
    return mouse.get_pos()

def mouseX():
    """Returns the current X position of the mouse."""
    return mouse.get_pos()[0]

def getMouse():
    """Returns the current (x, y) position of the mouse."""
    return mouse.get_pos()

def mouseY():
    """Returns the current Y position of the mouse."""
    return mouse.get_pos()[1]

def mouseL():
    """Returns True if the left mouse button is currently pressed."""
    return mouse.get_pressed()[0]

def mouseM():
    """Returns True if the middle mouse button is currently pressed."""
    return mouse.get_pressed()[1]

def mouseR():
    """Returns True if the right mouse button is currently pressed."""
    return mouse.get_pressed()[2]

def wheelUp():
    """Returns True if there was a mouse wheel up event."""
    return clicked[3]

def wheelDown():
    """Returns True if there was a mouse wheel up event."""
    return clicked[4]
def clickOnRect(x,y,w,h,btn=1):
    """returns true if the mouse is inside the rectangle given
       and the mouse button just went down. By default it check the left
       mouse button, but you can add 2 or 3 for the middle or right button.
       """
    if btn not in [1,2,3]:
        btn=1
    click = clicked[btn-1]
    mx,my = mouse.get_pos()
    return click and x <= mx <= x+w and y <= my <= y+h
    
def pressOnRect(x,y,w,h,btn=1):
    """returns true if the mouse is inside the rectangle given
       and the mouse button is down. By default it check the left mouse button,
       but you can add 2 or 3 for the middle or right button.
       """
    if btn not in [1,2,3]:
        btn=1
    click = mouse.get_pressed()[btn-1]
    mx,my = mouse.get_pos()
    return click and x <= mx <= x+w and y <= my <= y+h
    
def overRect(x,y,w,h):
    """returns true if the mouse is inside the rectangle given.
       """
    mx,my = mouse.get_pos()
    return x <= mx <= x+w and y <= my <= y+h

# ----------------------------------------------------------------------------
# -------                   Keyboard Interaction                           ---------
# ----------------------------------------------------------------------------

def upKey():
    """Returns True if the "w" or up arrow is currently pressed."""
    keys = key.get_pressed()
    return keys[K_w] or keys[K_UP]

def rightKey():
    """Returns True if the "d" or right arrow is currently pressed."""
    keys = key.get_pressed()
    return keys[K_d] or keys[K_RIGHT]

def downKey():
    """Returns True if the "s" or down arrow is currently pressed."""
    keys = key.get_pressed()
    return keys[K_s] or keys[K_DOWN]

def leftKey():
    """Returns True if the "a" or left arrow is currently pressed."""
    keys = key.get_pressed()
    return keys[K_a] or keys[K_LEFT]

def spaceKey():
    """Returns True if the "a" or left arrow is currently pressed."""
    keys = key.get_pressed()
    return keys[K_SPACE]

def keyPressed(keycode):
    """Returns True the keycode is currently pressed. e.g. K_z
    see: https://www.pygame.org/docs/ref/key.html """
    keys = key.get_pressed()
    return keys[keycode]

# ----------------------------------------------------------------------------
# -------                   Rectangles                           ---------
# ----------------------------------------------------------------------------

def overlapsList(lst1, lst2):
    """Returns True if the two rectangles overlap."""
    r1 = Rect(lst1)
    r2 = Rect(lst2)
    return r1.colliderect(r2)

def overlaps(x1, y1, w1, h1, x2, y2, w2, h2):
    """Returns True if the two rectangles overlap."""
    r1 = Rect(x1, y1, w1, h1)
    r2 = Rect(x2, y2, w2, h2)
    return r1.colliderect(r2)

# ----------------------------------------------------------------------------
# -------                   Basic Drawing Commands                   ---------
# ----------------------------------------------------------------------------

def loadImage(img, newWidth=0, newHeight=0):
    """Loads an image from a file. Can resize the image as you load it."""
    #print(img, newWidth, newHeight)
    try:
        pic =  image.load(img)
    except:
        pic = Surface((10,10))
        pic.fill("beige")
    if newWidth==0 and newHeight==0:
        return pic
    wid, hei = pic.get_size()
    if newHeight == 0:
        ratio = newWidth / wid
        newHeight = hei * ratio
    elif newWidth == 0:
        ratio = newHeight / hei
        newWidth = wid * ratio
    #print(img, newWidth, newHeight)
    return transform.smoothscale(pic, (newWidth, newHeight))


def flipImage(img, flipX=False, flipY=False):
    return transform.flip(img, flipX, flipY)

def rotateImage(img, angle):
    return transform.rotate(img, angle)

def scaleImage(img, newWidth, newHeight):
    return transform.scale(img, (newWidth, newHeight))


def drawImage(img, x=0, y=0):
    """Draws an image at the specified (x, y) position."""
    screen.blit(img, (x, y))

def drawRectList(c, lst, t=0, corner=0, outline=0, alpha=255, outlineColour=0):
    drawRect(c, lst[0], lst[1], lst[2], lst[3], t, corner, outline, alpha, outlineColour)

def drawRect(c, x, y, width, height, t=0, corner=0, outline=0, alpha=255, outlineColour=0):
    """
    Draws a rectangle.
    
    Parameters:
    c: color
    x, y: top-left corner
    width, height: dimensions
    t: thickness (0 = filled)
    corner: corner radius (for rounded corners)
    alpha: Can set the transparency 0-255. 0=invisible, 255=fully opaque. corner
           is not preserved with alpha. 
    """
    if alpha == 255:
        draw.rect(screen, c, (x, y, width, height), t, corner)
        if outline > 0:
            draw.rect(screen, outlineColour, (x, y, width, height), outline, corner)
    elif 0<alpha<255:
        surf = Surface((width, height)).convert()
        surf.set_alpha(alpha)
        surf.fill(c)
        if outline > 0:
            draw.rect(surf, outlineColour, (0, 0, width, height), outline)
        screen.blit(surf, (x, y))
        

def drawLine(c, x, y, x2, y2, t=1):
    """Draws a line from (x, y) to (x2, y2) with thickness t."""
    draw.line(screen, c, (x, y), (x2, y2), t)

def drawText(c, txt, x, y, alpha = 255, align = "left", font = None):
    """Draws a text in current font at (x, y) in colour c.
        to draw in new font add font like, font=("Arial", 45) """
    global fnt
    tmpFnt = fnt
    if font != None:
        f,s = font
        setFont(f, s)
    txtPic = fnt.render(txt, False, c)
    txtPic.set_alpha(alpha)
    if align == "right":
        ox = x
        x = ox - txtPic.get_width()
    screen.blit(txtPic,(x,y))
    fnt = tmpFnt

def drawTextInRect(c, txt, rectangle, alpha = 255, font = None):
    """Draws a text in current font at centered in a rect in colour c.
        to draw in new font add font like, font=("Arial", 45) """
    global fnt
    tmpFnt = fnt
    if font != None:
        f,s = font
        setFont(f, s)
    txtPic = fnt.render(txt, False, c)
    txtPic.set_alpha(alpha)
    extraX = rectangle.width - txtPic.get_width()
    extraY = rectangle.height - txtPic.get_height()
    x = rectangle.x + extraX//2
    y = rectangle.y + extraY//2
    screen.blit(txtPic,(x,y))
    fnt = tmpFnt

def setFont(name, size=24):
    """sets the font for drawing. Once set, all drawText calls will use
       the current font. You can can use a system font, a .ttf or a .otf file. 
    """
    global fnt
    if (name, size) in allFonts:
        fnt = allFonts[(name, size)]
    else:
        try:
            if "." in name:
                fnt = font.Font(name, size)
            else:
                fnt = font.SysFont(name, size)
            allFonts[(name, size)] = fnt
        except:
            print("invalid font")


def drawArc(c, x, y, width, height, startAng, stopAng, t=0, outline=0, outlineColour=0):
    """Draws part of an oval (ellipse) inside the specified rectangle.
       The arc starts from the start angle and ends at the stop angle.
    """
    start = radians(startAng)
    stop = radians(stopAng)
    draw.arc(screen, c, (x, y, width, height), start, stop, t)
    if outline > 0:
        draw.ellipse(screen, outlineColour, (x, y, width, height),  start, stop, outline)

def quadratic_bezier(t, p0, p1, p2):
    """Calculate a point on a quadratic Bézier curve.    """
    x = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
    y = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
    return (int(x), int(y))

def drawCurve(c, x1, y1, x2, y2, x3, y3, thickness=1, accuracy = 200):
    """ Draw a Bézier curve.  This is the same curve you get in paint.
    There are three points, the first and last are the endpoints of the line.
    The middle one "pulls" the line to make a curve.
    """
    p0 = (x1, y1)
    p1 = (x2, y2)
    p2 = (x3, y3)   
    # Generate points along the Bézier curve
    curve_points = [quadratic_bezier(t / 200.0, p0, p1, p2) for t in range(201)]
    # Draw circles at each point on the curve
    for point in curve_points:
        draw.circle(screen, c, point, thickness)
        
def drawOval(c, x, y, width, height, t=0, outline=0, outlineColour=0):
    """Draws an oval (ellipse) inside the specified rectangle."""
    draw.ellipse(screen, c, (x, y, width, height), t)
    if outline > 0:
        draw.ellipse(screen, outlineColour, (x, y, width, height), outline)

def drawCircle(c, x, y, r, t=0, outline=0, outlineColour=0):
    """Draws a circle centered at (x, y) with radius r."""
    draw.circle(screen, c, (x, y), r, t)
    if outline > 0:
        draw.circle(screen, outlineColour, (x, y), r, outline)

def drawPoly(c, points, t=0, outline=0, outlineColour=0, debug=False, debugColour="black"):
    """Draws a polygon using a list of point tuples."""
    draw.polygon(screen, c, points, t)
    if outline > 0:
        draw.polygon(screen, outlineColour, points, outline)
    if debug:
        for i, v in enumerate(points):
            drawText(debugColour, f"{i}", v[0], v[1])

def drawTriangle(c, x1, y1, x2, y2, x3, y3, t=0, outline=0, outlineColour=0):
    """Draws a triangle using three points."""
    points = [(x1, y1), (x2, y2), (x3, y3)]
    draw.polygon(screen, c, points, t)
    if outline > 0:
        draw.polygon(screen, outlineColour, points, outline)

def drawTri(c, x1, y1, x2, y2, x3, y3, t=0, outline=0, outlineColour=0):
    """Draws a triangle using three points."""
    drawTriangle(c, x1, y1, x2, y2, x3, y3, t, outline, outlineColour)

def drawDot(c, x, y):
    """Draws a single pixel."""
    screen.set_at((x,y),c)

def fill(c):
    """Fills the entire screen with the specified color."""
    screen.fill(c)

def background(c):
    """Fills the entire screen with the specified color."""
    screen.fill((c, c, c))

# ----------------------------------------------------------------------------
# -------                   Misc. Commands                   ---------
# ----------------------------------------------------------------------------

def getColour(x, y):
    """Draws a single pixel."""
    return screen.set_at((x,y))


def resize(width, height):
    """Resizes the screen to the new width and height."""
    global screen
    screen = display.set_mode((width, height))

def wait(n):
    """Pauses the program for n milliseconds. This can cause some confusion
       results because it flips the screen first. This means that anything
       that shows up after the wait will not be there.
    """
    display.flip()
    time.wait(n)

def frameRate(fps):
    """Sets the frame rate (frames per second)."""
    global FPS
    FPS = fps

    
def loadMask(img, colourKey = None):
    """ My mask system only allows for one mask at a time. By default,
        the mask uses white as "open", anything else is a "wall". You
        can assign colours to values by adding a dictionary when you call it.
        e.g.
        loadMask("page1_mask.png", colourKey = {"green":"open", "blue":"water", "black":"wall"})
        - don't use a .jpg for your mask. The way it compresses colours will result in a messy mask.
    """
    global maskImage
    maskImage = loadImage(img)
    if colourKey != None and type(colourKey) == dict:
        maskValues.update(colourKey)
    else:
        maskValues[color_to_int("white")] = "open"

def checkMask(x, y):
    "returns the value at a pixel location"
    if x < 0 or y < 0 or x >= maskImage.get_width() or y >= maskImage.get_height():
        return "wall"
    col = color_to_int(maskImage.get_at((x, y)))

    if col in maskValues:
        return maskValues[col]
    return "wall"



def findRect(colour = "red", show = True):
    """
        This is helpful when adding Barriers. This lets you draw a rectangle on the screen.
        The default version draws a red rectangle and prints the coordinates as text.
    """

    global _x1, _y1, _x2, _y2
    temp = (_x1, _y1, _x2, _y2)
    if justClicked(0):
        _x1, _y1 = mouseXY()
        _x1 -= _x1 % 5
        _y1 -= _y1 % 5
    if mouseL():
        _x2, _y2 = mouseXY()
        _x2 -= _x2 % 5
        _y2 -= _y2 % 5
    x = min(_x1, _x2)
    y = min(_y1, _y2)
    w = abs(_x2-_x1)
    h = abs(_y2-_y1)
    if show and temp != (_x1, _y1, _x2, _y2):
        print(f"{x}, {y}, {w}, {h}")
    drawRect(colour, x, y, w, h, 2)

def xy(startX, startY, length, angle):
    """
    Calculate an (x, y) point that is offset from (startX, startY) by length and
    rotated by angle. This makes it easy for students who don't know trig yet to find angular
    points.

    """
    x = startX + cos(radians(angle)) * length
    y = startY - sin(radians(angle)) * length
    return (x, y)

def moveWindow(x,y):
    window = Window.from_display_module()
    window.position = (x, y)

"""
Puts a box on the screen at the x,y location with the given width. The height
of the box is based on the current font. The user can type whatever they like.
When they hit enter it returns the string.
"""
def getText(x, y, width, colour = "skyblue"):
    ans = ""                    # final answer will be built one letter at a time.
    back = screen.copy()        # copy screen so we can replace it when done
    xPic = fnt.render("X", False, 0)
    curWidth = xPic.get_width()//4
    curHeight = xPic.get_height()
    h_buff =  curHeight//8
    height = curHeight + h_buff * 2
    textArea = Rect(x, y, width, height)
    frame = 0
    typing = True
    while typing:
        frame = frame + 1
        for e in event.get():
            if e.type == QUIT:
                event.post(e)   # puts QUIT back in event list so main quits
                return ""
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    typing = False
                    ans = ""
                elif e.key == K_BACKSPACE:    # remove last letter
                    if len(ans)>0:
                        ans = ans[:-1]
                elif e.key == K_KP_ENTER or e.key == K_RETURN : 
                    typing = False
                elif e.key < 256:
                    ans += e.unicode       # add character to ans
                    
        drawRect(colour,x, y, width, height, outline=1)        # draw the text window and the text.
        drawText("black", ans, x + h_buff, y + h_buff)
        if time.get_ticks() % 1000 < 500:
            txtPic = fnt.render(ans, False, "black")
            x2 = x + txtPic.get_width() + h_buff
            drawRect("black", x2, y + h_buff*2, curWidth, curHeight-h_buff*2)
            
        display.flip()
        
    screen.blit(back,(0,0))
    return ans


# ----------------------------------------------------------------------------
# -------              Core function for all programs                ---------
# ----------------------------------------------------------------------------
    
def running():
    """
    Updates the display, maintains the frame rate and handles events.
    
    Returns:
    bool: False if the user quits or presses ESC, True otherwise.
    """
    display.flip()
    myClock.tick(FPS)

    # Reset click tracking
    clicked[:] = [False] * 5

    # Exit if ESC key is pressed
    if key.get_pressed()[27]:
        quit()
        return False

    # Handle events
    for evnt in event.get():
        if evnt.type == MOUSEBUTTONDOWN:
            if evnt.button <= 5:
                clicked[evnt.button - 1] = True
        if evnt.type == QUIT:
            quit()
            return False
    return True
