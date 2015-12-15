from OpenGL.GL.shaders import *

default_vertex_shader = '''
    varying vec3 normal;
    void main() {
        normal = gl_NormalMatrix * gl_Normal;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }'''

default_pixel_shader = '''
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
    
class Shader:
    default_shader = None
    
    def init(self):        
        # default shader
        self.default_shader = compileProgram(
                    compileShader(default_vertex_shader, GL_VERTEX_SHADER),
                    compileShader(default_pixel_shader, GL_FRAGMENT_SHADER), )