from __future__ import print_function

from .Qt import QtWidgets, QtCore, QtGui
import math

from .exc import *
from . import resource


class ControlLayout(QtWidgets.QGridLayout):

    def __init__(self, columns=1, parent=None):
        super(ControlLayout, self).__init__(parent)

        self._columns = columns
        self.setContentsMargins(20, 20, 20, 20)
        self.setHorizontalSpacing(10)
        self.setRowStretch(1000, 1)
        self.widgets = []

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, value):
        self._columns = value
        widgets = list(self.widgets)
        for w in widgets:
            self.takeWidget(w)
        for w in widgets:
            self.addWidget(w)

    @property
    def count(self):
        return len(self.widgets)

    def takeWidget(self, widget):
        if widget not in self.widgets:
            return None

        self.widgets.pop(self.widgets.index(widget))
        self.takeAt(self.indexOf(widget))
        return widget

    def addWidget(self, widget):
        count = self.count
        row = math.floor(count / self.columns)
        column = (count % self.columns)
        super(ControlLayout, self).addWidget(widget, row, column)
        self.widgets.append(widget)


class FormWidget(QtWidgets.QWidget):

    def __init__(self, name, columns=1, layout_horizontal=False, parent=None):
        super(FormWidget, self).__init__(parent)

        self.name = name
        self.controls = {}
        self.forms = {}
        self.parent = parent

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        if layout_horizontal:
            self.form_layout = QtWidgets.QBoxLayout(
                QtWidgets.QBoxLayout.LeftToRight
            )
        else:
            self.form_layout = QtWidgets.QBoxLayout(
                QtWidgets.QBoxLayout.TopToBottom
            )
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(0)

        self.control_layout = ControlLayout(columns=columns)
        self.form_layout.addLayout(self.control_layout)
        self.layout.addLayout(self.form_layout)

        self.setProperty('form', True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

    @property
    def valid(self):
        is_valid = []

        for name, control in self.controls.items():
            control.validate()
            is_valid.append(control.valid)

        for name, form in self.forms.items():
            is_valid.append(form.valid)

        return all(is_valid)

    def get_value(self, flatten=False):
        '''Get the value of this forms fields and subforms fields.

        :param flatten: If set to True, return a flattened dict
        '''

        form_data = {}
        for name, control in self.controls.items():
            form_data[name] = control.get_value()

        for name, form in self.forms.items():
            form_value = form.get_value(flatten=flatten)
            if flatten:
                form_data.update(form_value)
            else:
                form_data[name] = form_value

        return form_data

    def set_value(self, strict=True, **data):
        '''Set the value of all the forms subforms and fields. You can pass
        an additional keyword argument strict to False to ignore mismatched
        names and subforms.

        :param strict: raise exceptions for any invalid names in data
        :param data: Field data used to set the values of the form

        usage::

            myform.set_value(
                strict=True,
                **{
                    'strfield': 'ABCDEFG',
                    'intfield': 1,
                    'subform': {
                        'subform_strfield': 'BCDEFGH',
                        'subform_intfield': 2,}},
            )
        '''
        for name, value in data.items():

            if isinstance(value, dict):
                try:
                    self.forms[name].set_value(**value)
                except KeyError:
                    if strict:
                        raise FormNotFound(name + ' does not exist')
                continue

            try:
                self.controls[name].set_value(value)
            except KeyError:
                if strict:
                    raise FieldNotFound(name + ' does not exist')

    def add_header(self, title, description=None, icon=None):
        '''Add a header'''

        self.header = Header(title, description, icon, self)
        self.layout.insertWidget(0, self.header)

    def insert_form(self, index, name, form):
        '''Insert a subform'''

        self.form_layout.insertWidget(index, form)
        self.forms[name] = form
        setattr(self, name, form)

    def add_form(self, name, form):
        '''Add a subform'''

        self.form_layout.addWidget(form)
        self.forms[name] = form
        setattr(self, name, form)

    def add_control(self, name, control):
        '''Add a control'''

        self.control_layout.addWidget(control.main_widget)
        self.controls[name] = control
        setattr(self, name, control)


class FormDialog(QtWidgets.QDialog):

    def __init__(self, widget, *args, **kwargs):
        super(FormDialog, self).__init__(*args, **kwargs)

        self.widget = widget
        self.cancel_button = QtWidgets.QPushButton('&cancel')
        self.accept_button = QtWidgets.QPushButton('&accept')
        self.cancel_button.clicked.connect(self.reject)
        self.accept_button.clicked.connect(self.on_accept)

        self.layout = QtWidgets.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setRowStretch(1, 1)
        self.setLayout(self.layout)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(20, 20, 20, 20)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.accept_button)

        self.layout.addWidget(self.widget, 0, 0)
        self.layout.addLayout(self.button_layout, 2, 0)

    def set_widget(self, widget):
        self.widget = widget
        self.widget.setProperty('groupwidget', True)

        if self.layout.count() == 2:
            self.layout.takeAt(0)

        self.layout.insertWidget(0, self.widget)

    def __getattr__(self, attr):
        try:
            return getattr(self.widget, attr)
        except AttributeError:
            raise AttributeError('FormDialog has no attr: {}'.format(attr))

    def on_accept(self):
        if self.widget.valid:
            self.accept()
        return


