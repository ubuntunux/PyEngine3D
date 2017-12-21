kVertexShader = """
    #version 330
    uniform mat4 model_from_view;
    uniform mat4 view_from_clip;
    layout(location = 0) in vec4 vertex;
    out vec3 view_ray;
    void main() {
      view_ray = (model_from_view * vec4((view_from_clip * vertex).xyz, 0.0)).xyz;
      gl_Position = vertex;
    }"""


class Demo:
    def __init__(self, viewport_width, viewport_height):
        self.use_constant_solar_spectrum = False
        self.use_ozone = True
        self.use_combined_textures = True
        self.use_half_precision = True
        self.use_luminance = None
        self.do_white_balance = False
        self.show_help = True
        self.program = 0
        self.view_distance_meters = 9000.0
        self.view_zenith_angle_radians = 1.47
        self.view_azimuth_angle_radians = -0.1
        self.sun_zenith_angle_radians = 1.3
        self.sun_azimuth_angle_radians = 2.9
        self.exposure = 10.0

        self.InitModel()

    def InitModel(self):
        max_sun_zenith_angle = (102.0 if use_half_precision else 120.0) / 180.0 * kPi

  DensityProfileLayer
      rayleigh_layer(0.0, 1.0, -1.0 / kRayleighScaleHeight, 0.0, 0.0)
  DensityProfileLayer mie_layer(0.0, 1.0, -1.0 / kMieScaleHeight, 0.0, 0.0)
  # Density profile increasing linearly from 0 to 1 between 10 and 25km, and
  # decreasing linearly from 1 to 0 between 25 and 40km. This is an approximate
  # profile from http://www.kln.ac.lk/science/Chemistry/Teaching_Resources/
  # Documents/Introduction%20to%20atmospheric%20chemistry.pdf (page 10).
  std::vector<DensityProfileLayer> ozone_density
  ozone_density.push_back(
      DensityProfileLayer(25000.0, 0.0, 0.0, 1.0 / 15000.0, -2.0 / 3.0))
  ozone_density.push_back(
      DensityProfileLayer(0.0, 0.0, 0.0, -1.0 / 15000.0, 8.0 / 3.0))

  std::vector<double> wavelengths
  std::vector<double> solar_irradiance
  std::vector<double> rayleigh_scattering
  std::vector<double> mie_scattering
  std::vector<double> mie_extinction
  std::vector<double> absorption_extinction
  std::vector<double> ground_albedo
  for (int l = kLambdaMin l <= kLambdaMax l += 10) {
    double lambda = static_cast<double>(l) * 1e-3  # micro-meters
    double mie =
        kMieAngstromBeta / kMieScaleHeight * pow(lambda, -kMieAngstromAlpha)
    wavelengths.push_back(l)
    if (use_constant_solar_spectrum_) {
      solar_irradiance.push_back(kConstantSolarIrradiance)
    } else {
      solar_irradiance.push_back(kSolarIrradiance[(l - kLambdaMin) / 10])
    }
    rayleigh_scattering.push_back(kRayleigh * pow(lambda, -4))
    mie_scattering.push_back(mie * kMieSingleScatteringAlbedo)
    mie_extinction.push_back(mie)
    absorption_extinction.push_back(use_ozone_ ?
        kMaxOzoneNumberDensity * kOzoneCrossSection[(l - kLambdaMin) / 10] :
        0.0)
    ground_albedo.push_back(kGroundAlbedo)
  }

  model_.reset(new Model(wavelengths, solar_irradiance, kSunAngularRadius,
      kBottomRadius, kTopRadius, {rayleigh_layer}, rayleigh_scattering,
      {mie_layer}, mie_scattering, mie_extinction, kMiePhaseFunctionG,
      ozone_density, absorption_extinction, ground_albedo, max_sun_zenith_angle,
      kLengthUnitInMeters, use_luminance_ == PRECOMPUTED ? 15 : 3,
      use_combined_textures_, use_half_precision_))
  model_->Init()

/*
<p>Then, it creates and compiles the vertex and fragment shaders used to render
our demo scene, and link them with the <code>Model</code>'s atmosphere shader
to get the final scene rendering program:
*/

  GLuint vertex_shader = glCreateShader(GL_VERTEX_SHADER)
  const char* const vertex_shader_source = kVertexShader
  glShaderSource(vertex_shader, 1, &vertex_shader_source, NULL)
  glCompileShader(vertex_shader)

  const std::string fragment_shader_str =
      "#version 330\n" +
      std::string(use_luminance_ != NONE ? "#define USE_LUMINANCE\n" : "") +
      demo_glsl
  const char* fragment_shader_source = fragment_shader_str.c_str()
  GLuint fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
  glShaderSource(fragment_shader, 1, &fragment_shader_source, NULL)
  glCompileShader(fragment_shader)

  if (program_ != 0) {
    glDeleteProgram(program_)
  }
  program_ = glCreateProgram()
  glAttachShader(program_, vertex_shader)
  glAttachShader(program_, fragment_shader)
  glAttachShader(program_, model_->GetShader())
  glLinkProgram(program_)
  glDetachShader(program_, vertex_shader)
  glDetachShader(program_, fragment_shader)
  glDetachShader(program_, model_->GetShader())
  glDeleteShader(vertex_shader)
  glDeleteShader(fragment_shader)

