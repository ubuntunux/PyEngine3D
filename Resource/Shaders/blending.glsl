// https://github.com/jamieowen/glsl-blend

float Remap(float originalValue, float originalMin, float originalMax, float newMin, float newMax)
{
	return newMin + (((originalValue - originalMin) / (originalMax - originalMin)) * (newMax - newMin));
}

float Sharpen(float base, float sharpen)
{
    return (base - sharpen) / (1.0 - sharpen);
}

vec3 Sharpen(vec3 base, vec3 sharpen)
{
    return (base - sharpen) / (vec3(1.0) - sharpen);
}


float Contrast(float base, float contrast)
{
    return (base - 0.5) * contrast + 0.5;
}

vec3 Contrast(vec3 base, float contrast)
{
    return (base - vec3(0.5)) * contrast + vec3(0.5);
}


float ColorBurn(float base, float blend) {
	return (blend==0.0)?blend:max((1.0-((1.0-base)/blend)),0.0);
}

vec3 ColorBurn(vec3 base, vec3 blend) {
	return vec3(ColorBurn(base.r,blend.r),ColorBurn(base.g,blend.g),ColorBurn(base.b,blend.b));
}

vec3 ColorBurn(vec3 base, vec3 blend, float opacity) {
	return (ColorBurn(base, blend) * opacity + base * (1.0 - opacity));
}


float ColorDodge(float base, float blend) {
	return (blend==1.0)?blend:min(base/(1.0-blend),1.0);
}

vec3 ColorDodge(vec3 base, vec3 blend) {
	return vec3(ColorDodge(base.r,blend.r),ColorDodge(base.g,blend.g),ColorDodge(base.b,blend.b));
}

vec3 ColorDodge(vec3 base, vec3 blend, float opacity) {
	return (ColorDodge(base, blend) * opacity + base * (1.0 - opacity));
}


float Darken(float base, float blend) {
	return min(blend,base);
}

vec3 Darken(vec3 base, vec3 blend) {
	return vec3(Darken(base.r,blend.r),Darken(base.g,blend.g),Darken(base.b,blend.b));
}

