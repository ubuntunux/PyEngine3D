float4 CalcGerstnerWaveInfo(float depth, float frequency, float speed)
{
    speed *= fTime * frequency * 0.05f;

    float wave = depth * frequency - speed;

    float term = 60.0f;
    float linear_wave_gradient = saturate(1.0f - frac(abs(wave / term)));
    float wave_gradient = pow(linear_wave_gradient, sqrt(linear_wave_gradient) * 12.0f + 1.0);

    float s, c;
    sincos(wave_gradient * TWO_PI + M_PI, s, c);

    float wave_peak = c * 0.5 + 0.5;

    return float4(linear_wave_gradient, wave_gradient, wave_peak, s);
}

void GerstnerMainWave(float2 dir, float depth, float frequency, float speed, float intensity, float noise, inout float3 wave_offset, inout float3 wave_normal)
{
    intensity *= (0.5f + noise) * depth;

    float4 wave_infos = CalcGerstnerWaveInfo(depth, frequency, speed);
    float linear_wave_gradient = wave_infos.x;
    float wave_gradient = wave_infos.y;
    float wave_peak = wave_infos.z;
    float s = wave_infos.w;

    // smooth edge
    const float thickness = 1.2f;
    wave_gradient = 1.0 - wave_gradient;
    wave_gradient = saturate(wave_gradient * thickness) - saturate((wave_gradient * thickness - 1.0f) / (thickness - 1.0f));
    linear_wave_gradient = saturate(linear_wave_gradient * thickness) - saturate((linear_wave_gradient * thickness - 1.0f) / (thickness - 1.0f));

    // output
    wave_offset.y = intensity * wave_peak * 2.0;
    wave_offset.y += saturate(1.0 - depth) * (linear_wave_gradient * 2.0 - 1.0) * 100.0;
    wave_offset.xz = s * dir * intensity;
    wave_normal = safe_normalize(lerp(float3(0.0f, 1.0f, 0.0f), float3(wave_offset.x, 100.0f / intensity, wave_offset.z), (1.0f - wave_peak) * wave_gradient * depth));
}

struct FFTOCEAN_VS_OUTPUT
{
    float4 proj_pos : PA_VS_OUTPUT;
    float3 relative_pos : TEXCOORD0;
    float3 vertex_normal : TEXCOORD1;
    float4 uvs : TEXCOORD2;
    float2 pos_in_sector : TEXCOORD3;
    float4 depth_distance : TEXCOORD4;
    float3 vecExtinction : TEXCOORD5;
    float3 vecInscatter : TEXCOORD6;
    float2 vecAO : TEXCOORD7;
    float3 gerstner_wave_infos : TEXCOORD8;
    float3 wave_offset : TEXCOORD9;
    float vertex_noise : TEXCOORD10;
    float4 vertex_flow : TEXCOORD11;
    float3 vecLSun : TEXCOORD12;
    float screen_fade : TEXCOORD13;
};

