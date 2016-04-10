from OpenGL.GL.shaders import *

from Core import logger
from Utilities import Singleton


SIMPLE_VERTEX_SHADER = '''
#version 330
in vec4 position;
void main()
{
   gl_Position = position;
}'''

SIMPLE_PIXEL_SHADER = '''
#version 330
void main()
{
   gl_FragColor = vec4(1.0f, 0.0f, 1.0f, 1.0f);
}'''

TEXTURE_PIXEL_SHADER = '''
#version 140 // OpenGL 3.1
varying vec2 vCoord;			// vertex texture coordinates
uniform sampler2D diffuseTex;  // alpha mapped texture
uniform vec4 diffuseColor;		// actual color for this text

void main(void)
{
	// multiply alpha with the font texture value
	gl_FragColor = vec4(diffuseColor.rgb, texture2D(diffuseTex, vCoord).r * diffuseColor.a);
}
'''


DEFAULT_VERTEX_SHADER = '''
    varying vec3 normal;
    void main() {
        normal = gl_NormalMatrix * gl_Normal;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }'''

DEFAULT_PIXEL_SHADER = '''
    varying vec3 normal;
    void main() {
        float intensity;
        vec4 color;
        vec3 n = normalize(normal);
        vec3 l = normalize(gl_LightSource[0].position).xyz;        
        intensity = saturate(dot(l, n));
        color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity;
        gl_FragColor = color;
    }'''


#------------------------------#
# FUNCTION : CreateShader
#------------------------------#
def CreateShader(vertexShader, pixelShader):
    return compileProgram(compileShader(vertexShader, GL_VERTEX_SHADER), compileShader(pixelShader, GL_FRAGMENT_SHADER), )


#------------------------------#
# CLASS : ShaderManager
#------------------------------#
class ShaderManager(Singleton):
    def __init__(self):
        self.shaders = {}
        self.default_shader = None
        self.coreManager = None

    def initialize(self, coreManager):
        logger.info("initialize " + self.__class__.__name__)
        self.coreManager = coreManager
        self.default_shader = CreateShader(DEFAULT_VERTEX_SHADER, DEFAULT_PIXEL_SHADER)

    def createShader(self, shaderName, vertexShader, pixelShader):
        shader = createShader(vertexShader, pixelShader)
        self.shaders[shaderName] = shader

    def getShader(self, shaderName):
        return self.shaders[shaderName]