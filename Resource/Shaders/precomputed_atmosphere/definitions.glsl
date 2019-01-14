#include "scene_constants.glsl"

#define COMBINED_SCATTERING_TEXTURES 0

uniform vec3 earth_center;
uniform vec2 sun_size;
uniform float atmosphere_exposure;
uniform bool render_light_probe_mode;

uniform sampler2D transmittance_texture;
uniform sampler2D irradiance_texture;
uniform sampler3D scattering_texture;
uniform sampler3D single_mie_scattering_texture;
uniform sampler3D single_rayleigh_scattering_texture;
uniform sampler3D scattering_density_texture;
uniform sampler3D multiple_scattering_texture;


uniform vec3 SKY_RADIANCE_TO_LUMINANCE;
uniform vec3 SUN_RADIANCE_TO_LUMINANCE;

const float atmosphere_ratio = 0.1;

struct DensityProfileLayer
{
    float width;
    float exp_term;
    float exp_scale;
    float linear_term;
    float constant_term;
};

struct DensityProfile
{
    DensityProfileLayer layers[2];
};

struct AtmosphereParameters
{
    vec3 solar_irradiance;
    float sun_angular_radius;
    float bottom_radius;
    float top_radius;
    DensityProfile rayleigh_density;
    vec3 rayleigh_scattering;
    DensityProfile mie_density;
    vec3 mie_scattering;
    vec3 mie_extinction;
    float mie_phase_function_g;
    DensityProfile absorption_density;
    vec3 absorption_extinction;
    vec3 ground_albedo;
    float mu_s_min;
};


float ClampCosine(float mu)
{
    return clamp(mu, -1.0, 1.0);
}

float ClampDistance(float d)
{
    return max(d, 0.0);
}

float ClampRadius(const in AtmosphereParameters atmosphere, float r)
{
    return clamp(r, atmosphere.bottom_radius, atmosphere.top_radius);
}

float SafeSqrt(float a)
{
    return sqrt(max(a, 0.0));
}

float DistanceToTopAtmosphereBoundary(const in AtmosphereParameters atmosphere, float r, float mu)
{
    float discriminant = r * r * (mu * mu - 1.0) + atmosphere.top_radius * atmosphere.top_radius;
    return ClampDistance(-r * mu + SafeSqrt(discriminant));
}

float DistanceToBottomAtmosphereBoundary(const in AtmosphereParameters atmosphere, float r, float mu)
{
    float discriminant = r * r * (mu * mu - 1.0) + atmosphere.bottom_radius * atmosphere.bottom_radius;
    return ClampDistance(-r * mu - SafeSqrt(discriminant));
}

bool RayIntersectsGround(const in AtmosphereParameters atmosphere, float r, float mu)
{
    if(mu < 0.0)
    {
        float result = r * r * (mu * mu - 1.0) + atmosphere.bottom_radius * atmosphere.bottom_radius;
        if(0.0 <= result)
        {
            return true;
        }
    }
    return false;
}

float GetLayerDensity(const in DensityProfileLayer layer, float altitude)
{
    float density =
        layer.exp_term * exp(layer.exp_scale * altitude) + layer.linear_term * altitude + layer.constant_term;
    return clamp(density, 0.0, 1.0);
}

float GetProfileDensity(const in DensityProfile profile, float altitude)
{
    return altitude < profile.layers[0].width ?
        GetLayerDensity(profile.layers[0], altitude) : GetLayerDensity(profile.layers[1], altitude);
}

float ComputeOpticalLengthToTopAtmosphereBoundary(
    const in AtmosphereParameters atmosphere,
    const in DensityProfile profile,
    float r,
    float mu)
{
    const int SAMPLE_COUNT = 500;
    float dx = DistanceToTopAtmosphereBoundary(atmosphere, r, mu) / float(SAMPLE_COUNT);
    float result = 0.0;
    for (int i = 0; i <= SAMPLE_COUNT; ++i)
    {
        float d_i = float(i) * dx;
        float r_i = sqrt(d_i * d_i + 2.0 * r * mu * d_i + r * r);
        float y_i = GetProfileDensity(profile, r_i - atmosphere.bottom_radius);
        float weight_i = (i == 0 || i == SAMPLE_COUNT) ? 0.5 : 1.0;
        result += y_i * weight_i * dx;
    }
    return result;
}


vec3 ComputeTransmittanceToTopAtmosphereBoundary(
    const in AtmosphereParameters atmosphere,
    float r,
    float mu)
{
    return exp(-(
        atmosphere.rayleigh_scattering *
            ComputeOpticalLengthToTopAtmosphereBoundary(atmosphere, atmosphere.rayleigh_density, r, mu) +
        atmosphere.mie_extinction *
            ComputeOpticalLengthToTopAtmosphereBoundary(atmosphere, atmosphere.mie_density, r, mu) +
        atmosphere.absorption_extinction *
            ComputeOpticalLengthToTopAtmosphereBoundary(atmosphere, atmosphere.absorption_density, r, mu)));
}

float GetTextureCoordFromUnitRange(float x, int texture_size)
{
    return 0.5 / float(texture_size) + x * (1.0 - 1.0 / float(texture_size));
}

float GetUnitRangeFromTextureCoord(float u, int texture_size)
{
    return (u - 0.5 / float(texture_size)) / (1.0 - 1.0 / float(texture_size));
}

vec2 GetTransmittanceTextureUvFromRMu(const in AtmosphereParameters atmosphere, float r, float mu)
{
    float H = sqrt(atmosphere.top_radius * atmosphere.top_radius -
        atmosphere.bottom_radius * atmosphere.bottom_radius);
    float rho = SafeSqrt(r * r - atmosphere.bottom_radius * atmosphere.bottom_radius);
    float d = DistanceToTopAtmosphereBoundary(atmosphere, r, mu);
    float d_min = atmosphere.top_radius - r;
    float d_max = rho + H;
    float x_mu = (d - d_min) / (d_max - d_min);
    float x_r = rho / H;
    return vec2(GetTextureCoordFromUnitRange(x_mu, TRANSMITTANCE_TEXTURE_WIDTH),
              GetTextureCoordFromUnitRange(x_r, TRANSMITTANCE_TEXTURE_HEIGHT));
}

