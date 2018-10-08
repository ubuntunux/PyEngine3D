/* Hi there!
 * Here is a demo presenting volumetric rendering single with shadowing.
 * Did it quickly so I hope I have not made any big mistakes :)
 *
 * I also added the improved scattering integration I propose in my SIGGRAPH'15 presentation
 * about Frostbite new volumetric system I have developed. See slide 28 at http://www.frostbite.com/2015/08/physically-based-unified-volumetric-rendering-in-frostbite/
 * Basically it improves the scattering integration for each step with respect to extinction
 * The difference is mainly visible for some participating media having a very strong scattering value.
 * I have setup some pre-defined settings for you to checkout below (to present the case it improves):
 * - D_DEMO_SHOW_IMPROVEMENT_xxx: shows improvement (on the right side of the screen). You can still see aliasing due to volumetric shadow and the low amount of sample we take for it.
 * - D_DEMO_SHOW_IMPROVEMENT_xxx_NOVOLUMETRICSHADOW: same as above but without volumetric shadow
 *
 * To increase the volumetric rendering accuracy, I constrain the ray marching steps to a maximum distance.
 *
 * Volumetric shadows are evaluated by raymarching toward the light to evaluate transmittance for each view ray steps (ouch!)
 *
 * Do not hesitate to contact me to discuss about all that :)
 * SebH
 */


#include "scene_constants.glsl"
#include "quad.glsl"


#ifdef MATERIAL_COMPONENTS
    uniform sampler2D texture_noise;
#endif



const float D_FOG_NOISE = 1.0;
const float D_STRONG_FOG = 0.0;
const int D_USE_IMPROVE_INTEGRATION = 1;

vec3 LPOS()
{
    return vec3( 20.0 + 15.0 * sin(TIME), 15.0 + 12.0 * cos(TIME), -20.0);
}

vec3 LCOL()
{
    return 600.0 * vec3( 1.0, 0.9, 0.5);
}


float displacementSimple( vec2 p )
{
    float f;
    f  = 0.5000* texture2DLod( texture_noise, p, 0.0 ).x; p = p*2.0;
    f += 0.2500* texture2DLod( texture_noise, p, 0.0 ).x; p = p*2.0;
    f += 0.1250* texture2DLod( texture_noise, p, 0.0 ).x; p = p*2.0;
    f += 0.0625* texture2DLod( texture_noise, p, 0.0 ).x; p = p*2.0;

    return f;
}


vec3 getSceneColor(vec3 p, float material)
{
	if(material==1.0)
	{
		return vec3(1.0, 0.5, 0.5);
	}
	else if(material==2.0)
	{
		return vec3(0.5, 1.0, 0.5);
	}
	else if(material==3.0)
	{
		return vec3(0.5, 0.5, 1.0);
	}

	return vec3(0.0, 0.0, 0.0);
}


float getClosestDistance(vec3 p, out float material)
{
	float d = 0.0;
    float minD = 1.0; // restrict max step for better scattering evaluation
	material = 0.0;

    float yNoise = 0.0;
    float xNoise = 0.0;
    float zNoise = 0.0;

	d = max(0.0, p.y - yNoise);
	if(d<minD)
	{
		minD = d;
		material = 2.0;
	}

	d = max(0.0,p.x - xNoise);
	if(d<minD)
	{
		minD = d;
		material = 1.0;
	}

	d = max(0.0,40.0-p.x - xNoise);
	if(d<minD)
	{
		minD = d;
		material = 1.0;
	}

	d = max(0.0,-p.z - zNoise);
	if(d<minD)
	{
		minD = d;
		material = 3.0;
    }

	return minD;
}


vec3 calcNormal( in vec3 pos)
{
    float material = 0.0;
    vec3 eps = vec3(0.3,0.0,0.0);
	return normalize( vec3(
           getClosestDistance(pos+eps.xyy, material) - getClosestDistance(pos-eps.xyy, material),
           getClosestDistance(pos+eps.yxy, material) - getClosestDistance(pos-eps.yxy, material),
           getClosestDistance(pos+eps.yyx, material) - getClosestDistance(pos-eps.yyx, material) ) );

}

vec3 evaluateLight(in vec3 pos)
{
    vec3 lightPos = LPOS();
    vec3 lightCol = LCOL();
    vec3 L = lightPos-pos;
    return lightCol * 1.0/dot(L,L);
}

vec3 evaluateLight(in vec3 pos, in vec3 normal)
{
    vec3 lightPos = LPOS();
    vec3 L = lightPos-pos;
    float distanceToL = length(L);
    vec3 Lnorm = L/distanceToL;
    return max(0.0,dot(normal,Lnorm)) * evaluateLight(pos);
}

