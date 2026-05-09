from mckPy import *

c = "beige"
while running():
    fill(c)
        
    drawRect("red", 100, 50, 200, 50, outline = 3)
    if overRect(100, 50, 200, 50):
        drawRect("red3", 100, 50, 200, 50, outline = 3)
    if clickOnRect(100, 50, 200, 50):
        c = "tan"
        

        
    