FFTOCEAN_VS_OUTPUT FFTOceanVS(float3 iPos : POSITION, uniform int fft_quality, uniform bool calcHeightOnly=false)
{
    FFTOCEAN_VS_OUTPUT output = (FFTOCEAN_VS_OUTPUT)0;

    // Note : sorting 문제 때문에 좌우상하를 뒤짚어주어야 한다!
    float3 screen_pos = (1.0f - iPos) * 2.0f - 1.0f;
    float3 vertex_scale = float3(1.5f, 1.5f, 1.0f);
    float4 vertex_pos = float4(screen_pos * vertex_scale, 1.0f);

    float3 world_pos = oceanPos(vertex_pos);
    float3 relative_pos = world_pos - vecViewPosition.xyz;
    float depth = length(relative_pos);

    float screen_fade = 1.0f - saturate(ceil(max(abs(screen_pos.x), abs(screen_pos.y)) - 0.999f));
    float fGiantWave = 0.0f;

    if (calcHeightOnly)
    {
        world_pos.xz = iPos.xz;
        world_pos.y = fSeaHeightConst;
    }

    [branch]
    if (isUnderWater)
    {
        world_pos.y += 20.0f;
    }
    else
    {
        fGiantWave = (sin(world_pos.x / 1500.0f + fTime * 2.2f) + 1.0f) * (sin(world_pos.z / 5000.0f + fTime) + 1.0f) * 150.0f;
        fGiantWave += (sin(world_pos.x / 1100.0f + fTime * -4.9f) + 1.0f) * (sin(world_pos.z / 3000.0f + fTime * 1.0f) + 1.0f) * 100.0f;
        fGiantWave *= fGiantWaveScale;
        world_pos.y += fGiantWave;
        world_pos.y -= 40.0f;
    }

    relative_pos = world_pos - vecViewPosition.xyz;
    depth = length(relative_pos);

    float2 plane_uv = world_pos.xz;
    float dist_xz = length(relative_pos.xz);
    float4 depth_distance = GetFlowDepthAndDistance(world_pos.xz); //xy:texture flow, z:render (upperTerrain), w:depth
    float3 eye_dir = relative_pos / depth;

    // interpolate flow direction
    float2 fmodePos = abs(fmod(world_pos.xz - vecSectorConstInfo.xy, vecFlowMapPixelSize.xy));
    float2 lerpValue = saturate(fmodePos / vecFlowMapPixelSize.xy);
    lerpValue = 1.0f - lerpValue;
    float4 flowO = GetFlowDirection(world_pos.xz);
    float4 flowR = GetFlowDirection(float2(world_pos.x + vecFlowMapPixelSize.x, world_pos.z));
    float4 flowT = GetFlowDirection(float2(world_pos.x, world_pos.z + vecFlowMapPixelSize.y));
    float4 flowRT = GetFlowDirection(float2(world_pos.x + vecFlowMapPixelSize.x, world_pos.z + vecFlowMapPixelSize.y));

    // Note : world좌표와 uv좌표가 서로 반대방향임을 주의할것!!
    flowO = lerp(flowR, flowO, lerpValue.x);
    flowT = lerp(flowRT, flowT, lerpValue.x);
    flowO = lerp(flowT, flowO, lerpValue.y);
    flowO.xy = normalize(flowO.xy);

    output.vertex_flow = flowO;

    float3 wave_offset = float3(0.0f, 0.0f, 0.0f);
    float2 fft_uv = plane_uv;
    [branch]
    if (depth_distance.z > 0.0f && dist_xz < 500000.0f)
    {
        float2 ux = oceanPos(vertex_pos + float4(gridCellSize.x, 0.0f, 0.0f, 0.0f)).xz;
        float2 uy = oceanPos(vertex_pos + float4(0.0f, gridCellSize.y, 0.0f, 0.0f)).xz;

        /*float radO = atan2(flowO.y, flowO.x);
        float radR = atan2(flowR.y, flowR.x);
        float radT = atan2(flowT.y, flowT.x);
        float radRT = atan2(flowRT.y, flowRT.x);*/

        // NOTE!!! : 파도의 방향성 제거.. 제대로 rotation하려면 회전된 fft와 원래의 fft를 모두구해서 섞어야 하는데 비용이 너무크다...
        // 이거 사용하려면 아랫쪽에서 inverse rotation도 적용해주어야 한다
        //float s, c;
        //s = flowO.y;
        //c = flowO.x;
        //{
        // // sincos(radO, s, c);
        // fft_uv = c * fft_uv + s * float2(-fft_uv.y, fft_uv.x);
        // ux = c * ux + s * float2(-ux.y, ux.x);
        // uy = c * uy + s * float2(-uy.y, uy.x);
        //}

        float2 dux = abs(ux - fft_uv) * 2.0;
        float2 duy = abs(uy - fft_uv) * 2.0;

        float wave_noise = PAGetTexelLod(texNoise, samNoise, float4(fTime * simulation_wind * -0.01f + world_pos.xz * 0.000025f, 0.0f, 0.0f)).x;
        output.vertex_noise = (wave_noise * 2.0f - 1.0f) * 0.2f;

        wave_offset.y += PAGetTexelGrad(texture_fft0, sampler_fft0, fft_uv / GRID_SIZES.x, dux / GRID_SIZES.x, duy / GRID_SIZES.x).x;
        wave_offset.y += PAGetTexelGrad(texture_fft0, sampler_fft0, fft_uv / GRID_SIZES.y, dux / GRID_SIZES.y, duy / GRID_SIZES.y).y;
        wave_offset.y += PAGetTexelGrad(texture_fft0, sampler_fft0, fft_uv / GRID_SIZES.z, dux / GRID_SIZES.z, duy / GRID_SIZES.z).z;
        wave_offset.y += PAGetTexelGrad(texture_fft0, sampler_fft0, fft_uv / GRID_SIZES.w, dux / GRID_SIZES.w, duy / GRID_SIZES.w).w;

        if (FFT_QUALITY_HIGH == fft_quality)
        {
            wave_offset.xz += PAGetTexelGrad(texture_fft3, sampler_fft3, fft_uv / GRID_SIZES.x, dux / GRID_SIZES.x, duy / GRID_SIZES.x).xy;
            wave_offset.xz += PAGetTexelGrad(texture_fft3, sampler_fft3, fft_uv / GRID_SIZES.y, dux / GRID_SIZES.y, duy / GRID_SIZES.y).zw;
        }

        wave_offset.xz += PAGetTexelGrad(texture_fft4, sampler_fft4, fft_uv / GRID_SIZES.z, dux / GRID_SIZES.z, duy / GRID_SIZES.z).xy;
        wave_offset.xz += PAGetTexelGrad(texture_fft4, sampler_fft4, fft_uv / GRID_SIZES.w, dux / GRID_SIZES.w, duy / GRID_SIZES.w).zw;

        // inverse rotation
        //{
        // // regular : sincos(-radO, s, c);
        // c = c;
        // s = -s;
        // wave_offset.xz = c * wave_offset.xz + s * float2(-wave_offset.z, wave_offset.x);
        //}

        output.wave_offset = wave_offset;
        output.wave_offset.y += saturate(fGiantWave * 0.001f);

        float wave_amplitude = saturate((1.0f - depth_distance.w) * 2.5f);
        wave_amplitude *= wave_amplitude * amplitude * (wave_noise + 0.3f);

        // Apply FFT Wave
        world_pos += wave_offset * wave_amplitude;

        // VertexNormal
        float3 vertex_normal = safe_normalize(float3(-wave_offset.x, 1.0f + wave_offset.y, -wave_offset.z));

        // GerstnerWave - Main wave
        {
            const float intensity = wave_amplitude * 0.2f;
            const float frequency = 170.0f;
            const float speed = simulation_wind * 0.7f;

            output.gerstner_wave_infos = float3(intensity, frequency, speed);

            float3 main_wave_offset;
            float3 main_wave_normal;
            GerstnerMainWave(flowO.xy, depth_distance.w, frequency, speed, intensity, wave_noise, main_wave_offset, main_wave_normal);

            world_pos += main_wave_offset * depth_distance.w;
            vertex_normal.xz += main_wave_normal.xz * 0.3f;
        }

        float wave_intensity = wave_amplitude * 0.01f;

        vertex_normal = safe_normalize(lerp(float3(0.0, 1.0, 0.0), vertex_normal, saturate(wave_intensity)));
        output.vertex_normal = vertex_normal;
    }

    //float4 screenTex = float4((proj_pos.xy / proj_pos.w) * 0.5f + 0.5f, 0.0f, 0.0f);
    //screenTex.y = 1.0f - screenTex.y;
    float4 proj_pos = mul(float4(world_pos, 1.0f), matViewProjection);

    float t = (proj_pos.y / proj_pos.w);

    if (dist_xz < 50000.0f)
    {
        // 가장자리 버텍스 삐져나가지 않게 맞주기
        proj_pos.xy = lerp(vertex_pos.xy * proj_pos.w, proj_pos.xy, screen_fade);
    }

    output.screen_fade = screen_fade;
    output.uvs.xy= plane_uv;
    output.uvs.zw = fft_uv;
    output.depth_distance = depth_distance;
    output.relative_pos = world_pos - vecViewPosition.xyz;
    output.proj_pos = proj_pos;

    output.pos_in_sector = world_pos.xz - vecSectorConstInfo.xy;
    output.pos_in_sector.xy = output.pos_in_sector.xy / vecSectorConstInfo.zw;
    output.pos_in_sector.y = 1.0f - output.pos_in_sector.y;

    // 바다 clip 관련 수정시, 폐철광산 옵션별 테스트 필수, farTerrain 으로 덮을 수 있는 영역에 따라 scattering
    [branch] if (depth_distance.z > 0.05f || depth > 150000.0f)
    {
        float3 vecLSun, vecAmbientColor, vecAmbientOcclusionColor;
        vecLSun = 1.0f;
        vecAmbientColor = 1.0f;

        float fExtinction = 1.0f;
        GetScatter(vecLSun, vecAmbientColor, vecAmbientOcclusionColor, output.vertex_normal, fExtinction, world_pos, vecViewPosition, output.vecInscatter, vecSunDirection, vecMoonDirection, 1.0f);
        output.vecExtinction.xyz = fExtinction;
        output.vecLSun = vecLSun;
    }
    else
    {
        // clip
        output.proj_pos.w = -1;
        //output.relative_pos.w = -1;
    }

    // reflectAO
    float reflectAO = 1.0f;
    {
        reflectAO = 0.0f;
        const int nLoop = 5 - saturate(depth / 3000.0f) * 3;

        [loop]
        for (int i = 0; i < nLoop; i++)
        {
            const bool useDynamic = true;
            const bool bCloudShadow = false;
            const float farFade = 0.25f;
            reflectAO += GetOutDoorShadow3(float4(world_pos + eye_dir * i * 15.0f, 1.0f), useDynamic, bCloudShadow, farFade);
        }

        reflectAO = min(reflectAO / (float)nLoop, 0.96f);
        {
            const bool useDynamic = false;
            const bool bCloudShadow = true;
            getDynamicShadow(reflectAO, float4(world_pos, 1), useDynamic, bCloudShadow);
        }
        reflectAO = saturate(reflectAO * 0.75f + 0.25f);
    }

    // longtermAO
    float fLongtermAO = 1.0f;
    // 그다지 필요없을듯.. 사용할꺼면 pixel shader쪽에도 주석처리 해제하시오.
    /*float4 refracted_screenTex = float4((proj_pos.xy / proj_pos.w) * 0.5f + 0.5f, 0.0f, 0.0f);
    refracted_screenTex.y = 1.0f - refracted_screenTex.y;
    refracted_screenTex.xy += output.vertex_normal.xz * 0.2f;

    float refracted_scene_depth = GetViewDepthLod(PASamplerParamToFunc(texDepth, samDepth), refracted_screenTex);
    float depth_diff = max(0.0f, refracted_scene_depth - depth);

    if (vecViewPosition.y > fSeaHeightConst)
    {
        fLongtermAO = saturate(PAGetTexelLod(texLongtermMinus, samSceneScatter, refracted_screenTex).w);
        fLongtermAO = pow(fLongtermAO, 1.0f);
        fLongtermAO = saturate(fLongtermAO + pow(depth_diff / 3000.0f, 2));
    }*/

    output.vecAO.x = reflectAO;
    output.vecAO.y = fLongtermAO;

    return output;
}


