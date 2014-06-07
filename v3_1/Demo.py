from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GL.ARB.vertex_buffer_object import *
import numpy
import math

class DisplayWidget(QGLWidget):
    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(500, 500)

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.tmp_offset_x = 0.0
        self.tmp_offset_y = 0.0
        self.scale = 1.0

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, """
#version 120
attribute vec2 position;
uniform float w, h, scale, offset_x, offset_y;
void main()
{
    float x, y;
    if (w > h) {
        x = (position.x + offset_x) * scale * h / w;
        y = (position.y + offset_y) * scale;
    } else {
        x = (position.x + offset_x) * scale;
        y = (position.y + offset_y) * scale * w / h;
    }
    gl_Position = vec4(x, y, 0., 1.);
}
""")
        glCompileShader(vs)
        result = glGetShaderiv(vs, GL_COMPILE_STATUS)
        if not(result):
            raise RuntimeError(glGetShaderInfoLog(vs))

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, """
#version 120
void main()
{
    gl_FragColor = vec4(1., 0., 0., 1.);
}
""")
        glCompileShader(fs)
        result = glGetShaderiv(fs, GL_COMPILE_STATUS)
        if not(result):
            raise RuntimeError(glGetShaderInfoLog(fs))

        self.program = glCreateProgram()
        glAttachShader(self.program, vs)
        glAttachShader(self.program, fs)
        glLinkProgram(self.program)
        result = glGetProgramiv(self.program, GL_LINK_STATUS)
        if not(result):
            raise RuntimeError(glGetProgramInfoLog(self.program))

        self.attrib = glGetAttribLocation(self.program, "position")
        self.uniform_scale = glGetUniformLocation(self.program, "scale")
        self.uniform_offset_x = glGetUniformLocation(self.program, "offset_x")
        self.uniform_offset_y = glGetUniformLocation(self.program, "offset_y")
        self.uniform_w = glGetUniformLocation(self.program, "w")
        self.uniform_h = glGetUniformLocation(self.program, "h")

        self.vbo = glGenBuffers(1)
        self.data = numpy.zeros((10000, 2), dtype=numpy.float32)
        self.data[:,0] = numpy.linspace(-0.5, 0.5, len(self.data))
        for i in xrange(10000):
            self.data[i, 1] = math.sin(180.0 / 3.14 * self.data[i, 0])
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 8 * len(self.data), self.data, GL_STATIC_DRAW)

        glEnable(GL_POINT_SMOOTH)
        glPointSize(6.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

        self.w = w
        self.h = h

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(self.program)

        glUniform1f(self.uniform_scale, self.scale)
        glUniform1f(self.uniform_w, self.w)
        glUniform1f(self.uniform_h, self.h)
        glUniform1f(self.uniform_offset_x, self.offset_x + self.tmp_offset_x)
        glUniform1f(self.uniform_offset_y, self.offset_y + self.tmp_offset_y)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glEnableVertexAttribArray(self.attrib)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        glDrawArrays(GL_LINE_STRIP, 0, len(self.data))
        
        glDrawArrays(GL_POINTS, 0, len(self.data))

    def wheelEvent(self, event):
        self.scale *= math.exp(0.0 - float(event.angleDelta().y()) / 400.0)

        self.update()

    def mousePressEvent(self, event):
        self.start_x = event.x()
        self.start_y = event.y()

    def mouseMoveEvent(self, event):
        delta_x = event.x() - self.start_x
        delta_y = event.y() - self.start_y

        if self.w < self.h:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.w / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.w / self.scale
        else:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.h / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.h / self.scale

        self.update()

    def mouseReleaseEvent(self, event):
        delta_x = event.x() - self.start_x
        delta_y = event.y() - self.start_y

        if self.w < self.h:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.w / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.w / self.scale
        else:
            self.tmp_offset_x = 2.0 * float(delta_x) / self.h / self.scale
            self.tmp_offset_y = -2.0 * float(delta_y) / self.h / self.scale

        self.offset_x += self.tmp_offset_x
        self.offset_y += self.tmp_offset_y
        self.tmp_offset_x = 0.0
        self.tmp_offset_y = 0.0

        self.update()

class Form(QWidget):
    STATE_INIT = 0
    STATE_LOADED = 1
    STATE_STEP1_DONE = 2
    STATE_STEP2_DONE = 3
    STATE_STEP3_DONE = 4
    STATE_STEP4_DONE = 5

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.buttonReset = QPushButton("Reset")
        self.buttonReset.clicked.connect(self.reset)
        self.buttonLoad = QPushButton("Load from file")
        self.buttonLoad.clicked.connect(self.load)
        self.buttonStep1 = QPushButton("Step1")
        self.buttonStep1.clicked.connect(self.step1)
        self.buttonStep2 = QPushButton("Step2")
        self.buttonStep2.clicked.connect(self.step2)
        self.buttonStep3 = QPushButton("Step3")
        self.buttonStep3.clicked.connect(self.step3)
        self.buttonStep4 = QPushButton("Step4")
        self.buttonStep4.clicked.connect(self.step4)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.buttonReset)
        buttonLayout.addWidget(self.buttonLoad)
        buttonLayout.addWidget(self.buttonStep1)
        buttonLayout.addWidget(self.buttonStep2)
        buttonLayout.addWidget(self.buttonStep3)
        buttonLayout.addWidget(self.buttonStep4)

        self.displayWidget = DisplayWidget(self)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.displayWidget)

        self.setLayout(mainLayout)
        self.setWindowTitle("Demo")

        self.setState(Form.STATE_INIT)

    def setState(self, state):
        self.buttonLoad.setEnabled(state == Form.STATE_INIT)
        self.buttonStep1.setEnabled(state == Form.STATE_LOADED)
        self.buttonStep2.setEnabled(state == Form.STATE_STEP1_DONE)
        self.buttonStep3.setEnabled(state == Form.STATE_STEP2_DONE)
        self.buttonStep4.setEnabled(state == Form.STATE_STEP3_DONE)

    def reset(self):
        self.setState(Form.STATE_INIT)
    def load(self):
        self.setState(Form.STATE_LOADED)
    def step1(self):
        self.setState(Form.STATE_STEP1_DONE)
    def step2(self):
        self.setState(Form.STATE_STEP2_DONE)
    def step3(self):
        self.setState(Form.STATE_STEP3_DONE)
    def step4(self):
        self.setState(Form.STATE_STEP4_DONE)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    form = Form()
    form.show()

    sys.exit(app.exec_())