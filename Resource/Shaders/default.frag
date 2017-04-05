#include "default.vert"

#ifdef FRAGMENT_SHADER
in VERTEX_OUT vs_output;
out vec4 fs_output;

void main() {
    vec4 baseColor = get_base_color();
    if(baseColor.a < 0.333f && enable_blend != 1)
    {
        discard;
    }

    vec3 normalVector = normalize(vs_output.normalVector);
    vec3 cameraVector = normalize(vs_output.cameraVector);
    vec3 lightVector = normalize(vs_output.lightVector);
    vec4 emissiveColor = get_emissive_color();
    vec3 normal = get_normal();
    vec3 diffuseLighting = baseColor.xyz * clamp(dot(lightVector, normal), 0.0, 1.0);
    float specularLighting = clamp(dot(reflect(-lightVector, normal), cameraVector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0);
    fs_output = vec4(lightColor.xyz * (diffuseLighting + specularLighting) + emissiveColor.xyz * emissiveColor.w, 1.0);
}
#endif