void GetRMuFromTransmittanceTextureUv(const in AtmosphereParameters atmosphere,
    const in vec2 uv, out float r, out float mu)
{
    float x_mu = GetUnitRangeFromTextureCoord(uv.x, TRANSMITTANCE_TEXTURE_WIDTH);
    float x_r = GetUnitRangeFromTextureCoord(uv.y, TRANSMITTANCE_TEXTURE_HEIGHT);

    float H = sqrt(atmosphere.top_radius * atmosphere.top_radius -
        atmosphere.bottom_radius * atmosphere.bottom_radius);

    float rho = H * x_r;
    r = sqrt(rho * rho + atmosphere.bottom_radius * atmosphere.bottom_radius);
    float d_min = atmosphere.top_radius - r;
    float d_max = rho + H;
    float d = d_min + x_mu * (d_max - d_min);
    mu = (d == 0.0) ? 1.0 : (H * H - rho * rho - d * d) / (2.0 * r * d);
    mu = ClampCosine(mu);
}


vec3 ComputeTransmittanceToTopAtmosphereBoundarytexture2D(
    const in AtmosphereParameters atmosphere,
    const in vec2 gl_frag_coord)
{
    const vec2 TRANSMITTANCE_TEXTURE_SIZE = vec2(TRANSMITTANCE_TEXTURE_WIDTH, TRANSMITTANCE_TEXTURE_HEIGHT);
    float r;
    float mu;
    GetRMuFromTransmittanceTextureUv(atmosphere, gl_frag_coord / TRANSMITTANCE_TEXTURE_SIZE, r, mu);
    return ComputeTransmittanceToTopAtmosphereBoundary(atmosphere, r, mu);
}


vec3 GetTransmittanceToTopAtmosphereBoundary(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r, float mu)
{
    vec2 uv = GetTransmittanceTextureUvFromRMu(atmosphere, r, mu);
    return vec3(texture2D(transmittance_texture, uv));
}


vec3 GetTransmittance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r,
    float mu,
    float d,
    bool ray_r_mu_intersects_ground)
{
    float r_d = ClampRadius(atmosphere, sqrt(d * d + 2.0 * r * mu * d + r * r));
    float mu_d = ClampCosine((r * mu + d) / r_d);
    if (ray_r_mu_intersects_ground)
    {
        return min(
            GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r_d, -mu_d) /
            GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r, -mu),
            vec3(1.0));
    }
    else
    {
        return min(
            GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r, mu) /
            GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r_d, mu_d),
            vec3(1.0));
    }
}


vec3 GetTransmittanceToSun(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r,
    float mu_s)
{
    float sin_theta_h = atmosphere.bottom_radius / r;
    float cos_theta_h = -sqrt(max(1.0 - sin_theta_h * sin_theta_h, 0.0));
    return GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r, mu_s) *
      smoothstep(-sin_theta_h * atmosphere.sun_angular_radius,
                 sin_theta_h * atmosphere.sun_angular_radius,
                 mu_s - cos_theta_h);
}


void ComputeSingleScatteringIntegrand(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r,
    float mu,
    float mu_s,
    float nu,
    float d,
    bool ray_r_mu_intersects_ground,
    out vec3 rayleigh,
    out vec3 mie)
{
    float r_d = ClampRadius(atmosphere, sqrt(d * d + 2.0 * r * mu * d + r * r));
    float mu_s_d = ClampCosine((r * mu_s + d * nu) / r_d);
    vec3 transmittance =
        GetTransmittance(atmosphere, transmittance_texture, r, mu, d, ray_r_mu_intersects_ground) *
        GetTransmittanceToSun(atmosphere, transmittance_texture, r_d, mu_s_d);
    rayleigh = transmittance * GetProfileDensity(atmosphere.rayleigh_density, r_d - atmosphere.bottom_radius);
    mie = transmittance * GetProfileDensity(atmosphere.mie_density, r_d - atmosphere.bottom_radius);
}


float DistanceToNearestAtmosphereBoundary(
    const in AtmosphereParameters atmosphere,
    float r,
    float mu,
    bool ray_r_mu_intersects_ground)
{
    if (ray_r_mu_intersects_ground)
    {
        return DistanceToBottomAtmosphereBoundary(atmosphere, r, mu);
    }
    return DistanceToTopAtmosphereBoundary(atmosphere, r, mu);
}


void ComputeSingleScattering(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r,
    float mu,
    float mu_s,
    float nu,
    bool ray_r_mu_intersects_ground,
    out vec3 rayleigh,
    out vec3 mie)
{
    const int SAMPLE_COUNT = 50;
    float dx = DistanceToNearestAtmosphereBoundary(atmosphere, r, mu, ray_r_mu_intersects_ground) / float(SAMPLE_COUNT);

    vec3 rayleigh_sum = vec3(0.0);
    vec3 mie_sum = vec3(0.0);
    for (int i = 0; i <= SAMPLE_COUNT; ++i)
    {
        float d_i = float(i) * dx;
        vec3 rayleigh_i;
        vec3 mie_i;
        ComputeSingleScatteringIntegrand(
            atmosphere, transmittance_texture, r, mu, mu_s, nu, d_i, ray_r_mu_intersects_ground, rayleigh_i, mie_i);
        float weight_i = (i == 0 || i == SAMPLE_COUNT) ? 0.5 : 1.0;
        rayleigh_sum += rayleigh_i * weight_i;
        mie_sum += mie_i * weight_i;
    }
    rayleigh = rayleigh_sum * dx * atmosphere.solar_irradiance * atmosphere.rayleigh_scattering;
    mie = mie_sum * dx * atmosphere.solar_irradiance * atmosphere.mie_scattering;
}


float RayleighPhaseFunction(float nu)
{
    float k = 3.0 / (16.0 * PI);
    return k * (1.0 + nu * nu);
}

float MiePhaseFunction(float g, float nu)
{
    float k = 3.0 / (8.0 * PI) * (1.0 - g * g) / (2.0 + g * g);
    return k * (1.0 + nu * nu) / pow(1.0 + g * g - 2.0 * g * nu, 1.5);
}


