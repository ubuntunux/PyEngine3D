import time
import sys

from multiprocessing import Process, Queue, Pipe
from pathos.multiprocessing import ProcessingPool as Pool

from threading import Thread


import numpy as np
from Utilities import *


class TransformObject:
    def __init__(self, pos):
        # transform
        self.quat = Float4(0.0, 0.0, 0.0, 1.0)
        self.matrix = Identity()
        self.inverse_matrix = Identity()
        self.translateMatrix = Identity()
        self.rotationMatrix = Identity()
        self.scaleMatrix = Identity()

        self.right = WORLD_RIGHT.copy()
        self.up = WORLD_UP.copy()
        self.front = WORLD_FRONT.copy()

        # init transform
        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True
        self.force_update = True
        self.pos = Float3(*pos)
        self.oldPos = Float3()
        self.rot = Float3()
        self.oldRot = Float3()
        self.scale = Float3(1, 1, 1)
        self.oldScale = Float3(1, 1, 1)
        self.updateTransform()

    def resetTransform(self):
        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True
        self.force_update = True
        self.setPos(Float3())
        self.setRot(Float3())
        self.setScale(Float3(1, 1, 1))
        self.updateTransform()

    # Translate
    def getPos(self):
        return self.pos

    def setPos(self, pos):
        self.moved = True
        self.pos[...] = pos

    def setPosX(self, x):
        self.moved = True
        self.pos[0] = x

    def setPosY(self, y):
        self.moved = True
        self.pos[1] = y

    def setPosZ(self, z):
        self.moved = True
        self.pos[2] = z

    def move(self, vDelta):
        self.moved = True
        self.pos[...] = self.pos + vDelta

    def moveToFront(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.front * delta

    def moveToRight(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.right * delta

    def moveToUp(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.up * delta

    def moveX(self, delta):
        self.moved = True
        self.pos[0] += delta

    def moveY(self, delta):
        self.moved = True
        self.pos[1] += delta

    def moveZ(self, delta):
        self.moved = True
        self.pos[2] += delta

    # Rotation
    def getRotation(self):
        return self.rot

    def setRot(self, rot):
        self.rotated = True
        self.rot[...] = rot

    def setPitch(self, pitch):
        self.rotated = True
        if pitch > TWO_PI or pitch < 0.0:
            pitch %= TWO_PI
        self.rot[0] = pitch

    def setYaw(self, yaw):
        self.rotated = True
        if yaw > TWO_PI or yaw < 0.0:
            yaw %= TWO_PI
        self.rot[1] = yaw

    def setRoll(self, roll):
        self.rotated = True
        if roll > TWO_PI or roll < 0.0:
            roll %= TWO_PI
        self.rot[2] = roll

    def rotationPitch(self, delta=0.0):
        self.rotated = True
        self.rot[0] += delta
        if self.rot[0] > TWO_PI or self.rot[0] < 0.0:
            self.rot[0] %= TWO_PI

    def rotationYaw(self, delta=0.0):
        self.rotated = True
        self.rot[1] += delta
        if self.rot[1] > TWO_PI or self.rot[1] < 0.0:
            self.rot[1] %= TWO_PI

    def rotationRoll(self, delta=0.0):
        self.rotated = True
        self.rot[2] += delta
        if self.rot[2] > TWO_PI or self.rot[2] < 0.0:
            self.rot[2] %= TWO_PI

    # Scale
    def getScale(self):
        return self.scale

    def setScale(self, vScale):
        self.scaled = True
        self.scale[...] = vScale

    def setScaleX(self, x):
        self.scaled = True
        self.scale[0] = x

    def setScaleY(self, y):
        self.scaled = True
        self.scale[1] = y

    def setScaleZ(self, z):
        self.scaled = True
        self.scale[2] = z

    def update(self):
        self.count += 1
        self.resetTransform()
        self.updateTransform()
        return self

    # update Transform
    def updateTransform(self):
        self.updated = False

        if self.moved and any(self.oldPos != self.pos) or self.force_update:
            self.oldPos[...] = self.pos
            self.translateMatrix = getTranslateMatrix(self.pos[0], self.pos[1], self.pos[2])
            self.moved = False
            self.updated = True

        if self.rotated and any(self.oldRot != self.rot) or self.force_update:
            self.oldRot[...] = self.rot
            self.rotated = False
            self.updated = True

            # Matrix Rotation - faster
            matrix_rotation(*self.rot, self.rotationMatrix)
            matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

            # Euler Rotation - slow
            # p = getRotationMatrixX(self.rot[0])
            # y = getRotationMatrixY(self.rot[1])
            # r = getRotationMatrixZ(self.rot[2])
            # self.rotationMatrix = np.dot(p, np.dot(y, r))
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

            # Quaternion Rotation - slower
            # euler_to_quaternion(*self.rot, self.quat)
            # quaternion_to_matrix(self.quat, self.rotationMatrix)
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

        if self.scaled and any(self.oldScale != self.scale) or self.force_update:
            self.oldScale[...] = self.scale
            self.scaleMatrix = getScaleMatrix(self.scale[0], self.scale[1], self.scale[2])
            self.scaled = False
            self.updated = True

        if self.updated or self.force_update:
            self.force_update = False
            self.matrix = np.dot(self.scaleMatrix, np.dot(self.rotationMatrix, self.translateMatrix))


def run():
    def job(ts):
        for t in ts:
            t.count += 1
            t.resetTransform()
            t.updateTransform()

    def multi_job(job_pipe, end_pipe):
        while True:
            value = end_pipe.recv()
            if not value:
                ts = job_pipe.recv()
                for t in ts:
                    t.count += 1
                    t.resetTransform()
                    t.updateTransform()
                job_pipe.send(ts)
            else:
                break

    thread_count = 8
    object_count_per_thread = 200
    object_count = object_count_per_thread * thread_count
    loop_count = 2

    ts = []
    for i in range(object_count):
        t = TransformObject((0, 0, 0))
        t.count = 0
        ts.append(t)

    # pool example
    def pool_job(q):
        for i in range(loop_count-1):
            q()
        return q()

    p = Pool(120)

    qs = []
    for t in ts:
        qs.append(t.update)

    start_time = time.perf_counter()
    ts = p.map(pool_job, qs)
    print(time.perf_counter() - start_time)
    count = 0
    for t in ts:
        count += t.count
        t.count = 0
    print(count)

    # sing core
    start_time = time.perf_counter()
    for i in range(loop_count):
        job(ts)
    print(time.perf_counter() - start_time)
    count = 0
    for t in ts:
        count += t.count
        t.count = 0
    print(count)

    # multiprocess
    job_pipes = []
    end_pipes = []
    processes = []
    split_ts = []
    for i in range(thread_count):
        pipe1, pipe2 = Pipe()
        job_pipes.append(pipe1)
        end_pipe1, end_pipe2 = Pipe()
        end_pipes.append(end_pipe1)
        process = Process(target=multi_job, args=(pipe2, end_pipe2))
        process.start()
        processes.append(process)
        split_ts.append(ts[i * object_count_per_thread:i * object_count_per_thread + object_count_per_thread])

    start_time = time.perf_counter()
    for i in range(loop_count):
        for j in range(thread_count):
            end_pipes[j].send(False)
            job_pipes[j].send(split_ts[j])
        for j in range(thread_count):
            split_ts[j] = job_pipes[j].recv()

    for i in range(thread_count):
        end_pipes[i].send(True)
        processes[i].join()
    print(time.perf_counter() - start_time)

    ts = []
    for i in range(thread_count):
        ts += split_ts[i]

    count = 0
    for t in ts:
        count += t.count
        t.count = 0
    print(count)

if __name__ == "__main__":
    run()
