import numpy as np


class ParticleManager:
    def __init__(self):
        self.active = True
        self.emitters = {}
        self.particle_groups = {}
        self.active_particle_groups = []

    def setActive(self, active):
        self.active = active

    def clear_particles(self):
        self.destroy_particles()
        self.particle_groups = {}

    def destroy_particles(self):
        for i in self.particle_groups:
            self.particle_groups[i].destroy()

        self.active_particle_groups = []

    def get_particle_groups(self, name):
        return self.particle_groups[name]

    def regist_emitter(self, name, info, num):
        emitter = Emitter(self, info, num)
        self.emitters[name] = emitter
        return emitter

    def unregist_emitter(self, name):
        if name in self.emitters:
            emitter = self.emitters[name]
            emitter.destroy()
            if emitter in self.aliveEmitters:
                self.aliveEmitters.remove(emitter)

    def stop_emitters(self):
        for i in self.emitters:
            self.emitters[i].stop_particles()

    def notify_play_emitter(self, emitter):
        if not emitter in self.aliveEmitters:
            self.aliveEmitters.append(emitter)

    def notify_stop_emitter(self, emitter):
        if emitter in self.aliveEmitters:
            self.aliveEmitters.remove(emitter)

    def update(self, dt):
        if not self.active:
            return
        # gDebug.Print("emitters : " + str(len(self.aliveEmitters)))
        for emitter in self.aliveEmitters:
            emitter.update(dt)


class ParticleGroup:
    pass


class Emitter:
    def __init__(self, fxMgr, parent_layer, info, num):
        Scatter.__init__(self, size=[0, 0])
        self.do_translation = False
        self.do_rotation = False
        self.do_scale = False
        self.particles = []
        self.fxMgr = fxMgr
        self.create_particle(info, num)
        self.parent_layer = parent_layer
        self.aliveParticles = []

    def create_particle(self, info, num):
        self.info = info
        for i in range(num):
            par = Particle(self)
            par.Create(**info)
            self.particles.append(par)

    def destroy(self):
        for i in self.particles:
            i.destroy()
        self.aliveParticles = []
        self.particles = []

        if self.parent:
            self.parent.remove_widget(self)

    def play_particle(self):
        self.fxMgr.notify_play_emitter(self)
        if self.parent and self.parent != self.parent_layer:
            self.parent.remove_widget(self)
            self.parent_layer.add_widget(self)
            return
        elif not self.parent:
            self.parent_layer.add_widget(self)
        for i in self.particles:
            i.play(None, False)

    def play_particle_with(self, parent, bWorldSpace):
        self.fxMgr.notify_play_emitter(self)
        if self.parent and self.parent != parent:
            self.parent.remove_widget(self)
        if not self.parent:
            parent.add_widget(self)
        for i in self.particles:
            i.play(parent, bWorldSpace)

    def stop_particles(self):
        for i in self.aliveParticles:
            i.stop(True)

    def notify_play_particle(self, particle):
        if not particle in self.aliveParticles:
            self.aliveParticles.append(particle)

    def notify_stop_particle(self, particle):
        if particle in self.aliveParticles:
            self.aliveParticles.remove(particle)
        if self.aliveParticles == []:
            self.fxMgr.notify_stop_emitter(self)

    def update(self, dt):
        for i in self.aliveParticles:
            i.update(dt)