vec4 GetScatteringTextureUvwzFromRMuMuSNu(
    const in AtmosphereParameters atmosphere,
    float r,
    float mu,
    float mu_s,
    float nu,
    bool ray_r_mu_intersects_ground)
{
    float H = sqrt(atmosphere.top_radius * atmosphere.top_radius - atmosphere.bottom_radius * atmosphere.bottom_radius);
    float rho = SafeSqrt(r * r - atmosphere.bottom_radius * atmosphere.bottom_radius);
    float u_r = GetTextureCoordFromUnitRange(rho / H, SCATTERING_TEXTURE_R_SIZE);
    float r_mu = r * mu;
    float discriminant = r_mu * r_mu - r * r + atmosphere.bottom_radius * atmosphere.bottom_radius;
    float u_mu;
    if (ray_r_mu_intersects_ground)
    {
        float d = -r_mu - SafeSqrt(discriminant);
        float d_min = r - atmosphere.bottom_radius;
        float d_max = rho;
        u_mu = 0.5 - 0.5 * GetTextureCoordFromUnitRange(
            d_max == d_min ? 0.0 : (d - d_min) / (d_max - d_min), SCATTERING_TEXTURE_MU_SIZE / 2);
    }
    else
    {
        float d = -r_mu + SafeSqrt(discriminant + H * H);
        float d_min = atmosphere.top_radius - r;
        float d_max = rho + H;
        u_mu = 0.5 + 0.5 * GetTextureCoordFromUnitRange(
            (d - d_min) / (d_max - d_min), SCATTERING_TEXTURE_MU_SIZE / 2);
    }

    float d = DistanceToTopAtmosphereBoundary(atmosphere, atmosphere.bottom_radius, mu_s);
    float d_min = atmosphere.top_radius - atmosphere.bottom_radius;
    float d_max = H;
    float a = (d - d_min) / (d_max - d_min);
    float A = -2.0 * atmosphere.mu_s_min * atmosphere.bottom_radius / (d_max - d_min);
    float u_mu_s = GetTextureCoordFromUnitRange(max(1.0 - a / A, 0.0) / (1.0 + a), SCATTERING_TEXTURE_MU_S_SIZE);
    float u_nu = (nu + 1.0) / 2.0;
    return vec4(u_nu, u_mu_s, u_mu, u_r);
}


void GetRMuMuSNuFromScatteringTextureUvwz(
    const in AtmosphereParameters atmosphere,
    const in vec4 uvwz,
    out float r,
    out float mu,
    out float mu_s,
    out float nu,
    out bool ray_r_mu_intersects_ground)
{
    float H = sqrt(atmosphere.top_radius * atmosphere.top_radius - atmosphere.bottom_radius * atmosphere.bottom_radius);
    float rho = H * GetUnitRangeFromTextureCoord(uvwz.w, SCATTERING_TEXTURE_R_SIZE);
    r = sqrt(rho * rho + atmosphere.bottom_radius * atmosphere.bottom_radius);
    if (uvwz.z < 0.5)
    {
        float d_min = r - atmosphere.bottom_radius;
        float d_max = rho;
        float d = d_min + (d_max - d_min) *
            GetUnitRangeFromTextureCoord(1.0 - 2.0 * uvwz.z, SCATTERING_TEXTURE_MU_SIZE / 2);
        mu = (d == 0.0) ? -1.0 : ClampCosine(-(rho * rho + d * d) / (2.0 * r * d));
        ray_r_mu_intersects_ground = true;
    }
    else
    {
        float d_min = atmosphere.top_radius - r;
        float d_max = rho + H;
        float d = d_min + (d_max - d_min) *
            GetUnitRangeFromTextureCoord(2.0 * uvwz.z - 1.0, SCATTERING_TEXTURE_MU_SIZE / 2);
        mu = (d == 0.0) ? 1.0 : ClampCosine((H * H - rho * rho - d * d) / (2.0 * r * d));
        ray_r_mu_intersects_ground = false;
    }

    float x_mu_s = GetUnitRangeFromTextureCoord(uvwz.y, SCATTERING_TEXTURE_MU_S_SIZE);
    float d_min = atmosphere.top_radius - atmosphere.bottom_radius;
    float d_max = H;
    float A = -2.0 * atmosphere.mu_s_min * atmosphere.bottom_radius / (d_max - d_min);
    float a = (A - x_mu_s * A) / (1.0 + x_mu_s * A);
    float d = d_min + min(a, A) * (d_max - d_min);
    mu_s = (d == 0.0) ? 1.0 : ClampCosine((H * H - d * d) / (2.0 * atmosphere.bottom_radius * d));
    nu = ClampCosine(uvwz.x * 2.0 - 1.0);
}


