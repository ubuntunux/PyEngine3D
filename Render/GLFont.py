import os

import numpy
import pygame
from pygame import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *

FONT_VERTEX_SHADER = '''
#version 330 core
layout (location = 0) in vec4 vertex; // <vec2 pos, vec2 tex>
out vec2 TexCoords;
uniform mat4 projection;

void main()
{
    gl_Position = projection * vec4(vertex.xy, 0.0, 1.0);
    TexCoords = vertex.zw;
}'''

FONT_PIXEL_SHADER = '''
#version 330 core
in vec2 TexCoords;
out vec4 color;

uniform sampler2D text;
uniform vec3 textColor;

void main()
{
    vec4 sampled = vec4(1.0, 1.0, 1.0, texture(text, TexCoords).r);
    color = vec4(textColor, 1.0) * sampled;
}
'''

SIMPLE_VERTEX_SHADER = '''
    varying vec3 normal;
    void main() {
        normal = gl_NormalMatrix * gl_Normal;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }'''

SIMPLE_PIXEL_SHADER = '''
#version 140 // OpenGL 3.1

void main(void)
{
    // multiply alpha with the font texture value
    gl_FragColor = vec4(1.0f, 1.0f, 0.0f, 1.0f);
}
'''

defaultFontFile = os.path.join(os.path.split(__file__)[0], 'UbuntuFont.ttf')


#
# CLASS : GLFont
#
class GLFont:
    cmd_id = 0
    texture_id = []
    width = 0
    height = 0
    size = 0
    margin = (5, 0)
    shader = None
    VAO = 0
    VBO = 0

    def __init__(self, fontFile, size, margin=(5, 0)):
        if not os.path.exists(fontFile):
            print("Not found fontfile. Alternative use default font.")
            fontFile = defaultFontFile

        font = pygame.font.Font(fontFile, size)

        self.size = size
        self.margin = margin
        self.width, self.height = 0, 0
        self.shader = compileProgram(compileShader(SIMPLE_VERTEX_SHADER, GL_VERTEX_SHADER), compileShader(SIMPLE_PIXEL_SHADER, GL_FRAGMENT_SHADER), )

        # ascii code bitmap generate
        for i in range(32, 128):
            textSurface = font.render(chr(i), True, (255,255,255,255), (0,0,0,255))
            ix = textSurface.get_width()
            iy = textSurface.get_height()
            self.width = max(self.width, ix)
            self.height = max(self.height, iy)
            image = pygame.image.tostring(textSurface, "RGBA", True)
    
            glPixelStorei(GL_UNPACK_ALIGNMENT,1)
            i = glGenTextures(1)
            self.texture_id.append(i)
            glBindTexture(GL_TEXTURE_2D, i)
            glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)


        # create command list
        self.cmd_id = glGenLists(128)
        for i in range(128):
            c = chr(i)
            glNewList(self.cmd_id + i, GL_COMPILE)
            if c == '\n':
                glPopMatrix()
                glTranslatef(0, -(self.height+self.margin[1]), 0 )
                glPushMatrix()
            elif c == '\t':
                glTranslatef( self.width*4, 0, 0)
            elif i >= 32:
                glBindTexture( GL_TEXTURE_2D, self.texture_id[i-32] )
                glBegin(GL_QUADS)
                glTexCoord2f(0.0, 0.0); glVertex3f(0, 0, 0)
                glTexCoord2f(1.0, 0.0); glVertex3f(self.width, 0, 0)
                glTexCoord2f(1.0, 1.0); glVertex3f(self.width, self.height, 0)
                glTexCoord2f(0.0, 1.0); glVertex3f(0, self.height, 0)
                glEnd()
                glTranslatef(self.width, 0, 0)
            glEndList( )

    def render(self, text, x, y):
        glEnable( GL_TEXTURE_2D )
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(x+self.margin[0], y-self.margin[1], 0)
        glPushMatrix()
        glListBase( self.cmd_id )
        glCallLists( [ord(c) for c in text if ord(c) < 128] )
        glPopMatrix()
        glPopMatrix()


# test
if __name__ == '__main__':
    width, height = 640, 480
    pygame.init()
    pygame.display.set_mode((width, height), OPENGL|DOUBLEBUF|RESIZABLE|HWPALETTE|HWSURFACE)
    pygame.font.init()

    # test font
    test_font = GLFont('UbuntuFont.ttf', 64)

    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)

    # set orthographic view
    glMatrixMode( GL_PROJECTION )
    glLoadIdentity( )
    glOrtho( 0, width, 0, height, -1, 1 )
    glMatrixMode( GL_MODELVIEW )
    glLoadIdentity()

    running = True
    while running:
        for event in pygame.event.get():
            eventType = event.type
            keydown = pygame.key.get_pressed()
            if eventType == KEYDOWN and keydown[K_ESCAPE]:
                running = False
                break
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        test_font.render("Hello World!!\nTap\tTest!", 0, height * 0.5)
        pygame.display.flip()
    pygame.quit()
