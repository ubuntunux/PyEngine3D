import os
import sys

import numpy
from freetype import *
import OpenGL.GL as gl
import OpenGL.GLUT as glut

defaultFont = os.path.join(os.path.split(__file__)[0], 'UbuntuFont.ttf')


#------------------------------#
# CLASS : GLFont - FreeType Font
#------------------------------#
class GLFont:
    def __init__(self, filename, size):
        self.base = 0
        self.texid = 0
        self.makefont(filename, size)

    def makefont(self, filename, size):
        # Load font  and check it is monotype
        face = Face(filename)
        face.set_char_size( size*64 )
        if not os.path.exists(filename):
            raise IOError('%s is not found.' % filename)
        if not face.is_fixed_width:
            raise Exception('Font is not monotype')

        # Determine largest glyph size
        width, height, ascender, descender = 0, 0, 0, 0
        for c in range(32,128):
            face.load_char( chr(c), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
            bitmap    = face.glyph.bitmap
            width     = max( width, bitmap.width )
            ascender  = max( ascender, face.glyph.bitmap_top )
            descender = max( descender, bitmap.rows-face.glyph.bitmap_top )
        height = ascender+descender

        # Generate texture data
        Z = numpy.zeros((height*6, width*16), dtype=numpy.ubyte)
        for j in range(6):
            for i in range(16):
                face.load_char(chr(32+j*16+i), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
                bitmap = face.glyph.bitmap
                x = i*width  + face.glyph.bitmap_left
                y = j*height + ascender - face.glyph.bitmap_top
                Z[y:y+bitmap.rows,x:x+bitmap.width].flat = bitmap.buffer

        # Bound texture
        self.texid = gl.glGenTextures(1)
        gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )
        gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
        gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )
        gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_ALPHA, Z.shape[1], Z.shape[0], 0, gl.GL_ALPHA, gl.GL_UNSIGNED_BYTE, Z )
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )

        # Generate display lists
        dx, dy = width/float(Z.shape[1]), height/float(Z.shape[0])
        self.base = gl.glGenLists(8*16)
        for i in range(8*16):
            c = chr(i)
            x = i%16
            y = i//16-2
            gl.glNewList(self.base + i, gl.GL_COMPILE)
            if (c == '\n'):
                gl.glPopMatrix( )
                gl.glTranslatef( 0, -height, 0 )
                gl.glPushMatrix( )
            elif (c == '\t'):
                gl.glTranslatef( 4*width, 0, 0 )
            elif (i >= 32):
                gl.glBegin( gl.GL_QUADS )
                gl.glTexCoord2f(x*dx, (y+1)*dy)
                gl.glVertex3f(0, -height, 0)
                gl.glTexCoord2f(x*dx, y*dy)
                gl.glVertex(0, 0, 0)
                gl.glTexCoord2f((x+1)*dx, y*dy)
                gl.glVertex(width, 0, 0)
                gl.glTexCoord2f((x+1)*dx, (y+1)*dy)
                gl.glVertex(width, -height, 0)
                gl.glEnd( )
                gl.glTranslatef( width, 0, 0 )
            gl.glEndList( )

    def render(self, text):
        gl.glEnable( gl.GL_TEXTURE_2D )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )
        gl.glListBase( self.base )
        gl.glCallLists( [ord(c) for c in text] )


#------------------------------#
# Font Test
#------------------------------#
class GLFontTest:
    def __init__(self):
        self.testText = 'Hello World !'
        self.testFont1 = None
        self.testFont2 = None

    def test(self):
        glut.glutInit( sys.argv )
        glut.glutInitDisplayMode( glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH )
        glut.glutCreateWindow(b"Freetype OpenGL")
        glut.glutReshapeWindow( 640, 480 )
        glut.glutDisplayFunc( self.on_display )
        glut.glutReshapeFunc( self.on_reshape )
        glut.glutKeyboardFunc( self.on_keyboard )
        gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
        gl.glEnable( gl.GL_DEPTH_TEST )
        gl.glEnable( gl.GL_BLEND )
        gl.glEnable( gl.GL_COLOR_MATERIAL )
        gl.glColorMaterial( gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE )
        gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
        gl.glEnable( gl.GL_TEXTURE_2D )

        # make font
        self.testFont1 = GLFont(defaultFont, 64)
        self.testFont2 = GLFont(defaultFont, 14)
        glut.glutMainLoop( )

    def on_display(self):
        gl.glClearColor(0,0,0,1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glColor(1,1,1,1)
        gl.glPushMatrix( )
        gl.glTranslate( 10, 100, 0 )
        gl.glPushMatrix()
        # render text1
        self.testFont1.render(self.testText)
        gl.glTranslate( 10, 100, 0 )
        # render text2
        self.testFont2.render(self.testText)
        gl.glPopMatrix( )
        gl.glPopMatrix( )
        glut.glutSwapBuffers( )

    def on_reshape(self, width, height):
        gl.glViewport( 0, 0, width, height )
        gl.glMatrixMode( gl.GL_PROJECTION )
        gl.glLoadIdentity( )
        gl.glOrtho( 0, width, 0, height, -1, 1 )
        gl.glMatrixMode( gl.GL_MODELVIEW )
        gl.glLoadIdentity( )

    def on_keyboard(self, key, x, y):
        if key == '\033':
            sys.exit( )

if __name__ == '__main__':
    glFontTest = GLFontTest()
    glFontTest.test()
