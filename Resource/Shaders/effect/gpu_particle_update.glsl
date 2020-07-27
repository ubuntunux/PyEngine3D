#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect/common.glsl"


uniform bool enable_vector_field;
uniform float vector_field_strength;
uniform vec3 vector_field_offset;
uniform vec3 vector_field_radius;
uniform sampler3D texture_vector_field;
uniform sampler2D texture_depth;
uniform sampler2D texture_normal;


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


void update_local_matrix(inout ParticleData particle_data, vec3 normalized_world_velocity, float world_velocity_length)
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

    // apply alignment
    if(ALIGN_MODE_BILLBOARD == PARTICLE_ALIGN_MODE)
    {
        mat4 world_matrix = INV_VIEW_ORIGIN;
        world_matrix[3] = vec4(0.0, 0.0, 0.0, 1.0);
        particle_data.local_matrix = world_matrix * particle_data.local_matrix;
    }
    else if(ALIGN_MODE_VELOCITY_ALIGN == PARTICLE_ALIGN_MODE)
    {
        if(0.0 < world_velocity_length)
        {
            mat4 world_matrix;
            world_matrix[0].xyz = cross(normalized_world_velocity.xyz, normalize(particle_data.relative_position));
            world_matrix[1].xyz = normalized_world_velocity.xyz * (1.0 + world_velocity_length * PARTICLE_VELOCITY_STRETCH * 0.1);
            world_matrix[2].xyz = cross(world_matrix[0].xyz, normalized_world_velocity.xyz);
            world_matrix[3] = vec4(0.0, 0.0, 0.0, 1.0);

            particle_data.local_matrix = world_matrix * particle_data.local_matrix;
        }
    }
    else
    {
        mat4 world_matrix = particle_data.parent_matrix;
        world_matrix[3] = vec4(0.0, 0.0, 0.0, 1.0);
        particle_data.local_matrix = world_matrix * particle_data.local_matrix;
    }
}


