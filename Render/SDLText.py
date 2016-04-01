import os
from sys import exit
from ctypes import c_long, pointer, c_char_p, c_int

from sdl2 import *
from sdl2.sdlttf import *

def renderTexture(tex, ren, x, y):
    #Setup the destination rectangle to be at the position we want
    dst = SDL_Rect(x, y)
    w = pointer(c_int(0))
    h = pointer(c_int(0))
    #Query the texture to get its width and height to use
    SDL_QueryTexture(tex, None, None, w, h)
    dst.w = w.contents.value
    dst.h = h.contents.value
    SDL_RenderCopy(ren, tex, None, dst)

def renderText(message, fontFile, color, fontSize, renderer):
    # Open the font
    SDL_ClearError()
    font = TTF_OpenFont(fontFile, fontSize)
    if font is None:
        print(SDL_GetError())
        return None

    surf = TTF_RenderText_Blended(font, message, color)

    if surf is None:
        TTF_CloseFont(font)
        print("TTF_RenderText")
        return None

    texture = SDL_CreateTextureFromSurface(renderer, surf)
    if texture is None:
        print("CreateTexture")

    #Clean up the surface and font
    SDL_FreeSurface(surf)
    TTF_CloseFont(font)
    return texture


def init(renderer):

    color = SDL_Color(255, 255, 255)
    global image
    image = renderText(b"TTF fonts are cool!", str.encode(os.path.join('Render', 'Glametrix.otf')), color, 64, renderer)


def render(window):
    #Getting the window size.
    SCREEN_WIDTH = pointer(c_int(0))
    SCREEN_HEIGHT = pointer(c_int(0))
    SDL_GetWindowSize(window, SCREEN_WIDTH, SCREEN_HEIGHT)

    #Get the texture w/h so we can center it in the screen
    iW = pointer(c_int(0))
    iH = pointer(c_int(0))
    global image
    print(image)
    SDL_QueryTexture(image, None, None, iW, iH)
    x = int(SCREEN_WIDTH.contents.value / 2 - iW.contents.value / 2)
    y = int(SCREEN_HEIGHT.contents.value / 2 - iH.contents.value / 2)