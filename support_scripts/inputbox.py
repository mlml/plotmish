# by Timothy Downs, inputbox written for my map editor

# This program needs a little cleaning up
# It ignores the shift key
# And, for reasons of my own, this program converts "-" to "_"

# A program to get user input, allowing backspace etc
# shown in a box in the middle of the screen
# Called by:
# import inputbox
# answer = inputbox.ask(screen, "Your name")
#
# Only near the center of the screen is blitted to

import pygame, pygame.font, pygame.event, pygame.draw, string
from pygame.locals import *

def get_key():
  while 1:
    event = pygame.event.poll()
    if event.type == KEYDOWN:
      return event.key
    else:
      pass

def getCharacter():
  # Check to see if the player has inputed a command
  keyinput = pygame.key.get_pressed()  

  keyPress = get_key()

  if keyPress == 95: keyPress = 45
  
  if keyinput[K_LSHIFT] or keyinput[K_RSHIFT]: 
    if keyPress >= 97 and keyPress <= 122: keyPress -= 32
    elif keyPress >= 49 and keyPress <= 53: keyPress -= 16
    elif keyPress == 54: keyPress = 94
    elif keyPress == 55: keyPress = 38
    elif keyPress == 56: keyPress = 42 
    elif keyPress == 57: keyPress = 40 
    elif keyPress == 48: keyPress = 41
    elif keyPress == 54: keyPress = 94 
    elif keyPress == 96: keyPress = 126
    elif keyPress == 45: keyPress = 95

  return keyPress 

def display_box(screen, message, size, font):
  "Print a message in a box in the middle of the screen"
  fontobject = font if font else pygame.font.SysFont('helvetica',18)
  
  boxdimensions = size if size else ((screen.get_width() / 2) - 150, (screen.get_height() / 2) - 10, 300, 20)
  pygame.draw.rect(screen, (0,0,0), boxdimensions, 0)

  size = list(size)
  
  textdimensions = (size[0]-2,size[1]-2,size[2]+4,size[3]+4) if size else ((screen.get_width() / 2) - 152, (screen.get_height() / 2) - 12, 304, 24)
  pygame.draw.rect(screen, (255,255,255),textdimensions, 1)
  if len(message) != 0:
    screen.blit(fontobject.render(message, 1, (255,255,255)),
                (boxdimensions[0],boxdimensions[1]))
  pygame.display.flip()

def ask(screen, question, size = None, font = None, currentText = None):
  "ask(screen, question) -> answer"
  pygame.font.init()
  current_string = [] if not currentText else list(currentText)
  display_box(screen, question + ": " if question else "" + string.join(current_string,""), size, font)
  while 1:
    inkey = getCharacter()
    if inkey == K_BACKSPACE:
      current_string = current_string[0:-1]
    elif inkey == K_ESCAPE:
      return 'QUITNOW'
    elif inkey == K_RETURN:
      break
    elif inkey <= 127:
      current_string.append(chr(inkey))
    display_box(screen, question + ": " if question else "" + string.join(current_string,""), size, font)
  return string.join(current_string,"")

def main():
  screen = pygame.display.set_mode((320,240))
  print ask(screen, "Name") + " was entered"

if __name__ == '__main__': main()