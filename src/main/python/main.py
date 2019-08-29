from fbs_runtime.application_context.PyQt5 import ApplicationContext

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from OpenGL.GL import *
from OpenGL.GLU import *

import sys, os
import time
import struct
import math, random

import numpy as np

# TODO: progress bar (at bottom of GUI?)

class PrinterBar(QWidget):

	def __init__(self):
		super().__init__()

		dcBtn = QPushButton('DISCONNECT')
		#dcBtn.setMaximumWidth(400)
		dcBtn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		dcBtn.setDisabled(True) #TODO

		nameLabel = QLabel('Craitor I.2')
		nameLabel.setAlignment(Qt.AlignHCenter)

		statusLabel = QLabel('STATUS: Connected')
		statusLabel.setAlignment(Qt.AlignHCenter)

		labelLayout = QVBoxLayout()
		labelLayout.setAlignment(Qt.AlignHCenter)
		labelLayout.addWidget(nameLabel)
		labelLayout.addWidget(statusLabel)

		label = QWidget()
		label.setLayout(labelLayout)

		layout = QHBoxLayout()
		layout.setContentsMargins(QMargins())
		layout.addWidget(dcBtn)
		layout.addWidget(label)

		self.setLayout(layout)


class PobDash(QFrame):

	def __init__(self):
		super().__init__()
		self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
		self.setStyleSheet("background-color: cyan")

		self.thumb = QLabel()

		printNameLayout = QVBoxLayout()
		self.statusLabel = QLabel('')
		printNameLayout.addWidget(self.statusLabel)

		self.nameLabel = QLabel('')
		nameFont = QFont()
		nameFont.setPointSize(16)
		nameFont.setLetterSpacing(QFont.PercentageSpacing, 110)
		self.nameLabel.setFont(nameFont)
		printNameLayout.addWidget(self.nameLabel)

		printNamePanel = QWidget()
		printNamePanel.setLayout(printNameLayout)
		printNamePanel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

		self.controlLayout = QHBoxLayout()
		self.controlLayout.setContentsMargins(0, 0, 0, 16)
		printBtn = QPushButton('Print')
		printBtn.setDisabled(True) #TODO
		self.controlLayout.addWidget(printBtn)
		skipBtn = QPushButton('Skip')
		skipBtn.setDisabled(True) #TODO
		self.controlLayout.addWidget(skipBtn)
		self.removeBtn = QPushButton('Remove')
		self.removeBtn.setDisabled(True)
		self.controlLayout.addWidget(self.removeBtn)

		self.extruderTempLabel = QLabel('27.3\u00b0')
		self.extruderTempLabel.setFixedSize(80, 80)
		self.extruderTempLabel.setAlignment(Qt.AlignCenter)
		self.extruderTempLabel.setStyleSheet("background-color: white")
		self.heatbedTempLabel = QLabel('25.9\u00b0')
		self.heatbedTempLabel.setFixedSize(80, 80)
		self.heatbedTempLabel.setAlignment(Qt.AlignCenter)
		self.heatbedTempLabel.setStyleSheet("background-color: white")

		layout = QGridLayout()
		layout.setHorizontalSpacing(20)
		layout.setVerticalSpacing(10)
		layout.setAlignment(Qt.AlignVCenter)
		layout.addWidget(self.thumb, 0, 0, 2, 1)
		layout.addWidget(printNamePanel, 0, 1, Qt.AlignTop)
		layout.addLayout(self.controlLayout, 1, 1, Qt.AlignBottom)
		layout.setColumnStretch(2, 1)
		layout.addWidget(self.extruderTempLabel, 0, 3)
		layout.addWidget(self.heatbedTempLabel, 1, 3)

		self.setLayout(layout)
		self.display(None)

	def display(self, pob, removeCallback=None):
		if pob == None:
			self.thumb.setPixmap(QPixmap())
			self.statusLabel.setText('No Jobs Available.')
			self.nameLabel.setText('')
			for i in range(self.controlLayout.count()):
				self.controlLayout.itemAt(i).widget().setDisabled(True)
				self.controlLayout.itemAt(i).widget().setVisible(False)
			return

		self.thumb.setPixmap(pob['thumb'].scaled(180, 180, Qt.KeepAspectRatio))

		if pob['status'] == 'P':
			self.statusLabel.setText('Current Print:')
		else:
			self.statusLabel.setText('Selected Job:')
		self.nameLabel.setText(pob['fileUrl'])

		for i in range(self.controlLayout.count()):
				self.controlLayout.itemAt(i).widget().setVisible(True)
		if removeCallback is not None:
			self.removeBtn.setDisabled(False)
			self.removeBtn.disconnect()
			self.removeBtn.released.connect(removeCallback)
		else:
			self.removeBtn.setDisabled(True)


