#include "scene_constants.glsl"
#include "utility.glsl"


uniform bool enable_vector_field;
uniform sampler3D texture_vector_field;
uniform float vector_field_strength;
uniform vec3 vector_field_offset;
uniform vec3 vector_field_radius;


#ifdef COMPUTE_SHADER
layout(local_size_x=WORK_GROUP_SIZE, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer particle_buffer { ParticleData particle_datas[]; };
layout(std430, binding=1) buffer index_range_buffer { ParticleIndexRange particle_index_range; };


void update_sequence(inout ParticleData particle_data, float life_ratio)
{
    const int particle_total_cell_count = PARTICLE_CELL_COUNT[0] * PARTICLE_CELL_COUNT[1];

    if(1 < particle_total_cell_count && 0.0 < PARTICLE_PLAY_SPEED)
    {
        float ratio = life_ratio * PARTICLE_PLAY_SPEED;
        ratio = float(particle_total_cell_count - 1) * (ratio - floor(ratio));

        int index = int(ratio);
        int next_index = min(index + 1, particle_total_cell_count - 1);

        particle_data.sequence_ratio = ratio - float(index);

        if(next_index == particle_data.next_sequence_index)
        {
            return;
        }

        particle_data.sequence_index = particle_data.next_sequence_index;
        particle_data.sequence_uv = particle_data.next_sequence_uv;
        particle_data.next_sequence_index = next_index;
        particle_data.next_sequence_uv.x = mod(next_index, PARTICLE_CELL_COUNT.x) / float(PARTICLE_CELL_COUNT.x);
        particle_data.next_sequence_uv.y = float(PARTICLE_CELL_COUNT.y - 1 - int(floor(next_index / PARTICLE_CELL_COUNT.x))) / float(PARTICLE_CELL_COUNT.y);
    }
}


void update_local_matrix(inout ParticleData particle_data)
{
    mat4 rotation_matrix = mat4(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0);

    mat4 scale_matrix = mat4(
        particle_data.transform_scale.x, 0.0, 0.0, 0.0,
        0.0, particle_data.transform_scale.y, 0.0, 0.0,
        0.0, 0.0, particle_data.transform_scale.z, 0.0,
        0.0, 0.0, 0.0, 1.0);

    float ch = 1.0;
    float sh = 0.0;
    float ca = 1.0;
    float sa = 0.0;
    float cb = 1.0;
    float sb = 0.0;
    bool has_rotation = false;

    if(0.0 != particle_data.transform_rotation.x)
    {
        cb = cos(particle_data.transform_rotation.x);
        sb = sin(particle_data.transform_rotation.x);
        has_rotation = true;
    }

    if(0.0 != particle_data.transform_rotation.y)
    {
        ch = cos(particle_data.transform_rotation.y);
        sh = sin(particle_data.transform_rotation.y);
        has_rotation = true;
    }

    if(0.0 != particle_data.transform_rotation.z)
    {
        ca = cos(particle_data.transform_rotation.z);
        sa = sin(particle_data.transform_rotation.z);
        has_rotation = true;
    }

    if(has_rotation)
    {
        rotation_matrix[0] = vec4(ch*ca, sa, -sh*ca, 0.0);
        rotation_matrix[1] = vec4(sh*sb - ch*sa*cb, ca*cb, sh*sa*cb + ch*sb, 0.0);
        rotation_matrix[2] = vec4(ch*sa*sb + sh*cb, -ca*sb, -sh*sa*sb + ch*cb, 0.0);
        particle_data.local_matrix = rotation_matrix * scale_matrix;
    }
    else
    {
        particle_data.local_matrix = scale_matrix;
    }

    
    particle_data.local_matrix[3].xyz = particle_data.transform_position.xyz;
}


void update(inout ParticleData particle_data, uint id)
{
    if(PARTICLE_STATE_DELAY == particle_data.state)
    {
        particle_data.delay -= DELTA_TIME;
        if(particle_data.delay <= 0.0)
        {
            particle_data.elapsed_time = abs(particle_data.delay);
            particle_data.delay = 0.0;
            particle_data.state = PARTICLE_STATE_ALIVE;
        }
    }

    // Update
    if(PARTICLE_STATE_ALIVE == particle_data.state)
    {
        particle_data.elapsed_time += DELTA_TIME;

        if(particle_data.elapsed_time <= particle_data.life_time)
        {
            float life_ratio = 0.0;
            float elapsed_time = particle_data.elapsed_time;
            float life_time = particle_data.life_time;

            if(0.0 < particle_data.life_time)
            {
                life_ratio = clamp(elapsed_time / particle_data.life_time, 0.0, 1.0);
            }

            // update sequence
            update_sequence(particle_data, life_ratio);

            particle_data.velocity_position += particle_data.force * DELTA_TIME;

            if(PARTICLE_ENABLE_VECTOR_FIELD)
            {
                vec3 uvw = (PARTICLE_VECTOR_FIELD_INV_MATRIX * vec4(particle_data.transform_position, 1.0)).xyz;
                vec3 force = texture3D(texture_vector_field, uvw - vec3(0.5)).xyz;
                force = (PARTICLE_VECTOR_FIELD_MATRIX * vec4(force, 1.0)).xyz;
                particle_data.velocity_position = mix(particle_data.velocity_position, force, PARTICLE_VECTOR_FIELD_TIGHTNESS);
                particle_data.velocity_position += force * PARTICLE_VECTOR_FIELD_STRENGTH * DELTA_TIME;
            }

            particle_data.transform_position += particle_data.velocity_position * DELTA_TIME;
            particle_data.transform_rotation += particle_data.velocity_rotation * DELTA_TIME;
            particle_data.transform_scale += particle_data.velocity_scale * DELTA_TIME;

            // update transform
            update_local_matrix(particle_data);

            // update opacity
            particle_data.opacity = PARTICLE_OPACITY;

            float left_elapsed_time = life_time - elapsed_time;

            if(0.0 < PARTICLE_FADE_IN && elapsed_time < PARTICLE_FADE_IN)
            {
                particle_data.opacity *= elapsed_time / PARTICLE_FADE_IN;
            }

            if(0.0 < PARTICLE_FADE_OUT && left_elapsed_time < PARTICLE_FADE_OUT)
            {
                particle_data.opacity *= left_elapsed_time / PARTICLE_FADE_OUT;
            }
        }
        else
        {
            particle_data.state = PARTICLE_STATE_DEAD;
        }
    }
}


void main()
{
    if(gl_GlobalInvocationID.x < particle_index_range.instance_count)
    {
        uint id = (particle_index_range.begin_index + gl_GlobalInvocationID.x) % PARTICLE_MAX_COUNT;

        update(particle_datas[id], id);

        // update the dead index and update index.
        if(PARTICLE_STATE_DEAD == particle_datas[id].state)
        {
            atomicAdd(particle_index_range.destroy_count, 1);
        }
    }
}
#endif