void GetRMuMuSNuFromScatteringTextureFragCoord(
    const in AtmosphereParameters atmosphere,
    const in vec3 gl_frag_coord,
    out float r,
    out float mu,
    out float mu_s,
    out float nu,
    out bool ray_r_mu_intersects_ground)
{
    const vec4 SCATTERING_TEXTURE_SIZE = vec4(
        SCATTERING_TEXTURE_NU_SIZE - 1,
        SCATTERING_TEXTURE_MU_S_SIZE,
        SCATTERING_TEXTURE_MU_SIZE,
        SCATTERING_TEXTURE_R_SIZE);
    float frag_coord_nu = floor(gl_frag_coord.x / float(SCATTERING_TEXTURE_MU_S_SIZE));
    float frag_coord_mu_s = mod(gl_frag_coord.x, float(SCATTERING_TEXTURE_MU_S_SIZE));
    vec4 uvwz = vec4(frag_coord_nu, frag_coord_mu_s, gl_frag_coord.y, gl_frag_coord.z) / SCATTERING_TEXTURE_SIZE;
    GetRMuMuSNuFromScatteringTextureUvwz(atmosphere, uvwz, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    nu = clamp(
        nu,
        mu * mu_s - sqrt((1.0 - mu * mu) * (1.0 - mu_s * mu_s)),
        mu * mu_s + sqrt((1.0 - mu * mu) * (1.0 - mu_s * mu_s)));
}


void ComputeSingleScatteringtexture2D(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in vec3 gl_frag_coord,
    out vec3 rayleigh, out vec3 mie)
{
    float r;
    float mu;
    float mu_s;
    float nu;
    bool ray_r_mu_intersects_ground;
    GetRMuMuSNuFromScatteringTextureFragCoord(atmosphere, gl_frag_coord,
        r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    ComputeSingleScattering(atmosphere, transmittance_texture,
        r, mu, mu_s, nu, ray_r_mu_intersects_ground, rayleigh, mie);
}


vec3 GetScattering(
    const in AtmosphereParameters atmosphere,
    const in sampler3D scattering_texture,
    float r, float mu, float mu_s, float nu,
    bool ray_r_mu_intersects_ground)
{
    vec4 uvwz = GetScatteringTextureUvwzFromRMuMuSNu(atmosphere, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    float tex_coord_x = uvwz.x * float(SCATTERING_TEXTURE_NU_SIZE - 1);
    float tex_x = floor(tex_coord_x);
    float lerp = tex_coord_x - tex_x;
    vec3 uvw0 = vec3((tex_x + uvwz.y) / float(SCATTERING_TEXTURE_NU_SIZE), uvwz.z, uvwz.w);
    vec3 uvw1 = vec3((tex_x + 1.0 + uvwz.y) / float(SCATTERING_TEXTURE_NU_SIZE), uvwz.z, uvwz.w);
    return vec3(
        texture3D(scattering_texture, uvw0) * (1.0 - lerp) + texture3D(scattering_texture, uvw1) * lerp);
}

vec3 GetScattering(
    const in AtmosphereParameters atmosphere,
    const in sampler3D single_rayleigh_scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    const in sampler3D multiple_scattering_texture,
    float r, float mu, float mu_s, float nu,
    bool ray_r_mu_intersects_ground,
    int scattering_order)
{
    if (scattering_order == 1)
    {
        vec3 rayleigh = GetScattering(
            atmosphere, single_rayleigh_scattering_texture, r, mu, mu_s, nu,
            ray_r_mu_intersects_ground);
        vec3 mie = GetScattering(
            atmosphere, single_mie_scattering_texture, r, mu, mu_s, nu,
            ray_r_mu_intersects_ground);

        return rayleigh * RayleighPhaseFunction(nu) + mie * MiePhaseFunction(atmosphere.mie_phase_function_g, nu);
    }

    return GetScattering(atmosphere, multiple_scattering_texture, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
}

vec3 GetIrradiance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D irradiance_texture,
    float r, float mu_s);

vec3 ComputeScatteringDensity(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D single_rayleigh_scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    const in sampler3D multiple_scattering_texture,
    const in sampler2D irradiance_texture,
    float r, float mu, float mu_s, float nu, int scattering_order)
{
    vec3 zenith_direction = vec3(0.0, 0.0, 1.0);
    vec3 omega = vec3(sqrt(1.0 - mu * mu), 0.0, mu);
    float sun_dir_x = omega.x == 0.0 ? 0.0 : (nu - mu * mu_s) / omega.x;
    float sun_dir_y = sqrt(max(1.0 - sun_dir_x * sun_dir_x - mu_s * mu_s, 0.0));
    vec3 omega_s = vec3(sun_dir_x, sun_dir_y, mu_s);

    const int SAMPLE_COUNT = 16;
    const float dphi = PI / float(SAMPLE_COUNT);
    const float dtheta = PI / float(SAMPLE_COUNT);
    vec3 rayleigh_mie = vec3(0.0);

    for (int l = 0; l < SAMPLE_COUNT; ++l)
    {
        float theta = (float(l) + 0.5) * dtheta;
        float cos_theta = cos(theta);
        float sin_theta = sin(theta);
        bool ray_r_theta_intersects_ground = RayIntersectsGround(atmosphere, r, cos_theta);

        float distance_to_ground = 0.0;
        vec3 transmittance_to_ground = vec3(0.0);
        vec3 ground_albedo = vec3(0.0);
        if (ray_r_theta_intersects_ground)
        {
            distance_to_ground = DistanceToBottomAtmosphereBoundary(atmosphere, r, cos_theta);
            transmittance_to_ground = GetTransmittance(atmosphere, transmittance_texture, r, cos_theta, distance_to_ground, true );
            ground_albedo = atmosphere.ground_albedo;
        }

        for (int m = 0; m < 2 * SAMPLE_COUNT; ++m)
        {
            float phi = 1.5 * dphi;
            vec3 omega_i = vec3(cos(phi) * sin_theta, sin(phi) * sin_theta, cos_theta);
            float domega_i = dtheta * dphi * sin(theta);

            float nu1 = dot(omega_s, omega_i);
            vec3 incident_radiance = GetScattering(atmosphere,
                single_rayleigh_scattering_texture, single_mie_scattering_texture,
                multiple_scattering_texture, r, omega_i.z, mu_s, nu1,
                ray_r_theta_intersects_ground, scattering_order - 1);

            vec3 ground_normal = normalize(zenith_direction * r + omega_i * distance_to_ground);
            vec3 ground_irradiance = GetIrradiance(
                atmosphere, irradiance_texture, atmosphere.bottom_radius,
                dot(ground_normal, omega_s));
            incident_radiance += transmittance_to_ground * ground_albedo * (1.0 / (PI)) * ground_irradiance;

            float nu2 = dot(omega, omega_i);
            float rayleigh_density = GetProfileDensity(
                atmosphere.rayleigh_density, r - atmosphere.bottom_radius);
            float mie_density = GetProfileDensity(
                atmosphere.mie_density, r - atmosphere.bottom_radius);
            rayleigh_mie += incident_radiance *
                (atmosphere.rayleigh_scattering * rayleigh_density * RayleighPhaseFunction(nu2) +
                atmosphere.mie_scattering * mie_density *
                MiePhaseFunction(atmosphere.mie_phase_function_g, nu2)) * domega_i;
        }
    }
    return rayleigh_mie;
}


vec3 ComputeMultipleScattering(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D scattering_density_texture,
    float r, float mu, float mu_s, float nu,
    bool ray_r_mu_intersects_ground)
{
    const int SAMPLE_COUNT = 50;
    float dx = DistanceToNearestAtmosphereBoundary(atmosphere, r, mu, ray_r_mu_intersects_ground) / float(SAMPLE_COUNT);
    vec3 rayleigh_mie_sum = vec3(0.0);
    for (int i = 0; i <= SAMPLE_COUNT; ++i)
    {
        float d_i = float(i) * dx;
        float r_i = ClampRadius(atmosphere, sqrt(d_i * d_i + 2.0 * r * mu * d_i + r * r));
        float mu_i = ClampCosine((r * mu + d_i) / r_i);
        float mu_s_i = ClampCosine((r * mu_s + d_i * nu) / r_i);
        vec3 rayleigh_mie_i =
            GetScattering(atmosphere, scattering_density_texture, r_i, mu_i, mu_s_i, nu, ray_r_mu_intersects_ground) *
            GetTransmittance(atmosphere, transmittance_texture, r, mu, d_i, ray_r_mu_intersects_ground) * dx;
        float weight_i = (i == 0 || i == SAMPLE_COUNT) ? 0.5 : 1.0;
        rayleigh_mie_sum += rayleigh_mie_i * weight_i;
    }
    return rayleigh_mie_sum;
}


vec3 ComputeScatteringDensitytexture2D(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D single_rayleigh_scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    const in sampler3D multiple_scattering_texture,
    const in sampler2D irradiance_texture,
    const in vec3 gl_frag_coord, int scattering_order)
{
    float r;
    float mu;
    float mu_s;
    float nu;
    bool ray_r_mu_intersects_ground;
    GetRMuMuSNuFromScatteringTextureFragCoord(atmosphere, gl_frag_coord, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    return ComputeScatteringDensity(atmosphere, transmittance_texture,
        single_rayleigh_scattering_texture, single_mie_scattering_texture,
        multiple_scattering_texture, irradiance_texture, r, mu, mu_s, nu,
        scattering_order);
}


vec3 ComputeMultipleScatteringtexture2D(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D scattering_density_texture,
    const in vec3 gl_frag_coord, out float nu)
{
    float r;
    float mu;
    float mu_s;
    bool ray_r_mu_intersects_ground;
    GetRMuMuSNuFromScatteringTextureFragCoord(atmosphere, gl_frag_coord, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    return ComputeMultipleScattering(atmosphere, transmittance_texture,
        scattering_density_texture, r, mu, mu_s, nu,
        ray_r_mu_intersects_ground);
}


vec3 ComputeDirectIrradiance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    float r,
    float mu_s)
{
    float alpha_s = atmosphere.sun_angular_radius;
    float average_cosine_factor = 0.0;
    if(-alpha_s <= mu_s)
    {
        if(mu_s <= alpha_s)
        {
            average_cosine_factor = (mu_s + alpha_s) * (mu_s + alpha_s) / (4.0 * alpha_s);
        }
        else
        {
            average_cosine_factor = mu_s;
        }
    }

    return atmosphere.solar_irradiance *
        GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r, mu_s) * average_cosine_factor;
}


vec3 ComputeIndirectIrradiance(
    const in AtmosphereParameters atmosphere,
    const in sampler3D single_rayleigh_scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    const in sampler3D multiple_scattering_texture,
    float r,
    float mu_s,
    int scattering_order)
{
    const int SAMPLE_COUNT = 32;
    const float dphi = PI / float(SAMPLE_COUNT);
    const float dtheta = PI / float(SAMPLE_COUNT);

    vec3 result = vec3(0.0);
    vec3 omega_s = vec3(sqrt(1.0 - mu_s * mu_s), 0.0, mu_s);
    for (int j = 0; j < SAMPLE_COUNT / 2; ++j)
    {
        float theta = (float(j) + 0.5) * dtheta;
        for (int i = 0; i < 2 * SAMPLE_COUNT; ++i)
        {
            float phi = (float(i) + 0.5) * dphi;
            vec3 omega = vec3(cos(phi) * sin(theta), sin(phi) * sin(theta), cos(theta));
            float domega = dtheta * dphi * sin(theta);
            float nu = dot(omega, omega_s);
            result += GetScattering(
                atmosphere,
                single_rayleigh_scattering_texture,
                single_mie_scattering_texture,
                multiple_scattering_texture,
                r, omega.z, mu_s, nu, false, scattering_order) * omega.z * domega;
        }
    }
  return result;
}


vec2 GetIrradianceTextureUvFromRMuS(const in AtmosphereParameters atmosphere, float r, float mu_s)
{
    float x_r = (r - atmosphere.bottom_radius) / (atmosphere.top_radius - atmosphere.bottom_radius);
    float x_mu_s = mu_s * 0.5 + 0.5;
    return vec2(GetTextureCoordFromUnitRange(x_mu_s, IRRADIANCE_TEXTURE_WIDTH),
                GetTextureCoordFromUnitRange(x_r, IRRADIANCE_TEXTURE_HEIGHT));
}


void GetRMuSFromIrradianceTextureUv(const in AtmosphereParameters atmosphere,
    const in vec2 uv, out float r, out float mu_s)
{
    float x_mu_s = GetUnitRangeFromTextureCoord(uv.x, IRRADIANCE_TEXTURE_WIDTH);
    float x_r = GetUnitRangeFromTextureCoord(uv.y, IRRADIANCE_TEXTURE_HEIGHT);
    r = atmosphere.bottom_radius + x_r * (atmosphere.top_radius - atmosphere.bottom_radius);
    mu_s = ClampCosine(2.0 * x_mu_s - 1.0);
}

vec3 ComputeDirectIrradiancetexture2D(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in vec2 gl_frag_coord)
{
    float r;
    float mu_s;
    GetRMuSFromIrradianceTextureUv(atmosphere, gl_frag_coord / IRRADIANCE_TEXTURE_SIZE, r, mu_s);
    return ComputeDirectIrradiance(atmosphere, transmittance_texture, r, mu_s);
}


vec3 ComputeIndirectIrradiancetexture2D(
    const in AtmosphereParameters atmosphere,
    const in sampler3D single_rayleigh_scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    const in sampler3D multiple_scattering_texture,
    const in vec2 gl_frag_coord, int scattering_order)
{
    float r;
    float mu_s;
    GetRMuSFromIrradianceTextureUv(atmosphere, gl_frag_coord / IRRADIANCE_TEXTURE_SIZE, r, mu_s);
    return ComputeIndirectIrradiance(atmosphere, single_rayleigh_scattering_texture, single_mie_scattering_texture,
        multiple_scattering_texture, r, mu_s, scattering_order);
}


vec3 GetIrradiance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D irradiance_texture,
    float r,
    float mu_s)
{
    vec2 uv = GetIrradianceTextureUvFromRMuS(atmosphere, r, mu_s);
    return vec3(texture2D(irradiance_texture, uv));
}


#if COMBINED_SCATTERING_TEXTURES == 1
vec3 GetExtrapolatedSingleMieScattering(const in AtmosphereParameters atmosphere, const in vec4 scattering)
{
    if (scattering.r == 0.0)
    {
        return vec3(0.0);
    }
    return scattering.rgb * scattering.a / scattering.r *
        (atmosphere.rayleigh_scattering.r / atmosphere.mie_scattering.r) *
        (atmosphere.mie_scattering / atmosphere.rayleigh_scattering);
}
#endif


vec3 GetCombinedScattering(
    const in AtmosphereParameters atmosphere,
    const in sampler3D scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    float r, float mu, float mu_s, float nu,
    bool ray_r_mu_intersects_ground,
    out vec3 single_mie_scattering)
{
    vec4 uvwz = GetScatteringTextureUvwzFromRMuMuSNu(atmosphere, r, mu, mu_s, nu, ray_r_mu_intersects_ground);
    float tex_coord_x = uvwz.x * float(SCATTERING_TEXTURE_NU_SIZE - 1);
    float tex_x = floor(tex_coord_x);
    float lerp = tex_coord_x - tex_x;
    vec3 uvw0 = vec3((tex_x + uvwz.y) / float(SCATTERING_TEXTURE_NU_SIZE), uvwz.z, uvwz.w);
    vec3 uvw1 = vec3((tex_x + 1.0 + uvwz.y) / float(SCATTERING_TEXTURE_NU_SIZE), uvwz.z, uvwz.w);
#if COMBINED_SCATTERING_TEXTURES == 1
    vec4 combined_scattering =
        texture3D(scattering_texture, uvw0) * (1.0 - lerp) + texture3D(scattering_texture, uvw1) * lerp;
    vec3 scattering = vec3(combined_scattering.xyz);
    single_mie_scattering = GetExtrapolatedSingleMieScattering(atmosphere, combined_scattering);
#else
    vec3 scattering = vec3(
        texture3D(scattering_texture, uvw0) * (1.0 - lerp) + texture3D(scattering_texture, uvw1) * lerp);
    single_mie_scattering = vec3(
        texture3D(single_mie_scattering_texture, uvw0) * (1.0 - lerp) +
        texture3D(single_mie_scattering_texture, uvw1) * lerp);
#endif
    return scattering;
}


vec3 ComputeSkyRadiance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    vec3 camera, const in vec3 view_ray, float shadow_length,
    const in vec3 sun_direction, out vec3 transmittance)
{
    float r = length(camera);
    float rmu = dot(camera, view_ray);
    float distance_to_top_atmosphere_boundary = -rmu -
        sqrt(rmu * rmu - r * r + atmosphere.top_radius * atmosphere.top_radius);

    if (distance_to_top_atmosphere_boundary > 0.0)
    {
        camera = camera + view_ray * distance_to_top_atmosphere_boundary;
        r = atmosphere.top_radius;
        rmu += distance_to_top_atmosphere_boundary;
    }
    else if(r > atmosphere.top_radius)
    {
        transmittance = vec3(1.0);
        return vec3(0.0);
    }

    float mu = rmu / r;
    float mu_s = dot(camera, sun_direction) / r;
    float nu = dot(view_ray, sun_direction);
    bool ray_r_mu_intersects_ground = RayIntersectsGround(atmosphere, r, mu);

    transmittance = ray_r_mu_intersects_ground ?
        vec3(0.0) : GetTransmittanceToTopAtmosphereBoundary(atmosphere, transmittance_texture, r, mu);
    vec3 single_mie_scattering;
    vec3 scattering;
    if (shadow_length == 0.0)
    {
        scattering = GetCombinedScattering(
            atmosphere, scattering_texture, single_mie_scattering_texture,
            r, mu, mu_s, nu, ray_r_mu_intersects_ground, single_mie_scattering);
    }
    else
    {
        float d = shadow_length;
        float r_p = ClampRadius(atmosphere, sqrt(d * d + 2.0 * r * mu * d + r * r));
        float mu_p = (r * mu + d) / r_p;
        float mu_s_p = (r * mu_s + d * nu) / r_p;

        scattering = GetCombinedScattering(
            atmosphere, scattering_texture, single_mie_scattering_texture,
            r_p, mu_p, mu_s_p, nu, ray_r_mu_intersects_ground, single_mie_scattering);
        vec3 shadow_transmittance =
            GetTransmittance(atmosphere, transmittance_texture, r, mu, shadow_length, ray_r_mu_intersects_ground);
        scattering = scattering * shadow_transmittance;
        single_mie_scattering = single_mie_scattering * shadow_transmittance;
    }

    return scattering * RayleighPhaseFunction(nu) + single_mie_scattering *
        MiePhaseFunction(atmosphere.mie_phase_function_g, nu);
}


vec3 ComputeSkyRadianceToPoint(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler3D scattering_texture,
    const in sampler3D single_mie_scattering_texture,
    vec3 camera, const in vec3 point, float shadow_length,
    const in vec3 sun_direction, out vec3 transmittance)
{
    vec3 view_ray = normalize(point - camera);
    float r = length(camera);
    float rmu = dot(camera, view_ray);
    float distance_to_top_atmosphere_boundary =
        -rmu - sqrt(rmu * rmu - r * r + atmosphere.top_radius * atmosphere.top_radius);

    if (distance_to_top_atmosphere_boundary > 0.0)
    {
        camera = camera + view_ray * distance_to_top_atmosphere_boundary;
        r = atmosphere.top_radius;
        rmu += distance_to_top_atmosphere_boundary;
    }

    float mu = rmu / r;
    float mu_s = dot(camera, sun_direction) / r;
    float nu = dot(view_ray, sun_direction);
    float d = length(point - camera);
    bool ray_r_mu_intersects_ground = RayIntersectsGround(atmosphere, r, mu);

    transmittance = GetTransmittance(atmosphere, transmittance_texture, r, mu, d, ray_r_mu_intersects_ground);

    vec3 single_mie_scattering;
    vec3 scattering = GetCombinedScattering(
        atmosphere, scattering_texture, single_mie_scattering_texture,
        r, mu, mu_s, nu, ray_r_mu_intersects_ground,
        single_mie_scattering);

    d = max(d - shadow_length, 0.0);
    float r_p = ClampRadius(atmosphere, sqrt(d * d + 2.0 * r * mu * d + r * r));
    float mu_p = (r * mu + d) / r_p;
    float mu_s_p = (r * mu_s + d * nu) / r_p;

    vec3 single_mie_scattering_p;
    vec3 scattering_p = GetCombinedScattering(
        atmosphere, scattering_texture, single_mie_scattering_texture,
        r_p, mu_p, mu_s_p, nu, ray_r_mu_intersects_ground,
        single_mie_scattering_p);

    vec3 shadow_transmittance = transmittance;
    if (shadow_length > 0.0)
    {
        shadow_transmittance = GetTransmittance(
            atmosphere, transmittance_texture, r, mu, d, ray_r_mu_intersects_ground);
    }
    scattering = scattering - shadow_transmittance * scattering_p;
    single_mie_scattering = single_mie_scattering - shadow_transmittance * single_mie_scattering_p;
#if COMBINED_SCATTERING_TEXTURES == 1
    single_mie_scattering = GetExtrapolatedSingleMieScattering(atmosphere, vec4(scattering, single_mie_scattering.r));
#endif

    single_mie_scattering = single_mie_scattering * smoothstep(0.0, float(0.01), mu_s);

    return scattering * RayleighPhaseFunction(nu) + single_mie_scattering *
        MiePhaseFunction(atmosphere.mie_phase_function_g, nu);
}

vec3 ComputeSunAndSkyIrradiance(
    const in AtmosphereParameters atmosphere,
    const in sampler2D transmittance_texture,
    const in sampler2D irradiance_texture,
    const in vec3 point, const in vec3 normal, const in vec3 sun_direction,
    out vec3 sky_irradiance)
{
    float r = length(point);
    float mu_s = dot(point, sun_direction) / r;

    sky_irradiance = GetIrradiance(atmosphere, irradiance_texture, r, mu_s) * (1.0 + dot(normal, point) / r) * 0.5;

    return atmosphere.solar_irradiance *
        GetTransmittanceToSun(atmosphere, transmittance_texture, r, mu_s) *
        max(dot(normal, sun_direction), 0.0);
}


vec3 GetSolarRadiance(const in AtmosphereParameters atmosphere)
{
    return atmosphere.solar_irradiance /
        (PI * atmosphere.sun_angular_radius * atmosphere.sun_angular_radius) * SUN_RADIANCE_TO_LUMINANCE * atmosphere_exposure;
}

vec3 GetSkyRadiance(
    const in AtmosphereParameters atmosphere, vec3 camera, vec3 view_ray, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadiance(atmosphere, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, view_ray, shadow_length, sun_direction, transmittance) * SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSkyRadianceToPoint(
    const in AtmosphereParameters atmosphere, vec3 camera, vec3 point, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadianceToPoint(atmosphere, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, point, shadow_length, sun_direction, transmittance) * SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSunAndSkyIrradiance(
   const in AtmosphereParameters atmosphere, vec3 p, vec3 normal, vec3 sun_direction,
   out vec3 sky_irradiance)
{
    vec3 sun_irradiance = ComputeSunAndSkyIrradiance(
        atmosphere, transmittance_texture, irradiance_texture, p, normal, sun_direction, sky_irradiance);
    sky_irradiance *= SKY_RADIANCE_TO_LUMINANCE;
    return sun_irradiance * SUN_RADIANCE_TO_LUMINANCE;
}

float GetSunVisibility(vec3 point, vec3 sun_direction)
{
    vec3 p = point - kSphereCenter;
    float p_dot_v = dot(p, sun_direction);
    float p_dot_p = dot(p, p);
    float ray_sphere_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
    float distance_to_intersection = -p_dot_v - sqrt(
        kSphereRadius * kSphereRadius - ray_sphere_center_squared_distance);
    if (distance_to_intersection > 0.0)
    {
        float ray_sphere_distance = kSphereRadius - sqrt(ray_sphere_center_squared_distance);
        float ray_sphere_angular_distance = -ray_sphere_distance / p_dot_v;
        return smoothstep(1.0, 0.0, ray_sphere_angular_distance / sun_size.x);
    }
    return 1.0;
}

float GetSkyVisibility(vec3 point)
{
  vec3 p = point - kSphereCenter;
  float p_dot_p = dot(p, p);
  return 1.0 + p.y / sqrt(p_dot_p) * kSphereRadius * kSphereRadius / p_dot_p;
}

void GetSphereShadowInOut(vec3 view_direction, vec3 sun_direction, out float d_in, out float d_out)
{
    vec3 pos = CAMERA_POSITION.xyz * atmosphere_ratio - kSphereCenter;
    float pos_dot_sun = dot(pos, sun_direction);
    float view_dot_sun = dot(view_direction, sun_direction);
    float k = sun_size.x;
    float l = 1.0 + k * k;
    float a = 1.0 - l * view_dot_sun * view_dot_sun;
    float b = dot(pos, view_direction) - l * pos_dot_sun * view_dot_sun - k * kSphereRadius * view_dot_sun;
    float c = dot(pos, pos) - l * pos_dot_sun * pos_dot_sun -
        2.0 * k * kSphereRadius * pos_dot_sun - kSphereRadius * kSphereRadius;
    float discriminant = b * b - a * c;
    if (discriminant > 0.0)
    {
        d_in = max(0.0, (-b - sqrt(discriminant)) / a);
        d_out = (-b + sqrt(discriminant)) / a;
        float d_base = -pos_dot_sun / view_dot_sun;
        float d_apex = -(pos_dot_sun + kSphereRadius / k) / view_dot_sun;
        if (view_dot_sun > 0.0)
        {
            d_in = max(d_in, d_apex);
            d_out = a > 0.0 ? min(d_out, d_base) : d_base;
        }
        else
        {
            d_in = a > 0.0 ? max(d_in, d_base) : d_base;
            d_out = min(d_out, d_apex);
        }
    }
    else
    {
        d_in = 0.0;
        d_out = 0.0;
    }
}

float GetSceneShadowLength(float scene_dist, vec3 view_direction, sampler2D texture_shadow)
{
    const float earth_radius = abs(earth_center.y);
    bool shadow_enter = false;
    bool do_exit = false;
    float scene_shadow_out = 0.0;
    float scene_shadow_in = 0.0;
    float shadow_length = 0.0;
    const int LOOP = 64;
    float d = min(NEAR_FAR.y * 0.01, scene_dist) / float(LOOP);
    float enter_count = 0.0;

    for(int i=0; i<LOOP; ++i)
    {
        float ray_dist = float(i) * d;
        vec3 world_pos = CAMERA_POSITION.xyz + view_direction * ray_dist;
        vec4 shadow_uv = SHADOW_MATRIX * vec4(world_pos, 1.0);
        shadow_uv.xyz /= shadow_uv.w;
        shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
        float shadow_depth = texture2D(texture_shadow, shadow_uv.xy, 0).x;

        if(shadow_uv.x < 0.0 || 1.0 < shadow_uv.x || shadow_uv.y < 0.0 || 1.0 < shadow_uv.y || scene_dist <= ray_dist)
        {
            do_exit = true;
        }
        else if(length(world_pos - earth_center) < earth_radius)
        {
            // Clip shdoaw by ground. Check if the ray enters the earth.
            do_exit = true;
        }
        else if(false == shadow_enter && shadow_depth <= shadow_uv.z)
        {
            // enter the shadow.
            shadow_enter = true;
            scene_shadow_in = dot(view_direction, world_pos);
        }
        else if(shadow_enter && shadow_uv.z < shadow_depth)
        {
            // It came out of the shadows or hit the surface of the object.
            scene_shadow_out = dot(view_direction, world_pos);
            shadow_length += scene_shadow_out - scene_shadow_in;

            // initialize
            shadow_enter = false;
            scene_shadow_in = 0.0;
            scene_shadow_out = 0.0;
            continue;
        }

        if(shadow_enter)
        {
            enter_count += 1.0;
        }

        if(do_exit || i == (LOOP-1))
        {
            if(shadow_enter)
            {
                // If there is already a shadow, set the position outside the shadow to the current position.
                scene_shadow_out = dot(view_direction, world_pos);
                shadow_length += scene_shadow_out - scene_shadow_in;
            }
            else
            {
                // Shadow not detected.
                scene_shadow_in = 0.0;
                scene_shadow_out = 0.0;
            }
            break;
        }
    }

    shadow_length = enter_count / float(LOOP);

    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 relative_camera_pos = CAMERA_POSITION.xyz * atmosphere_ratio;
    float lightshaft_fadein_hack = smoothstep(0.02, 0.04, dot(normalize(relative_camera_pos - earth_center), sun_direction));

    return max(0.0, shadow_length) * lightshaft_fadein_hack * 2.0;
}


void GetSceneRadiance(
    const in AtmosphereParameters atmosphere,
    float scene_linear_depth, vec3 eye_direction, vec3 normal,
    out vec3 sun_irradiance, out vec3 sky_irradiance, out vec3 in_scatter)
{
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 relative_camera_pos = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 relative_point = relative_camera_pos + eye_direction * scene_linear_depth * atmosphere_ratio;

    // Avoid brightening
    relative_camera_pos.y = max(0.0, relative_camera_pos.y);
    relative_point.y = max(0.0, relative_point.y);

    // 0.0 is for off screen light shaft
    float scene_shadow_length = 0.0;

    sun_irradiance = GetSunAndSkyIrradiance(
            atmosphere, relative_point.xyz - earth_center, normal, sun_direction, sky_irradiance);

    vec3 transmittance;
    in_scatter = GetSkyRadianceToPoint(atmosphere, relative_camera_pos - earth_center,
        relative_point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);

    sun_irradiance *= transmittance / PI;
    sky_irradiance *= transmittance / PI;
}


void GetSceneRadianceWithShadow(
    const in AtmosphereParameters atmosphere,
    float scene_linear_depth, vec3 eye_direction, vec3 normal, sampler2D texture_shadow,
    out vec3 sun_irradiance, out vec3 sky_irradiance, out vec3 in_scatter, out float scene_shadow_length)
{
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 relative_camera_pos = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 relative_point = relative_camera_pos + eye_direction * scene_linear_depth * atmosphere_ratio;

    // Avoid brightening
    relative_camera_pos.y = max(0.0, relative_camera_pos.y);
    relative_point.y = max(0.0, relative_point.y);

    scene_shadow_length = GetSceneShadowLength(scene_linear_depth, eye_direction, texture_shadow);

    sun_irradiance = GetSunAndSkyIrradiance(
            atmosphere, relative_point.xyz - earth_center, normal, sun_direction, sky_irradiance);

    vec3 transmittance;
    in_scatter = GetSkyRadianceToPoint(atmosphere, relative_camera_pos - earth_center,
        relative_point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);

    sun_irradiance *= transmittance / PI;
    sky_irradiance *= transmittance / PI;
}


void GetCloudRadiance(
    const in AtmosphereParameters atmosphere,
    float dist, vec3 eye_direction, float scene_shadow_length,
    out vec3 sun_irradiance, out vec3 sky_irradiance, out vec3 inscatter)
{
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 camera_pos = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 point = camera_pos + eye_direction.xyz * max(NEAR_FAR.x, dist) * atmosphere_ratio;

    sun_irradiance = GetSunAndSkyIrradiance(
        atmosphere, point.xyz - earth_center, sun_direction, sun_direction, sky_irradiance);

    vec3 transmittance;
    inscatter = GetSkyRadianceToPoint(atmosphere, camera_pos - earth_center,
        point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);

    sun_irradiance = max(vec3(0.0), sun_irradiance);
    sky_irradiance = max(vec3(0.0), sky_irradiance);
    transmittance = max(vec3(0.0), transmittance);
    inscatter = max(vec3(0.0), inscatter);

    sun_irradiance *= transmittance / PI;
    sky_irradiance *= transmittance / PI;
}