/*
<p>Finally, it sets the uniforms of this program that can be set once and for
all (in our case this includes the <code>Model</code>'s texture uniforms,
because our demo app does not have any texture of its own):
*/

  glUseProgram(program_)
  model_->SetProgramUniforms(program_, 0, 1, 2, 3)
  double white_point_r = 1.0
  double white_point_g = 1.0
  double white_point_b = 1.0
  if (do_white_balance_) {
    Model::ConvertSpectrumToLinearSrgb(wavelengths, solar_irradiance,
        &white_point_r, &white_point_g, &white_point_b)
    double white_point = (white_point_r + white_point_g + white_point_b) / 3.0
    white_point_r /= white_point
    white_point_g /= white_point
    white_point_b /= white_point
  }
  glUniform3f(glGetUniformLocation(program_, "white_point"),
      white_point_r, white_point_g, white_point_b)
  glUniform3f(glGetUniformLocation(program_, "earth_center"),
      0.0, 0.0, -kBottomRadius / kLengthUnitInMeters)
  glUniform2f(glGetUniformLocation(program_, "sun_size"),
      tan(kSunAngularRadius),
      cos(kSunAngularRadius))

  # This sets 'view_from_clip', which only depends on the window size.
  HandleReshapeEvent(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
}

/*
<p>The scene rendering method simply sets the uniforms related to the camera
position and to the Sun direction, and then draws a full screen quad (and
optionally a help screen).
*/

void Demo::HandleRedisplayEvent() const {
  # Unit vectors of the camera frame, expressed in world space.
  float cos_z = cos(view_zenith_angle_radians_)
  float sin_z = sin(view_zenith_angle_radians_)
  float cos_a = cos(view_azimuth_angle_radians_)
  float sin_a = sin(view_azimuth_angle_radians_)
  float ux[3] = { -sin_a, cos_a, 0.0 }
  float uy[3] = { -cos_z * cos_a, -cos_z * sin_a, sin_z }
  float uz[3] = { sin_z * cos_a, sin_z * sin_a, cos_z }
  float l = view_distance_meters_ / kLengthUnitInMeters

  # Transform matrix from camera frame to world space (i.e. the inverse of a
  # GL_MODELVIEW matrix).
  float model_from_view[16] = {
    ux[0], uy[0], uz[0], uz[0] * l,
    ux[1], uy[1], uz[1], uz[1] * l,
    ux[2], uy[2], uz[2], uz[2] * l,
    0.0, 0.0, 0.0, 1.0
  }

  glUniform3f(glGetUniformLocation(program_, "camera"),
      model_from_view[3],
      model_from_view[7],
      model_from_view[11])
  glUniform1f(glGetUniformLocation(program_, "exposure"),
      use_luminance_ != NONE ? exposure_ * 1e-5 : exposure_)
  glUniformMatrix4fv(glGetUniformLocation(program_, "model_from_view"),
      1, true, model_from_view)
  glUniform3f(glGetUniformLocation(program_, "sun_direction"),
      cos(sun_azimuth_angle_radians_) * sin(sun_zenith_angle_radians_),
      sin(sun_azimuth_angle_radians_) * sin(sun_zenith_angle_radians_),
      cos(sun_zenith_angle_radians_))

  glBindVertexArray(full_screen_quad_vao_)
  glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
  glBindVertexArray(0)

  if (show_help_) {
    std::stringstream help
    help << "Mouse:\n"
         << " drag, CTRL+drag, wheel: view and sun directions\n"
         << "Keys:\n"
         << " h: help\n"
         << " s: solar spectrum (currently: "
         << (use_constant_solar_spectrum_ ? "constant" : "realistic") << ")\n"
         << " o: ozone (currently: " << (use_ozone_ ? "on" : "off") << ")\n"
         << " t: combine textures (currently: "
         << (use_combined_textures_ ? "on" : "off") << ")\n"
         << " p: half precision (currently: "
         << (use_half_precision_ ? "on" : "off") << ")\n"
         << " l: use luminance (currently: "
         << (use_luminance_ == PRECOMPUTED ? "precomputed" :
             (use_luminance_ == APPROXIMATE ? "approximate" : "off")) << ")\n"
         << " w: white balance (currently: "
         << (do_white_balance_ ? "on" : "off") << ")\n"
         << " +/-: increase/decrease exposure (" << exposure_ << ")\n"
         << " 1-9: predefined views\n"
    text_renderer_->SetColor(1.0, 0.0, 0.0)
    text_renderer_->DrawText(help.str(), 5, 4)
  }

  glutSwapBuffers()
  glutPostRedisplay()
}

/*
<p>The other event handling methods are also straightforward, and do not
interact with the atmosphere model:
*/