class PobTabs(QTabWidget):

	def __init__(self, pobDash):
		super().__init__()
		self.addTab(self.buildQueuePage(), 'QUEUE (0)')
		self.addTab(self.buildLibraryPage(), 'LIBRARY')
		self.addTab(self.buildHistoryPage(), 'HISTORY')

		self.pobDashRef = pobDash

		self.queue = []
		self.activePob = -1

	def setActivePob(self, index):
		for i in range(len(self.queue)):
			if i == index:
				self._queueLayout.itemAt(i).widget().setStyleSheet("background-color: cyan")
			else:
				self._queueLayout.itemAt(i).widget().setStyleSheet("background-color: white")
		self.activePob = index
		if self.activePob == -1:
			self.pobDashRef.display(None)
		else:
			self.pobDashRef.display(self.queue[self.activePob], self.removeActivePob)

	def addToQueue(self, pob):
		self.queue.append(pob)
		self._queueLayout.addWidget(self.buildPobEntry(pob))
		self.tabBar().setTabText(0, f'QUEUE ({len(self.queue)})')
		self.removeBtn.setDisabled(False)
		if len(self.queue) == 1:
			self.setActivePob(0)

	def removeActivePob(self):
		del self.queue[self.activePob]
		self._queueLayout.itemAt(self.activePob).widget().deleteLater()
		self._queueLayout.removeWidget(self._queueLayout.itemAt(self.activePob).widget())
		self.tabBar().setTabText(0, f'QUEUE ({len(self.queue)})')
		if len(self.queue) == 0:
			self.setActivePob(-1)
			self.removeBtn.setDisabled(True)
		else:
			self.setActivePob(max(self.activePob - 1, 0))

	def buildPobEntry(self, pob):
		layout = QGridLayout()
		layout.setHorizontalSpacing(20)
		layout.setVerticalSpacing(0)

		thumb = QLabel()
		thumb.setPixmap(pob['thumb'].scaled(80, 80, Qt.KeepAspectRatio))
		layout.addWidget(thumb, 0, 0, 2, 1)

		name = QLabel(pob['fileUrl'])
		nameFont = QFont()
		nameFont.setPointSize(16)
		nameFont.setLetterSpacing(QFont.PercentageSpacing, 110)
		name.setFont(nameFont)
		layout.addWidget(name, 0, 1, Qt.AlignBottom)
		layout.setRowStretch(0, 3)

		if pob['status'] == 'P':
			status = QLabel('STATUS: Printing...')
		elif pob['status'] == 'Q':
			status = QLabel('STATUS: Queued to Print')
		else:
			status = QLabel('STATUS: Unknown')
		statusFont = QFont()
		statusFont.setPointSize(10)
		status.setFont(statusFont)
		layout.addWidget(status, 1, 1, Qt.AlignTop)
		layout.setRowStretch(1, 2)
		layout.setColumnStretch(1, 1)
		
		def handleClick(widget):
			self.setActivePob(self.queue.index(widget))
		class Entry(QFrame):
			def __init__(self):
				super().__init__()
				self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
				self.setLayout(layout)
				self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
			def mouseReleaseEvent(self, evt):
				handleClick(pob)
		return Entry()

	def buildQueuePage(self):
		editBtn = QPushButton('Edit')
		editBtn.setDisabled(True) #TODO
		exportBtn = QPushButton('Export')
		exportBtn.setDisabled(True) #TODO
		copyBtn = QPushButton('Copy')
		copyBtn.setDisabled(True) #TODO
		self.removeBtn = QPushButton('Remove')
		self.removeBtn.released.connect(self.removeActivePob)

		controlLayout = QHBoxLayout()
		controlLayout.addWidget(editBtn)
		controlLayout.addStretch(1)
		controlLayout.addWidget(exportBtn)
		controlLayout.addWidget(copyBtn)
		controlLayout.addWidget(self.removeBtn)
		controlLayout.addWidget(QComboBox())

		controlPane = QWidget()
		controlPane.setLayout(controlLayout)

		self._queueLayout = QVBoxLayout()
		self._queueLayout.setAlignment(Qt.AlignTop)

		queuePane = QWidget()
		queuePane.setLayout(self._queueLayout)

		scrollArea = QScrollArea();
		scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		scrollArea.setWidget(queuePane);
		scrollArea.setWidgetResizable(True)

		queuePageLayout = QVBoxLayout()
		queuePageLayout.addWidget(controlPane)
		queuePageLayout.addWidget(scrollArea)

		queuePage = QWidget()
		queuePage.setLayout(queuePageLayout)
		return queuePage

	def buildLibraryPage(self):
		return QWidget()

	def buildHistoryPage(self):
		return QWidget()