float4 FFTOceanPS(FFTOCEAN_VS_OUTPUT input, half4 Tex : PA_PS_VPOS, uniform int fft_quality) : PA_PS_OUTPUT0
{
    if (input.proj_pos.w < 0)
    {
        discard;
    }

    float2 uv = input.uvs.xy * 0.0015f;
    float2 fft_uv = input.uvs.zw;
    float2 screenTex = getScreenTex(Tex, invScreenSize.xy, invScreenSize.zw);

    float3 relative_pos = input.relative_pos.xyz;
    float3 world_pos = relative_pos + vecViewPosition.xyz;
    float3 vertex_normal = input.vertex_normal;
    float depth = length(relative_pos);
    float3 V = -relative_pos / depth;
    float3 L = vecLightDirection;

    float reflectAO = input.vecAO.x;
    // 그다지 필요없을듯.. 사용할꺼면 vertex shader쪽에도 주석처리 해제하시오.
    // float fLongtermAO = input.vecAO.y;
    float3 vecInscatter = input.vecInscatter.xyz;
    float3 vecExtinction = input.vecExtinction.xyz;
    float vertex_noise = input.vertex_noise;
    float normalized_vertex_noise = saturate(input.vertex_noise * 0.5f + 0.55f);

    float scene_depth = GetViewDepth(PASamplerParamToFunc(texDepth, samDepth), screenTex.xy);

    // fix scene_depth
    float3 groundPos = -V * scene_depth;
    groundPos.xz = lerp(relative_pos.xz, groundPos.xz, abs(V.y));
    scene_depth = length(groundPos.xyz);

    // NOTE : 물의 방향성을 없애기 위해 vertex shader에서와 반대방향으로 흐르게 하자
    float2 slopes0 = (FFT_QUALITY_HIGH == fft_quality) ? PAGetTexelLod(texture_fft1, sampler_fft1, float4(-fft_uv / GRID_SIZES.x, 0.0f, 0.0f)).xy : float2(0.0f, 0.0f);
    float2 slopes1 = (FFT_QUALITY_HIGH == fft_quality) ? PAGetTexelLod(texture_fft1, sampler_fft1, float4(-fft_uv / GRID_SIZES.y, 0.0f, 0.0f)).zw : float2(0.0f, 0.0f);
    float2 slopes2 = PAGetTexelLod(texture_fft2, sampler_fft2, float4(-fft_uv / GRID_SIZES.z, 0.0f, 0.0f)).xy;
    float2 slopes3 = PAGetTexelLod(texture_fft2, sampler_fft2, float4(-fft_uv / GRID_SIZES.w, 0.0f, 0.0f)).zw;

    float3 detail_normal;
    detail_normal.xz = -(slopes0 + slopes1 + slopes2 + slopes3);
    detail_normal.y = 1.0f;
    detail_normal = normalize(detail_normal);

    float3 N = float3(0.0f, 0.0f, 0.0f);
    //N.xz -= -(slopes0 + slopes1 * saturate(1.0f - depth * 0.00002f) + slopes2 * saturate(1.0f - depth * 0.0001f) + slopes3 * saturate(1.0f - depth * 0.0005f));
    N.xz = -(slopes0 + slopes1 + slopes2 * 0.9f + slopes3 * saturate(1.0f - depth * 0.0005f) * 0.7f);
    N.y = 1.0f;
    N = normalize(N + vertex_normal * 0.5f);

    float NdotV = dot(N, V);
    float NdotL = dot(N, L);
    float3 R = reflect(-V, N);
    R.y = abs(R.y);

    // fresnel
    const float fresnelPower = 6.0f;
    const float fresnelBias = 0.2f;
    float fresnel = saturate(fresnelBias + (1.0 - fresnelBias) * pow(saturate(1.0f - saturate(NdotV)), fresnelPower));

    // refract
    float2 reflected_screen_uv = screenTex + N.xz * 0.1f;
    float refractedSceneDepth = GetViewDepth(PASamplerParamToFunc(texDepth, samDepth), reflected_screen_uv);
    float refractedSceneDepthOrigin = refractedSceneDepth;

    // fix refractedSceneDepth
    groundPos = -V * refractedSceneDepth;
    groundPos.xz = lerp(relative_pos.xz, groundPos.xz, abs(V.y));
    refractedSceneDepth = length(groundPos.xyz);

    float depth_diff = max(0.0f, max(scene_depth, refractedSceneDepth) - depth);

    float screen_fade = pow(input.screen_fade, 100.0f);

    float opacity = sqrt(saturate(depth_diff * 0.0006f)) * screen_fade;
    float invOpacity = 1.0f - opacity;
    float coast_line_edge = saturate(1.0f - depth_diff * 0.01f);

    // apply water mask
    if (depth_diff < 500.f)
    {
        opacity *= pow(1.0f - PAGetTexel(texWaterMask, samWaterMask, screenTex).r, 2.0f);
    }

    float4 outColor = 1.0f;
    float aboveWater = 1.0f;

    // groud pos
    groundPos = world_pos - V * depth_diff + float3(N.x, 0.0f, N.z) * 200.0f;

    // Water Base Color
    float4 vecSeaNearColorConst = float4(0.61f, 0.66f, 0.66f, 1.0f);
    float4 vecSeaBaseColorConst = float4(0.5f, 0.75f, 0.78f, 1.0f);
    float4 vecSeaFarColorConst = float4(0.25f, 0.36f, 0.39f, 1.0f);
    float3 waterColor;
    {
        waterColor = lerp(vecSeaBaseColorConst.xyz, vecSeaFarColorConst.xyz, saturate((depth_diff - 600.0f) * 0.0002f));
        waterColor = lerp(vecSeaNearColorConst.xyz, waterColor, saturate(depth_diff * 0.0001f)) * hdrEncodeMulti;
    }

    // 물위의 오브젝트가 수면위에 그려지는것 방지
    float3 underWaterDiffuse = PAGetTexelLod(texDiffuse, samDiffuse, float4((refractedSceneDepth <= depth) ? screenTex : reflected_screen_uv, 0.0f, 0.0f)).xyz;
    underWaterDiffuse = pow(underWaterDiffuse, 2.2f);
    {
        // Under Water Caustic
        float under_water_shadow = PAGetTexel(tex_shadowMap, sam_shadowMap, screenTex).r * aboveWater;
        const float chromaSeperation = (world_pos - groundPos).y * 0.00004f * sin(fTime * 3.5f);
        float2 caustic_uv = (groundPos + L * depth_diff).xz * 0.0025f;

        float3 causticColor;
        causticColor.r = PAGetTexel(texCaustic, samCaustic, caustic_uv + float2(0.0f, chromaSeperation) + vertex_noise);
        causticColor.g = PAGetTexel(texCaustic, samCaustic, caustic_uv + float2(chromaSeperation, 0.0f) + vertex_noise);
        causticColor.b = PAGetTexel(texCaustic, samCaustic, caustic_uv - float2(chromaSeperation, chromaSeperation) + vertex_noise);
        causticColor *= reflectAO * vecExtinction * normalized_vertex_noise * 1.5f * screen_fade;

        // apply caustic
        underWaterDiffuse += causticColor * input.vecLSun * max(0.5f, under_water_shadow) * (1.0f - coast_line_edge);

        float3 fog_color = vecSeaFarColorConst * vecSeaFarColorConst;
        float fog_ratio = saturate(refractedSceneDepthOrigin * 0.00005f);
        fog_color = lerp(underWaterDiffuse, fog_color, fog_ratio * fog_ratio) * 0.3f;

        underWaterDiffuse = lerp(underWaterDiffuse, waterColor * underWaterDiffuse, opacity) * invOpacity;
        underWaterDiffuse = lerp(fog_color, underWaterDiffuse, screen_fade);
    }

    // Reflection
    float3 reflectColor = PAGetTexelCube(texEnv, samEnv, R).xyz;

    #ifndef __XBOX_ONE
    // NOTE : XBOX에서는 SSR을 끈다
    [branch] if (0.0f < aboveWater)
    {
        float3 smooth_normal = lerp(N, float3(0.0f, 1.0f, 0.0f), 0.5f);

        float4 SSReflectionColor = getSSReflectionUltra(
        PASamplerParamToFunc(texDepth, samDepth), true, PASamplerParamToFunc(texDiffuse, samDiffuse),
        matViewOrigin, matProjection, relative_pos, smooth_normal, 0.0f, screenTex, Tex.xy);

        reflectColor = lerp(reflectColor, SSReflectionColor.xyz, SSReflectionColor.w);
    }
    #endif

    reflectColor = pow(reflectColor, 2.2f);

    // Specular
    const float waterSpecular = 0.02f;
    const float waterGloss = 0.97f;
    float specular = max(0.0f, calcSpecularGGXSmithFresnel0(detail_normal, V, L, saturate(dot(detail_normal, V)), waterSpecular, waterGloss)) * 10.0f;

    // Foam
    float3 foam;
    float transmission = 0.0f;
    {
        //float2 vecFlowDir = PAGetTexel(texSeaFlow, samSeaFlowLinear, input.pos_in_sector).xy * 2.0f - 1.0f;
        float2 vecFlowDir = input.vertex_flow.xy;

        float depth_fade = input.depth_distance.w * input.depth_distance.w;
        const float frequency = input.gerstner_wave_infos.y;
        const float speed = input.gerstner_wave_infos.z;

        float wave_detail_noise = (PAGetTexel(texNoise, samNoise, uv * 7.7f).x * 2.0f - 1.0f) * 0.01f * invOpacity;

        float4 wave_infos = CalcGerstnerWaveInfo(input.depth_distance.w + wave_detail_noise + vertex_noise * 0.02f, frequency, speed);

        float long_wave_gradient = pow(wave_infos.x, 8.0f);

        float wave_peak = pow((input.wave_offset.y + (1.0f - N.y)) * 0.25f + 0.5f, 3.0f);

        float white_cap = wave_peak * wave_peak * simulation_wind;

        // transmission
        transmission = max(white_cap * 0.7f, invOpacity * long_wave_gradient * saturate((1.0f - long_wave_gradient) * 8.0f) * (1.0f - saturate(depth * 0.0001f)))
        * normalized_vertex_noise * 30.0f;

        float coast_line = saturate(1.0f - depth_diff * 0.004f);
        coast_line = coast_line * coast_line * invOpacity * 1.2f;

        float wave_shift = long_wave_gradient * input.depth_distance.w * 3.0f;

        const float foam_speed = 4.0f;
        float t1 = frac(fTime * simulation_wind * 0.02f);
        float t2 = t1 + (0.5f <= t1 ? -0.5f : 0.5f);
        // texture_waterFoam, sampler_waterFoam
        float foam1 = PAGetTexel(texWaterFoam, samWaterFoam, uv + vecFlowDir * t1 * (foam_speed + wave_shift + vertex_noise)).z;
        float foam2 = PAGetTexel(texWaterFoam, samWaterFoam, uv + vecFlowDir * t2 * (foam_speed + wave_shift + vertex_noise)).z;
        foam1 = lerp(foam1, foam2, abs(t1 * 2.0 - 1.0));

        float wave_gradient = pow(wave_infos.x, lerp(10.0f, 0.1f, depth_fade));
        float foam_amount = saturate(((coast_line + wave_gradient) * invOpacity + white_cap) * normalized_vertex_noise);

        float sharpen = lerp(0.45f, 0.15f, saturate(foam_amount + white_cap));
        foam1 = saturate((foam1 - sharpen) / (1.0f - sharpen) * 3.0f) * foam_amount;
        foam = foam1 * waterColor * 80.0f;
    }

    float foam_lum = dot(float3(0.3f, 0.59f, 0.11f), foam);
    specular *= saturate(1.0f - foam_lum * 2.0f);
    fresnel *= saturate(1.0f - foam_lum * 2.0f);

    // 주의!! : 현재는 일몰, 일출일때 cube맵이 갱신되지 않기 때문에 태양색을 섞었지만 realtime cube을 사용하게 되면 이것 필요없음!!
    outColor.xyz = ((lerp(waterColor, reflectColor, fresnel) + foam) * saturate(NdotL) + specular) * input.vecLSun.xyz * 2.0f;
    outColor.xyz += transmission * waterColor * input.vecLSun.xyz;
    outColor.xyz *= reflectAO * vecExtinction;
    outColor.xyz += vecInscatter * 3.0f * hdrEncodeMulti;
    // outColor.xyz = clamp(outColor.xyz, 0.0f, 20.0f);

    // output
    opacity = saturate(depth_diff * 0.01f) * saturate(opacity + (foam_lum + specular + fresnel + transmission * 0.01f));
    outColor.xyz = lerp(underWaterDiffuse.xyz, outColor.xyz, opacity * screen_fade);
    outColor.xyz = pow(outColor.xyz , 1.0f/2.2f);

    return outColor;
}