void Demo::HandleReshapeEvent(int viewport_width, int viewport_height) {
  glViewport(0, 0, viewport_width, viewport_height)

  const float kFovY = 50.0 / 180.0 * kPi
  const float kTanFovY = tan(kFovY / 2.0)
  float aspect_ratio = static_cast<float>(viewport_width) / viewport_height

  # Transform matrix from clip space to camera space (i.e. the inverse of a
  # GL_PROJECTION matrix).
  float view_from_clip[16] = {
    kTanFovY * aspect_ratio, 0.0, 0.0, 0.0,
    0.0, kTanFovY, 0.0, 0.0,
    0.0, 0.0, 0.0, -1.0,
    0.0, 0.0, 1.0, 1.0
  }
  glUniformMatrix4fv(glGetUniformLocation(program_, "view_from_clip"), 1, true,
      view_from_clip)
}

void Demo::HandleKeyboardEvent(unsigned char key) {
  if (key == 27) {
    glutDestroyWindow(window_id_)
  } else if (key == 'h') {
    show_help_ = !show_help_
  } else if (key == 's') {
    use_constant_solar_spectrum_ = !use_constant_solar_spectrum_
  } else if (key == 'o') {
    use_ozone_ = !use_ozone_
  } else if (key == 't') {
    use_combined_textures_ = !use_combined_textures_
  } else if (key == 'p') {
    use_half_precision_ = !use_half_precision_
  } else if (key == 'l') {
    switch (use_luminance_) {
      case NONE: use_luminance_ = APPROXIMATE break
      case APPROXIMATE: use_luminance_ = PRECOMPUTED break
      case PRECOMPUTED: use_luminance_ = NONE break
    }
  } else if (key == 'w') {
    do_white_balance_ = !do_white_balance_
  } else if (key == '+') {
    exposure_ *= 1.1
  } else if (key == '-') {
    exposure_ /= 1.1
  } else if (key == '1') {
    SetView(9000.0, 1.47, 0.0, 1.3, 3.0, 10.0)
  } else if (key == '2') {
    SetView(9000.0, 1.47, 0.0, 1.564, -3.0, 10.0)
  } else if (key == '3') {
    SetView(7000.0, 1.57, 0.0, 1.54, -2.96, 10.0)
  } else if (key == '4') {
    SetView(7000.0, 1.57, 0.0, 1.328, -3.044, 10.0)
  } else if (key == '5') {
    SetView(9000.0, 1.39, 0.0, 1.2, 0.7, 10.0)
  } else if (key == '6') {
    SetView(9000.0, 1.5, 0.0, 1.628, 1.05, 200.0)
  } else if (key == '7') {
    SetView(7000.0, 1.43, 0.0, 1.57, 1.34, 40.0)
  } else if (key == '8') {
    SetView(2.7e6, 0.81, 0.0, 1.57, 2.0, 10.0)
  } else if (key == '9') {
    SetView(1.2e7, 0.0, 0.0, 0.93, -2.0, 10.0)
  }
  if (key == 's' || key == 'o' || key == 't' || key == 'p' || key == 'l' ||
      key == 'w') {
    InitModel()
  }
}

void Demo::HandleMouseClickEvent(
    int button, int state, int mouse_x, int mouse_y) {
  previous_mouse_x_ = mouse_x
  previous_mouse_y_ = mouse_y
  is_ctrl_key_pressed_ = (glutGetModifiers() & GLUT_ACTIVE_CTRL) != 0

  if ((button == 3) || (button == 4)) {
    if (state == GLUT_DOWN) {
      HandleMouseWheelEvent(button == 3 ? 1 : -1)
    }
  }
}

void Demo::HandleMouseDragEvent(int mouse_x, int mouse_y) {
  kScale = 500.0
  if (is_ctrl_key_pressed_) {
    sun_zenith_angle_radians_ -= (previous_mouse_y_ - mouse_y) / kScale
    sun_zenith_angle_radians_ =
        std::max(0.0, std::min(kPi, sun_zenith_angle_radians_))
    sun_azimuth_angle_radians_ += (previous_mouse_x_ - mouse_x) / kScale
  } else {
    view_zenith_angle_radians_ += (previous_mouse_y_ - mouse_y) / kScale
    view_zenith_angle_radians_ =
        std::max(0.0, std::min(kPi / 2.0, view_zenith_angle_radians_))
    view_azimuth_angle_radians_ += (previous_mouse_x_ - mouse_x) / kScale
  }
  previous_mouse_x_ = mouse_x
  previous_mouse_y_ = mouse_y
}

void Demo::HandleMouseWheelEvent(int mouse_wheel_direction) {
  if (mouse_wheel_direction < 0) {
    view_distance_meters_ *= 1.05
  } else {
    view_distance_meters_ /= 1.05
  }
}

void Demo::SetView(double view_distance_meters,
    double view_zenith_angle_radians, double view_azimuth_angle_radians,
    double sun_zenith_angle_radians, double sun_azimuth_angle_radians,
    double exposure) {
  view_distance_meters_ = view_distance_meters
  view_zenith_angle_radians_ = view_zenith_angle_radians
  view_azimuth_angle_radians_ = view_azimuth_angle_radians
  sun_zenith_angle_radians_ = sun_zenith_angle_radians
  sun_azimuth_angle_radians_ = sun_azimuth_angle_radians
  exposure_ = exposure
}