// To simplify: wavelength independent scattering and extinction
void getParticipatingMedia(out float muS, out float muE, in vec3 pos)
{
    float heightFog = 7.0 + D_FOG_NOISE*3.0*clamp(displacementSimple(pos.xz*0.005 + TIME*0.01),0.0,1.0);
    heightFog = 0.3*clamp((heightFog-pos.y)*1.0, 0.0, 1.0);

    const float fogFactor = 1.0 + D_STRONG_FOG * 5.0;

    const float sphereRadius = 5.0;
    float sphereFog = clamp((sphereRadius-length(pos-vec3(20.0,19.0,-17.0)))/sphereRadius, 0.0,1.0);

    const float constantFog = 0.02;

    muS = constantFog + heightFog*fogFactor + sphereFog;

    const float muA = 0.0;
    muE = max(0.000000001, muA + muS); // to avoid division by zero extinction
}

float phaseFunction()
{
    return 1.0/(4.0*3.14);
}

float volumetricShadow(in vec3 from, in vec3 to)
{
    const float numStep = 16.0; // quality control. Bump to avoid shadow alisaing
    float shadow = 1.0;
    float muS = 0.0;
    float muE = 0.0;
    float dd = length(to-from) / numStep;
    for(float s=0.5; s<(numStep-0.1); s+=1.0)// start at 0.5 to sample at center of integral part
    {
        vec3 pos = from + (to-from)*(s/(numStep));
        getParticipatingMedia(muS, muE, pos);
        shadow *= exp(-muE * dd);
    }
    return shadow;
}

void traceScene(bool improvedScattering, vec3 rO, vec3 rD, inout vec3 finalPos, inout vec3 normal, inout vec3 albedo, inout vec4 scatTrans)
{
	const int numIter = 100;

    float muS = 0.0;
    float muE = 0.0;

    vec3 lightPos = LPOS();

    // Initialise volumetric scattering integration (to view)
    float transmittance = 1.0;
    vec3 scatteredLight = vec3(0.0, 0.0, 0.0);

	float d = 1.0; // hack: always have a first step of 1 unit to go further
	float material = 0.0;
	vec3 p = vec3(0.0, 0.0, 0.0);
    float dd = 0.0;
	for(int i=0; i<numIter;++i)
	{
		vec3 p = rO + d*rD;


    	getParticipatingMedia(muS, muE, p);


        if(D_USE_IMPROVE_INTEGRATION>0) // freedom/tweakable version
        {
            // See slide 28 at http://www.frostbite.com/2015/08/physically-based-unified-volumetric-rendering-in-frostbite/
            vec3 S = evaluateLight(p) * muS * phaseFunction()* volumetricShadow(p,lightPos);// incoming light
            vec3 Sint = (S - S * exp(-muE * dd)) / muE; // integrate along the current step segment
            scatteredLight += transmittance * Sint; // accumulate and also take into account the transmittance from previous steps

            // Evaluate transmittance to view independentely
            transmittance *= exp(-muE * dd);
        }
		else
        {
            // Basic scatering/transmittance integration
            scatteredLight += muS * evaluateLight(p) * phaseFunction() * volumetricShadow(p,lightPos) * transmittance * dd;
            transmittance *= exp(-muE * dd);
        }


        dd = getClosestDistance(p, material);
        if(dd<0.2)
            break; // give back a lot of performance without too much visual loss
		d += dd;
	}

	albedo = getSceneColor(p, material);

    finalPos = rO + d*rD;

    normal = calcNormal(finalPos);

    scatTrans = vec4(scatteredLight, transmittance);
}


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
	vec2 uv = vs_output.tex_coord;
	vec2 uv2 = 2.0 * vs_output.tex_coord - 1.0;

	vec3 camPos = vec3( 20.0, 18.0,-50.0);
    if(MOUSE_POS.x+MOUSE_POS.y > 0.0)
    {
        camPos += vec3(0.05,0.12,0.0) * (vec3(MOUSE_POS.x, MOUSE_POS.y, 0.0) - vec3(BACKBUFFER_SIZE.xy * 0.5, 0.0));
    }

	vec3 camX   = vec3( 1.0, 0.0, 0.0) *0.75;
	vec3 camY   = vec3( 0.0, 1.0, 0.0) *0.5;
	vec3 camZ   = vec3( 0.0, 0.0, 1.0);

	vec3 rO = camPos;
	vec3 rD = normalize(uv2.x*camX + uv2.y*camY + camZ);
	vec3 finalPos = rO;
	vec3 albedo = vec3( 0.0, 0.0, 0.0 );
	vec3 normal = vec3( 0.0, 0.0, 0.0 );
    vec4 scatTrans = vec4( 0.0, 0.0, 0.0, 0.0 );
    traceScene( gl_FragCoord.x > (BACKBUFFER_SIZE.x / 2.0), rO, rD, finalPos, normal, albedo, scatTrans);

    //lighting
    vec3 color = (albedo/3.14) * evaluateLight(finalPos, normal) * volumetricShadow(finalPos, LPOS());
    // Apply scattering/transmittance
    color = color * scatTrans.w + scatTrans.xyz;

    // Gamma correction
	color = pow(color, vec3(1.0 / 2.2)); // simple linear to gamma, exposure of 1.0

	fs_output = vec4(color ,1.0);
}
#endif