void update(inout ParticleData particle_data, uint id)
{
    if(PARTICLE_STATE_DELAY == particle_data.state)
    {
        if(particle_data.delay <= 0.0)
        {
            particle_data.elapsed_time = abs(particle_data.delay);
            particle_data.delay = 0.0;
            particle_data.state = PARTICLE_STATE_ALIVE;
        }
        else
        {
            particle_data.delay -= DELTA_TIME;
        }
    }

    // Update
    if(PARTICLE_STATE_ALIVE == particle_data.state)
    {
        const float max_life_time = PARTICLE_DELAY.y + PARTICLE_LIFE_TIME.y;
        float elapsed_time = particle_data.elapsed_time;
        float left_elapsed_time = particle_data.life_time - elapsed_time;
        particle_data.elapsed_time += DELTA_TIME;

        if(elapsed_time <= particle_data.life_time)
        {
            float life_ratio = 0.0;
            vec3 old_position = particle_data.transform_position;

            if(0.0 < particle_data.life_time)
            {
                life_ratio = clamp(elapsed_time / particle_data.life_time, 0.0, 1.0);
            }

            // update sequence
            update_sequence(particle_data, life_ratio);

            // velocity acceleration
            if(0.0 != PARTICLE_VELOCITY_ACCELERATION && (0.0 != particle_data.velocity_position.x || 0.0 != particle_data.velocity_position.y || 0.0 != particle_data.velocity_position .z))
            {
                float velocity_length = length(particle_data.velocity_position);
                particle_data.velocity_position /= velocity_length;
                velocity_length += PARTICLE_VELOCITY_ACCELERATION * DELTA_TIME;
                if(0.0 < PARTICLE_VELOCITY_LIMIT.y)
                {
                    velocity_length = min(velocity_length, PARTICLE_VELOCITY_LIMIT.y);
                }
                velocity_length = max(velocity_length, PARTICLE_VELOCITY_LIMIT.x);
                particle_data.velocity_position *= velocity_length;
            }

            vec3 force = particle_data.force;

            if(PARTICLE_ENABLE_VECTOR_FIELD)
            {
                vec3 uvw = (PARTICLE_VECTOR_FIELD_INV_MATRIX * vec4(particle_data.transform_position, 1.0)).xyz;
                vec3 vector_field_force = texture3D(texture_vector_field, uvw - vec3(0.5)).xyz * PARTICLE_VECTOR_FIELD_STRENGTH;
                vector_field_force = mat3(PARTICLE_VECTOR_FIELD_MATRIX) * vector_field_force.xyz;
                
                force += vector_field_force * clamp(1.0 - PARTICLE_VECTOR_FIELD_TIGHTNESS, 0.0, 1.0);
                
                particle_data.velocity_position = mix(particle_data.velocity_position, vector_field_force, PARTICLE_VECTOR_FIELD_TIGHTNESS);
            }
            particle_data.velocity_position += force * DELTA_TIME;

            // end of transform
            particle_data.transform_position += particle_data.velocity_position * DELTA_TIME;
            particle_data.transform_rotation += particle_data.velocity_rotation * DELTA_TIME;
            particle_data.transform_scale += particle_data.velocity_scale * DELTA_TIME;

            // relative world position
            particle_data.relative_position = (particle_datas[id].parent_matrix * vec4(particle_data.transform_position, 1.0)).xyz - CAMERA_POSITION.xyz;

            // world velocity
            vec3 world_velocity = mat3(particle_data.parent_matrix) * particle_data.velocity_position.xyz;
            float world_velocity_length = length(world_velocity);
            vec3 normalized_world_velocity = (world_velocity_length != 0.0) ? (world_velocity / world_velocity_length) : world_velocity;

            // Collide
            if(0.0 < world_velocity_length && (0.0 != PARTICLE_FORCE_ELASTICITY || 0.0 != PARTICLE_FORCE_FRICTION))
            {
                vec4 proj_pos = PROJECTION * VIEW_ORIGIN * vec4(particle_data.relative_position, 1.0);
                vec3 scene_uvw = (proj_pos.xyz / proj_pos.w) * 0.5 + 0.5;
                float scene_depth = texture2DLod(texture_depth, scene_uvw.xy, 0.0).x;
                float scene_linear_depth = depth_to_linear_depth(scene_depth);
                vec3 scene_normal = normalize(texture2DLod(texture_normal, scene_uvw.xy, 0.0).xyz * 2.0 - 1.0);
                float depth_diff = proj_pos.w - scene_linear_depth;
                //float depth_diff = depth_to_linear_depth(scene_uvw.z) - scene_linear_depth;

                if(0.0 <= depth_diff && depth_diff < 1.0)
                {
                    vec3 up_vector = scene_normal * dot(scene_normal, -world_velocity);

                    vec3 front_vector = world_velocity + up_vector;
                    float front_vector_length = length(front_vector);
                    if(0.0 < front_vector_length)
                    {
                        front_vector /= front_vector_length;
                        front_vector_length = max(0.0f, front_vector_length - PARTICLE_FORCE_FRICTION * DELTA_TIME);
                        front_vector *= front_vector_length;
                    }
                    particle_data.velocity_position = transpose(mat3(particle_data.parent_matrix)) * (front_vector + up_vector * PARTICLE_FORCE_ELASTICITY);
                    particle_data.transform_position = old_position + particle_data.velocity_position * DELTA_TIME;
                }
            }

            // update matrix
            update_local_matrix(particle_data, normalized_world_velocity, world_velocity_length);

            // update opacity
            particle_data.opacity = PARTICLE_OPACITY;

            if(0.0 < PARTICLE_FADE_IN && elapsed_time < PARTICLE_FADE_IN)
            {
                particle_data.opacity *= elapsed_time / PARTICLE_FADE_IN;
            }

            if(0.0 < PARTICLE_FADE_OUT && left_elapsed_time < PARTICLE_FADE_OUT)
            {
                particle_data.opacity *= left_elapsed_time / PARTICLE_FADE_OUT;
            }
        }
        else if(max_life_time <= particle_data.elapsed_time)
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