class RenderPane(QOpenGLWidget):

	def __init__(self):
		super().__init__()

		self.bgColor = QColor('gray')
		self.setFocusPolicy(Qt.ClickFocus)
		#self.setFixedSize(500, 500)

		self.rx = 0
		self.ry = 0
		self.shiftPressed = False
		self.zoom = -100

		self.center = None
		self.S = None
		self.queueFit = False

	def renderSTL(self, data):
		self.stl = data
		header = data['header']
		tris = data['tris']
		bounds = data['bounds']

		self.center = (
			(bounds[0][0] + bounds[1][0]) / 2,
			(bounds[0][1] + bounds[1][1]) / 2,
			(bounds[0][2] + bounds[1][2]) / 2
		)

		pos = []
		for tri in tris:
			pos += [
				tri.v1[0], tri.v1[1], tri.v1[2],
				tri.v2[0], tri.v2[1], tri.v2[2],
				tri.v3[0], tri.v3[1], tri.v3[2]
			]
		col = computeTriColors(tris)

		vbo_p, vbo_c = glGenBuffer(2)
		glBindBuffer(GL_ARRAY_BUFFER, vbo_p)
		glBufferData(GL_ARRAY_BUFFER, len(pos) * 4, pos, GL_STATIC_DRAW)
		glBindBuffer(GL_ARRAY_BUFFER, 0)

		glBindBuffer(GL_ARRAY_BUFFER, vbo_c)
		glBufferData(GL_ARRAY_BUFFER, len(col) * 4, col, GL_DYNAMIC_DRAW)
		glBindBuffer(GL_ARRAY_BUFFER, 0)

		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)


		glEnableVertexAttribArray(1)



		self.queueFit = True

	def computeTriColors(self, tris):
		t = self.rx * math.pi / 180
		localLight = np.array([1, math.cos(t) - math.sin(t), math.cos(t) + math.sin(t)]) / math.sqrt(3)
		col = []
		for tri in tris:
			sat = (1 - np.dot(np.array(tri.normal), localLight)) / 2
			col += [0.0, sat, 0.0] * 3

	def initializeGL(self):
		glClearColor(self.bgColor.redF(), self.bgColor.greenF(), self.bgColor.blueF(), self.bgColor.alphaF())

		glEnable(GL_CULL_FACE)
		glCullFace(GL_FRONT)

		glEnable(GL_DEPTH_TEST)
		glDepthFunc(GL_LESS)
		'''
		self.fbo = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
		print(glCheckFramebufferStatus(GL_FRAMEBUFFER))

		tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width(), self.height(), 0, GL_RGB, GL_FLOAT, tex)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
		glBindTexture(GL_TEXTURE_2D, 0)
		print(glCheckFramebufferStatus(GL_FRAMEBUFFER))
		glBindFramebuffer(GL_FRAMEBUFFER, 0)
		'''




		'''
		self.tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.tex)
		glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGB, self.width(), self.height(), GL_TRUE)
		glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, 0)

		self.rb = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, self.rb)
		glRenderbufferStorageMultisample(GL_RENDERBUFFER, 4, GL_DEPTH24_STENCIL8, self.width(), self.height())
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		self.fbo = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.tex, 0)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rb)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rb)
		'''

			
	def paintGL(self):
		#glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

		if self.queueFit:
			self.queueFit = True
			self.S = 5
			proj = glGetDoublev(GL_PROJECTION_MATRIX)
			vp = glGetIntegerv(GL_VIEWPORT)
			w2  = self.width() / 2
			h2 = self.height() / 2
			for _ in range(5):
				glMatrixMode(GL_MODELVIEW)
				glLoadIdentity()
				gluLookAt(
					-30*self.S, -70*self.S, 20*self.S,
					0, 0, 0,
					0, 0, 1
				)
				glRotatef(self.rx, 1, 0, 0)
				glTranslatef(-self.center[0], -self.center[1], -self.center[2])

				model = glGetDoublev(GL_MODELVIEW_MATRIX)
				ax = ay = 0
				for i in (0, 1):
					for j in (0, 1):
						for k in (0, 1):
							x, y, _ = gluProject(self.bounds[i][0], self.bounds[j][1], self.bounds[k][2], model, proj, vp)
							ax = max(ax, abs(x - w2))
							ay = max(ay, abs(y - h2))
				
				self.S *= max(ax / w2, ay / h2)

		#glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glClear(GL_COLOR_BUFFER_BIT)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(
			-30 * self.S, -70 * self.S, 20 * self.S,
			0, 0, 0,
			0, 0, 1
		)
		glRotatef(self.rx, 1, 0, 0)
		glTranslatef(-self.center[0], -self.center[1], -self.center[2])

		if len(self.tris) == 0:
			return

		start = time.time()
		glEnableClientState(GL_VERTEX_ARRAY)
		glEnableClientState(GL_COLOR_ARRAY)
		glVertexPointer(3, GL_FLOAT, 0, self.v)
		glColorPointer(3, GL_FLOAT, 0, self.c)
		glDrawArrays(GL_TRIANGLES, 0, 3*len(self.tris))
		glDisableClientState(GL_VERTEX_ARRAY)
		glDisableClientState(GL_COLOR_ARRAY)
		print(time.time() - start)

		edge = 20
		fightingOffset = 0.1
		glColor3f(0.6, 0.6, 0.6)
		glBegin(GL_TRIANGLE_STRIP)
		glVertex3f(self.bounds[1][0] + edge, self.bounds[0][1] - edge, -fightingOffset)
		glVertex3f(self.bounds[0][0] - edge, self.bounds[0][1] - edge, -fightingOffset)
		glVertex3f(self.bounds[1][0] + edge, self.bounds[1][1] + edge, -fightingOffset)
		glVertex3f(self.bounds[0][0] - edge, self.bounds[1][1] + edge, -fightingOffset)
		glEnd()

		# Draw bounding box
		glColor3f(0.0, 0.0, 1.0)
		glBegin(GL_LINE_LOOP)
		glVertex3f(self.bounds[0][0], self.bounds[0][1], self.bounds[0][2])
		glVertex3f(self.bounds[1][0], self.bounds[0][1], self.bounds[0][2])
		glVertex3f(self.bounds[1][0], self.bounds[1][1], self.bounds[0][2])
		glVertex3f(self.bounds[0][0], self.bounds[1][1], self.bounds[0][2])
		glEnd()

		glBegin(GL_LINE_LOOP)
		glVertex3f(self.bounds[0][0], self.bounds[0][1], self.bounds[1][2])
		glVertex3f(self.bounds[1][0], self.bounds[0][1], self.bounds[1][2])
		glVertex3f(self.bounds[1][0], self.bounds[1][1], self.bounds[1][2])
		glVertex3f(self.bounds[0][0], self.bounds[1][1], self.bounds[1][2])
		glEnd()

		glBegin(GL_LINES)
		glVertex3f(self.bounds[0][0], self.bounds[0][1], self.bounds[0][2])
		glVertex3f(self.bounds[0][0], self.bounds[0][1], self.bounds[1][2])

		glVertex3f(self.bounds[1][0], self.bounds[0][1], self.bounds[0][2])
		glVertex3f(self.bounds[1][0], self.bounds[0][1], self.bounds[1][2])

		glVertex3f(self.bounds[1][0], self.bounds[1][1], self.bounds[0][2])
		glVertex3f(self.bounds[1][0], self.bounds[1][1], self.bounds[1][2])

		glVertex3f(self.bounds[0][0], self.bounds[1][1], self.bounds[0][2])
		glVertex3f(self.bounds[0][0], self.bounds[1][1], self.bounds[1][2])
		glEnd()

		'''
		glBindFramebuffer(GL_READ_FRAMEBUFFER, self.fbo)
		glReadBuffer(GL_COLOR_ATTACHMENT0)
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
		glDrawBuffer(GL_BACK)
		glBlitFramebuffer(0, 0, self.width(), self.height(), 0, 0, self.width(), self.height(), GL_COLOR_BUFFER_BIT, GL_NEAREST)
		'''

	def resizeGL(self, width, height):
		glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
		glViewport (0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(45, width / height, 0.01, 5_000.0)

	def mousePressEvent(self, evt):
		self.pressPos = self.pos = evt.pos()

	def mouseMoveEvent(self, evt):
		pos = evt.pos()
		if self.shiftPressed:
			self.zoom += (pos.y() - self.pos.y()) * 0.1
		else:
			self.rx = pos.x() - self.pressPos.x()
			self.ry = pos.y() - self.pressPos.y()
		self.pos = pos
		self.update()

	def keyPressEvent(self, evt):
		if evt.key() == Qt.Key_Shift:
			self.shiftPressed = True
		super().keyPressEvent(evt)

	def keyReleaseEvent(self, evt):
		if evt.key() == Qt.Key_Shift:
			self.shiftPressed = False
			self.pressPos = self.pos
		super().keyReleaseEvent(evt)



class UI(QMainWindow):
	size = (1600, 900)
	uid = 0

	def __init__(self, testImg):
		super().__init__()
		self.testImg = testImg

		self.setWindowTitle('Craitor GUI')
		self.setMenuBar(self.buildMenuBar())
		self.setCentralWidget(self.buildContentPane())
		self.statusBar().showMessage('Status bar message...')

		self.queue = []

		desktop = QApplication.desktop();
		self.setGeometry(
			(desktop.width() - UI.size[0]) // 2,
			(desktop.height() - UI.size[1]) // 2,
			UI.size[0], UI.size[1]
		)
		self.show()

	def buildMenuBar(self):
		menuBar = QMenuBar()
		fileMenu = menuBar.addMenu('File')

		importAction = fileMenu.addAction('Import')
		importAction.triggered.connect(self._import)

		testAction = fileMenu.addAction('Test')
		testAction.triggered.connect(self._test)
		
		exitAction = fileMenu.addAction('Exit')
		exitAction.triggered.connect(qApp.quit)
		
		fileMenu.insertSeparator(exitAction)
		
		return menuBar

	def buildContentPane(self):
		self.printerBar = PrinterBar()
		self.pobDash = PobDash()
		self.pobTabs = PobTabs(self.pobDash)

		leftLayout = QVBoxLayout()
		leftLayout.addWidget(self.printerBar)
		leftLayout.addWidget(self.pobDash)
		leftLayout.addWidget(self.pobTabs)
		leftPane = QWidget()
		leftPane.setLayout(leftLayout)

		self.renderPane = RenderPane()

		midLayout = QVBoxLayout()
		midLayout.addWidget(self.renderPane)
		midPane = QWidget()
		midPane.setStyleSheet('background-color: lightgray')
		midPane.setLayout(midLayout)

		rightLayout = QVBoxLayout()
		rightPane = QWidget()
		rightPane.setStyleSheet('background-color: lightgray')
		rightPane.setLayout(rightLayout)

		contentLayout = QHBoxLayout()
		contentLayout.addWidget(leftPane, 1)
		contentLayout.addWidget(midPane, 1)
		contentLayout.addWidget(rightPane, 1)

		contentPane = QWidget()
		contentPane.setLayout(contentLayout)
		return contentPane

	def _import(self):
		fileNames = QFileDialog.getOpenFileNames(self, 'Select model file(s)', '.', 'STL Files (*.stl);;All Files (*.*)')[0]
		if len(fileNames) == 0:
			return

		if len(fileNames) > 1:
			print('INFO: Batch STL import not yet supported.')

		class Tri():
			def __init__(self, data):
				self.normal = np.array(data[0:3])
				self.v1 = np.array(data[3:6])
				self.v2 = np.array(data[6:9])
				self.v3 = np.array(data[9:12])
				self.attrib = data[12]
			def __str__(self):
				return  ('-- Tri:\n'
						f'\tNormal: ({self.normal[0]:.3f}, {self.normal[1]:.3f}, {self.normal[2]:.3f})\n'
						f'\tV1:     ({self.v1[0]:.3f}, {self.v1[1]:.3f}, {self.v1[2]:.3f})\n'
						f'\tV2:     ({self.v2[0]:.3f}, {self.v2[1]:.3f}, {self.v2[2]:.3f})\n'
						f'\tV3:     ({self.v3[0]:.3f}, {self.v3[1]:.3f}, {self.v3[2]:.3f})\n'
						f'\tAttrib: {self.attrib}')
			def min(self):
				return np.array([self.v1, self.v2, self.v3]).min(axis=0)
			def max(self):
				return np.array([self.v1, self.v2, self.v3]).max(axis=0)

		with open(fileNames[0], 'rb') as f:
			header = struct.unpack('80s', f.read(80))[0].decode('utf-8').rstrip('\x00')
			numTriangles = struct.unpack('<I', f.read(4))[0]
			print(f"Importing {numTriangles} triangles...")
			tris = []
			for _ in range(numTriangles):
				tri = f.read(50)
				if not tri:
					break
				tris.append( Tri(struct.unpack('<12fH', tri)) )

		bounds = (
			np.array([tri.min() for tri in tris]).min(axis=0).tolist(),
			np.array([tri.max() for tri in tris]).max(axis=0).tolist()
		)
		print("Imported.")

		pob = {'fileUrl': os.path.basename(fileNames[0]), 'thumb': self.testImg, 'status': ('Q', 'P')[len(self.pobTabs.queue) == 0], 'UID': UI.uid}
		UI.uid += 1
		self.pobTabs.addToQueue(pob)

		self.renderPane.renderSTL({'header': header, 'tris': tris, 'bounds': bounds})

	def _test(self):
		pob = {'fileUrl': 'Bulba.stl', 'thumb': self.testImg, 'status': ('Q', 'P')[len(self.pobTabs.queue) == 0], 'UID': UI.uid}
		UI.uid += 1
		self.pobTabs.addToQueue(pob)


if __name__ == '__main__':
	appctxt = ApplicationContext()
	appctxt.app.setStyle('fusion')

	testImg = QPixmap(appctxt.get_resource('bulba.jpg'))
	ui = UI(testImg)

	sys.exit(appctxt.app.exec_())