class FormGroup(QtWidgets.QWidget):

    toggled = QtCore.Signal(bool)
    after_toggled = QtCore.Signal(bool)

    def __init__(self, name, widget, *args, **kwargs):
        super(FormGroup, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setStretch(1, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.title = QtWidgets.QPushButton(name)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(':/icons/plus'),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off
        )
        icon.addPixmap(
            QtGui.QPixmap(':/icons/minus'),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.title.setIcon(icon)
        self.title.setProperty('grouptitle', True)
        self.title.setCheckable(True)
        self.title.setChecked(True)
        self.title.toggled.connect(self.toggle_collapsed)
        self.layout.addWidget(self.title)

        self.widget = widget
        if isinstance(self.widget, QtWidgets.QWidget):
            self.widget.setProperty('groupwidget', True)
            self.layout.addWidget(self.widget)

    def set_widget(self, widget):
        self.widget = widget
        self.widget.setProperty('groupwidget', True)

        if self.layout.count() == 2:
            self.layout.takeAt(1)

        self.layout.addWidget(self.widget)

    def set_enabled(self, value):
        self.title.blockSignals(True)
        self.title.setChecked(value)
        self.widget.setVisible(value)
        self.title.blockSignals(False)

    def toggle_collapsed(self, collapsed):
        self.toggled.emit(collapsed)
        enabled = self.title.isChecked()
        self.widget.setVisible(enabled)
        self.after_toggled.emit(enabled)

    def __getattr__(self, attr):
        try:
            return getattr(self.widget, attr)
        except AttributeError:
            raise AttributeError('FormDialog has no attr: {}'.format(attr))


class Header(QtWidgets.QWidget):

    def __init__(self, title, description=None, icon=None, parent=None):
        super(Header, self).__init__(parent)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setColumnStretch(1, 1)

        self.setLayout(self.grid)

        self.title = QtWidgets.QLabel(title)
        self.title.setProperty('title', True)
        self.descr = QtWidgets.QLabel(description or 'No Description')
        self.descr.setProperty('description', True)
        if not description:
            self.descr.hide()

        if icon:
            self.descr.setAlignment(
                QtCore.Qt.AlignLeft
                | QtCore.Qt.AlignVCenter
            )
            self.title.setAlignment(
                QtCore.Qt.AlignLeft
                | QtCore.Qt.AlignVCenter
            )
            self.icon = QtWidgets.QLabel()
            self.icon.setPixmap(icon)
            if description:
                self.grid.addWidget(self.icon, 0, 0, 2, 1)
                self.grid.addWidget(self.title, 0, 1)
                self.grid.addWidget(self.descr, 1, 1)
            else:
                self.grid.addWidget(self.icon, 0, 0)
                self.grid.addWidget(self.title, 0, 1)
        else:
            self.descr.setAlignment(QtCore.Qt.AlignCenter)
            self.title.setAlignment(QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.title, 0, 0)
            self.grid.addWidget(self.descr, 1, 0)

        self.setProperty('header', True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self._mouse_button = None
        self._mouse_last_pos = None

    def mousePressEvent(self, event):
        self._mouse_button = event.button()
        super(Header, self).mousePressEvent(event)
        self._window = self.window()

    def mouseMoveEvent(self, event):
        '''Click + Dragging moves window'''

        if self._mouse_button == QtCore.Qt.LeftButton:
            if self._mouse_last_pos:

                p = self._window.pos()
                v = event.globalPos() - self._mouse_last_pos
                self._window.move(p + v)

            self._mouse_last_pos = event.globalPos()

        super(Header, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._mouse_button = None
        self._mouse_last_pos = None
        self._window = None
        super(Header, self).mouseReleaseEvent(event)


class ScalingImage(QtWidgets.QLabel):

    __images = {}

    def __init__(self, image=None, parent=None):
        super(ScalingImage, self).__init__(parent)
        self.images = self.__images
        if not image:
            image = ':/images/noimg'
        self.set_image(image)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)

    def set_image(self, image):
        if image not in self.images:
            if not isinstance(image, QtGui.QImage):
                if not QtCore.QFile.exists(image):
                    return
                self.img = QtGui.QImage(image)
            self.images[image] = self.img
        else:
            self.img = self.images[image]

        self.setMinimumSize(227, 128)
        self.scale_pixmap()
        self.repaint()

    def scale_pixmap(self):
        scaled_image = self.img.scaled(
            self.width(),
            self.height(),
            QtCore.Qt.KeepAspectRatioByExpanding,
            QtCore.Qt.FastTransformation)
        self.pixmap = QtGui.QPixmap(scaled_image)

    def resizeEvent(self, event):
        self.do_resize = True
        super(ScalingImage, self).resizeEvent(event)

    def paintEvent(self, event):
        if self.do_resize:
            self.scale_pixmap()
            self.do_resize = False

        offsetX = -((self.pixmap.width() - self.width()) * 0.5)
        offsetY = -((self.pixmap.height() - self.height()) * 0.5)
        painter = QtGui.QPainter(self)
        painter.drawPixmap(offsetX, offsetY, self.pixmap)


class IconButton(QtWidgets.QPushButton):
    '''A button with an icon.

    :param icon: path to icon file or resource
    :param tip: tooltip text
    :param name: object name
    :param size: width, height tuple (default: (24, 24))
    '''

    def __init__(self, icon, tip, name, size=(26, 26), *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)

        self.setObjectName(name)
        self.setIcon(QtGui.QIcon(icon))
        self.setIconSize(QtCore.QSize(*size))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed)
        self.setFixedHeight(size[0])
        self.setFixedWidth(size[1])
        self.setToolTip(tip)