vec3 Darken(vec3 base, vec3 blend, float opacity) {
	return (Darken(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Difference(vec3 base, vec3 blend) {
	return abs(base-blend);
}

vec3 Difference(vec3 base, vec3 blend, float opacity) {
	return (Difference(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Exclusion(vec3 base, vec3 blend) {
	return base+blend-2.0*base*blend;
}

vec3 Exclusion(vec3 base, vec3 blend, float opacity) {
	return (Exclusion(base, blend) * opacity + base * (1.0 - opacity));
}


float Reflect(float base, float blend) {
	return (blend==1.0)?blend:min(base*base/(1.0-blend),1.0);
}

vec3 Reflect(vec3 base, vec3 blend) {
	return vec3(Reflect(base.r,blend.r),Reflect(base.g,blend.g),Reflect(base.b,blend.b));
}

vec3 Reflect(vec3 base, vec3 blend, float opacity) {
	return (Reflect(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Glow(vec3 base, vec3 blend) {
	return Reflect(blend,base);
}

vec3 Glow(vec3 base, vec3 blend, float opacity) {
	return (Glow(base, blend) * opacity + base * (1.0 - opacity));
}



float Overlay(float base, float blend) {
	return base<0.5?(2.0*base*blend):(1.0-2.0*(1.0-base)*(1.0-blend));
}

vec3 Overlay(vec3 base, vec3 blend) {
	return vec3(Overlay(base.r,blend.r),Overlay(base.g,blend.g),Overlay(base.b,blend.b));
}

vec3 Overlay(vec3 base, vec3 blend, float opacity) {
	return (Overlay(base, blend) * opacity + base * (1.0 - opacity));
}


float HardLight(float base, float blend) {
	return Overlay(blend, base);
}

vec3 HardLight(vec3 base, vec3 blend) {
	return Overlay(blend, base);
}

vec3 HardLight(vec3 base, vec3 blend, float opacity) {
	return (HardLight(base, blend) * opacity + base * (1.0 - opacity));
}


float Lighten(float base, float blend) {
	return max(blend,base);
}

vec3 Lighten(vec3 base, vec3 blend) {
	return vec3(Lighten(base.r,blend.r),Lighten(base.g,blend.g),Lighten(base.b,blend.b));
}

vec3 Lighten(vec3 base, vec3 blend, float opacity) {
	return (Lighten(base, blend) * opacity + base * (1.0 - opacity));
}


float LinearBurn(float base, float blend) {
	return max(base+blend-1.0,0.0);
}

vec3 LinearBurn(vec3 base, vec3 blend) {
	return max(base+blend-vec3(1.0),vec3(0.0));
}

vec3 LinearBurn(vec3 base, vec3 blend, float opacity) {
	return (LinearBurn(base, blend) * opacity + base * (1.0 - opacity));
}



float LinearDodge(float base, float blend) {
	return min(base+blend,1.0);
}

vec3 LinearDodge(vec3 base, vec3 blend) {
	return min(base+blend,vec3(1.0));
}

vec3 LinearDodge(vec3 base, vec3 blend, float opacity) {
	return (LinearDodge(base, blend) * opacity + base * (1.0 - opacity));
}



float LinearLight(float base, float blend) {
	return blend<0.5?LinearBurn(base,(2.0*blend)):LinearDodge(base,(2.0*(blend-0.5)));
}

vec3 LinearLight(vec3 base, vec3 blend) {
	return vec3(LinearLight(base.r,blend.r),LinearLight(base.g,blend.g),LinearLight(base.b,blend.b));
}

vec3 LinearLight(vec3 base, vec3 blend, float opacity) {
	return (LinearLight(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Multiply(vec3 base, vec3 blend) {
	return base*blend;
}

vec3 Multiply(vec3 base, vec3 blend, float opacity) {
	return (Multiply(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Negation(vec3 base, vec3 blend) {
	return vec3(1.0)-abs(vec3(1.0)-base-blend);
}

vec3 Negation(vec3 base, vec3 blend, float opacity) {
	return (Negation(base, blend) * opacity + base * (1.0 - opacity));
}


vec3 Normal(vec3 base, vec3 blend) {
	return blend;
}

vec3 Normal(vec3 base, vec3 blend, float opacity) {
	return (Normal(base, blend) * opacity + base * (1.0 - opacity));
}


float PinLight(float base, float blend) {
	return (blend<0.5)?Darken(base,(2.0*blend)):Lighten(base,(2.0*(blend-0.5)));
}

vec3 PinLight(vec3 base, vec3 blend) {
	return vec3(PinLight(base.r,blend.r),PinLight(base.g,blend.g),PinLight(base.b,blend.b));
}

vec3 PinLight(vec3 base, vec3 blend, float opacity) {
	return (PinLight(base, blend) * opacity + base * (1.0 - opacity));
}


float Screen(float base, float blend) {
	return 1.0-((1.0-base)*(1.0-blend));
}

vec3 Screen(vec3 base, vec3 blend) {
	return vec3(Screen(base.r,blend.r),Screen(base.g,blend.g),Screen(base.b,blend.b));
}

vec3 Screen(vec3 base, vec3 blend, float opacity) {
	return (Screen(base, blend) * opacity + base * (1.0 - opacity));
}



float SoftLight(float base, float blend) {
	return (blend<0.5)?(2.0*base*blend+base*base*(1.0-2.0*blend)):(sqrt(base)*(2.0*blend-1.0)+2.0*base*(1.0-blend));
}

vec3 SoftLight(vec3 base, vec3 blend) {
	return vec3(SoftLight(base.r,blend.r),SoftLight(base.g,blend.g),SoftLight(base.b,blend.b));
}

vec3 SoftLight(vec3 base, vec3 blend, float opacity) {
	return (SoftLight(base, blend) * opacity + base * (1.0 - opacity));
}


float Subtract(float base, float blend) {
	return max(base+blend-1.0,0.0);
}

vec3 Subtract(vec3 base, vec3 blend) {
	return max(base+blend-vec3(1.0),vec3(0.0));
}

vec3 Subtract(vec3 base, vec3 blend, float opacity) {
	return (Subtract(base, blend) * opacity + base * (1.0 - opacity));
}


float VividLight(float base, float blend) {
	return (blend<0.5)?ColorBurn(base,(2.0*blend)):ColorDodge(base,(2.0*(blend-0.5)));
}

vec3 VividLight(vec3 base, vec3 blend) {
	return vec3(VividLight(base.r,blend.r),VividLight(base.g,blend.g),VividLight(base.b,blend.b));
}

vec3 VividLight(vec3 base, vec3 blend, float opacity) {
	return (VividLight(base, blend) * opacity + base * (1.0 - opacity));
}


