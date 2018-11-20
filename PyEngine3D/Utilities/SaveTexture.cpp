// save to file
SaveTextureImage(GL_TEXTURE_2D, GL_RGBA32F, transmittance_texture_, "transmittance.texture");
SaveTextureImage(GL_TEXTURE_3D, GL_RGBA32F, scattering_texture_, "scattering.texture");
SaveTextureImage(GL_TEXTURE_2D, GL_RGBA32F, irradiance_texture_, "irradiance.texture");


GLuint SaveTextureImage(GLuint target, GLuint internal_format, GLuint texture, const char* filename)
{
	std::cout << "SaveTextureImage : " << filename << std::endl;
	glBindTexture(target, texture);

	GLint textureWidth, textureHeight, textureDepth;
	int count;
	glGetTexLevelParameteriv(target, 0, GL_TEXTURE_WIDTH, &textureWidth);
	glGetTexLevelParameteriv(target, 0, GL_TEXTURE_HEIGHT, &textureHeight);
	glGetTexLevelParameteriv(target, 0, GL_TEXTURE_DEPTH, &textureDepth);
	count = textureWidth * textureHeight * 4;

	const char* texture_type = (target == GL_TEXTURE_3D) ? "Texture3D" : "Texture2D";
	const char* szInternalFormat = (internal_format == GL_RGBA32F) ? "GL_RGBA32F" : "GL_RGBA16F";

	std::ofstream myfile;
	myfile.open(filename);

	myfile << "{" << std::endl;
	myfile << "\t'width': " << textureWidth << ", " << std::endl;
	myfile << "\t'height': " << textureHeight << ", " << std::endl;
	myfile << "\t'depth': " << textureDepth << ", " << std::endl;
	myfile << "\t'image_mode': " << "'RGBA', " << std::endl;
	myfile << "\t'internal_format': " << szInternalFormat << ", " << std::endl;
	myfile << "\t'texture_format': " << "GL_RGBA, " << std::endl;
	myfile << "\t'mag_filter': " << "GL_LINEAR, " << std::endl;
	myfile << "\t'min_filter': " << "GL_LINEAR, " << std::endl;
	myfile << "\t'texture_type': " << texture_type << ", " << std::endl;
	myfile << "\t'wrap': " << "GL_CLAMP_TO_EDGE, " << std::endl;
	myfile << "\t'data_type': " << "GL_FLOAT, " << std::endl;

	////////////////////////////////////////////////
	// write data
	float *pixels = new float[count];

	myfile << "\t'data': [";

	if(GL_TEXTURE_2D == target)
	{
		glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT, pixels);
		int nWidthCount = 0;
		for(int i=0; i<count; ++i)
		{
			++nWidthCount;
			myfile << (std::isnan(pixels[i]) ? 0.0f : pixels[i]) << ", ";
			if(textureWidth <= nWidthCount)
			{
				nWidthCount = 0;
				myfile << "\n";
			}
		}
	}
	else if(GL_TEXTURE_3D == target)
	{
		GLuint fb;
		glGenFramebuffers(1, &fb);
		glBindFramebuffer(GL_FRAMEBUFFER, fb);
		for(int layer=0; layer<textureDepth; ++layer)
		{
			glFramebufferTexture3D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_3D, texture, 0, layer);
			glReadBuffer(GL_COLOR_ATTACHMENT0);
			glReadPixels(0, 0, textureWidth, textureHeight, GL_RGBA, GL_FLOAT, pixels);
			int nWidthCount = 0;
			for(int i=0; i<count; ++i)
			{
				++nWidthCount;
				myfile << (std::isnan(pixels[i]) ? 0.0f : pixels[i]) << ", ";
				if(textureWidth <= nWidthCount)
				{
					nWidthCount = 0;
					myfile << "\n";
				}
			}
		}
		glBindFramebuffer(GL_FRAMEBUFFER, 0);
		glDeleteFramebuffers(1, &fb);
	}
	glBindTexture(target, 0);

	myfile << "]\n}" << std::endl;
	myfile.close();
	delete pixels;
}