class Particle:
    def __init__(self, emitter):
        self.emitter = emitter
        self.bFirstTime = True
        self.isAlive = False
        self.elapseTime = 0.0
        self.accTime = 0.0
        self.texture = None
        self.curtexture = None
        self.curseq = [0, 0]
        self.cellsize = [1.0, 1.0]
        self.cellcount = 1
        self.oldsequence = -1
        self.attachTo = None
        self.bWorldSpace = False
        self.boxRot = None
        self.boxPos = None

        # variation
        self.collision = False
        self.loop = 1  # -1 is infinite
        self.loopleft = self.loop
        self.fade = 0.0
        self.sequence = [1, 1]
        self.playspeed = 1.0
        self.elastin = 0.8

        self.delay = 0.0
        self.lifeTime = 1.0
        self.gravity = 980.0
        self.vel = [0.0, 0.0]
        self.rotateVel = 0.0
        self.rotate = 0.0
        self.scaling = 1.0
        self.opacity = 1.0
        self.offset = (0.0, 0.0)
        self.variables = {
            'delay': Var(self.delay),
            'lifeTime': Var(self.lifeTime),
            'gravity': Var(self.gravity),
            'vel': Var(self.vel),
            'rotateVel': Var(self.rotateVel),
            'rotate': Var(self.rotate),
            'scaling': Var(self.scaling),
            'opacity': Var(self.opacity),
            'offset': Var(self.offset)
        }

    def Create(self, elastin=0.8, collision=False, size=[100, 100],
               source=None, texture=None, loop=1, fade=0.0,
               sequence=[1, 1], playspeed=1.0, **kargs):
        self.collision = collision
        self.elastin = max(min(elastin, 1.0), 0.0)
        self.size = size
        self.loop = loop
        self.fade = fade
        self.sequence = sequence
        self.playspeed = playspeed

        if texture == None:
            if source != None:
                self.texture = Image(source=source).texture
        else:
            self.texture = texture

        if self.sequence[0] == 1 and self.sequence[1] == 1:
            self.playspeed = 0

        for key in kargs:
            if not hasattr(self, key):
                raise AttributeError(self.__class__.__name__ + " has not attribue " + key)
            self.variables[key] = kargs[key]

        if self.texture:
            self.cellcount = self.sequence[0] * self.sequence[1]
            self.cellsize = div(self.texture.size, self.sequence)
            curtexture = self.texture.get_region(0.0, 0.0, *self.cellsize)
            with self.canvas:
                Color(1, 1, 1, 1)
                self.box = Rectangle(texture=curtexture, pos=(0, 0), size=self.size)
            with self.canvas.before:
                PushMatrix()
                self.boxPos = Translate(0, 0)
                self.boxRot = Rotate(angle=0, axis=(0, 0, 1), origin=mul(mul(self.size, 0.5), self.scaling))
                self.boxScale = Scale(1, 1, 1)
            with self.canvas.after:
                PopMatrix()

    def play(self, attachTo, bWorldSpace):
        self.emitter.notify_play_particle(self)
        self.attachTo = attachTo
        self.bWorldSpace = bWorldSpace
        self.isAlive = True
        self.loopleft = self.loop
        self.elapseTime = 0.0
        self.oldsequence = -1
        if self.parent:
            self.parent.remove_widget(self)
        self.refresh()

    def refresh(self, bUpdateOnlyTranslate=False):
        if not bUpdateOnlyTranslate:
            for key in self.variables:
                setattr(self, key, self.variables[key].get())
            self.vel = div(self.vel, self.scaling)
            self.realSize = mul(self.size, self.scaling)
            self.boxRot.origin = origin = mul(mul(self.size, 0.5), self.scaling)
            self.boxRot.angle = self.rotate
            self.boxScale.xyz = (self.scaling, self.scaling, self.scaling)
        # refresh translate
        self.boxPos.x = -self.realSize[0] * 0.5 + self.offset[0]
        self.boxPos.y = -self.realSize[1] * 0.5 + self.offset[1]
        if self.attachTo:
            if self.bWorldSpace:
                self.boxPos.x += self.attachTo.center[0]
                self.boxPos.y += self.attachTo.center[1]
            else:
                self.boxPos.x += self.attachTo.size[0] * 0.5
                self.boxPos.y += self.attachTo.size[1] * 0.5

    def updateSequence(self):
        if self.cellcount > 1 and self.playspeed > 0:
            ratio = self.elapseTime / self.lifeTime
            ratio *= self.playspeed
            ratio %= 1.0
            index = int(math.floor(self.cellcount * ratio))
            if index == self.oldsequence:
                return
            if index == self.cellcount:
                index = self.cellcount - 1
            self.oldsequence = index
            self.curseq = [index % self.sequence[0], self.sequence[1] - int(index / self.sequence[0]) - 1]
            self.curseq = mul(self.curseq, self.cellsize)
            self.box.texture = self.texture.get_region(*(self.curseq + self.cellsize))

    def update(self, fFrameTime):
        if not self.isAlive:
            return

        if not self.parent:
            self.delay -= fFrameTime
            if self.delay < 0.0:
                if self.bWorldSpace:
                    self.emitter.parent_layer.add_widget(self)
                else:
                    self.emitter.add_widget(self)
                self.refresh(bUpdateOnlyTranslate=True)
            else:
                return

        self.accTime += fFrameTime
        self.elapseTime += fFrameTime

        if self.elapseTime > self.lifeTime:
            self.elapseTime -= self.lifeTime
            if self.loopleft > 0:
                self.loopleft -= 1
            if self.loopleft == 0:
                self.destroy()
                return
            self.refresh()

        if self.lifeTime > 0:
            lifeRatio = self.elapseTime / self.lifeTime

        self.updateSequence()

        if self.gravity != 0:
            self.vel[1] -= self.gravity * fFrameTime

        # adjust velocity, move
        if self.collision:
            self.boxPos.x += self.vel[0] * fFrameTime
            self.boxPos.y += self.vel[1] * fFrameTime
            if self.boxPos.x < 0.0:
                self.boxPos.x = -self.boxPos.x
                self.vel[0] = -self.vel[0] * self.elastin
            elif self.boxPos.x > Util.W - self.size[0]:
                self.boxPos.x = (Util.W - self.size[0]) * 2.0 - self.boxPos.x
                self.vel[0] = -self.vel[0] * self.elastin
            if self.boxPos.y < 0.0:
                self.boxPos.y = -self.boxPos.y
                self.vel[1] = -self.vel[1] * self.elastin
            elif self.boxPos.y > Util.H - self.size[1]:
                self.boxPos.y = (Util.H - self.size[1]) * 2.0 - self.boxPos.y
                self.vel[1] = -self.vel[1] * self.elastin
        else:
            if self.vel[0] != 0:
                self.boxPos.x += self.vel[0] * fFrameTime
            if self.vel[1] != 0:
                self.boxPos.y += self.vel[1] * fFrameTime

        if self.rotateVel != 0.0:
            self.boxRot.angle += self.rotateVel * fFrameTime

        if self.fade:
            opacity = 1.0 - lifeRatio
            opacity = max(min(opacity, 1.0), 0.0)
            self.opacity = pow(opacity, self.fade)

    def stop(self, isStop):
        self.isAlive = not isStop

    def destroy(self):
        self.isAlive = False
        self.emitter.notify_stop_particle(self)
        if self.parent:
            self.parent.remove_widget(self)