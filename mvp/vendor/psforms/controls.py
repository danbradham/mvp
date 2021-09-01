# -*- coding: utf-8 -*-
'''
psforms.controls
================
Wraps standard PySide input widgets providing a unified api for getting and
setting their values. Each control implements :meth:`get_value` and
:meth:`set_value`. A required position argument ``value`` or
``values`` is used to set the default value of the control or in the case
of :class:`ComboBox` and :class:`IntComboBox` a sequence of items to add to
the wrapped QComboBox. In addition each control emits a Signal named `changed`
whenever the value is changed by user interaction.
'''

import os
from copy import deepcopy
from .Qt import QtWidgets, QtCore, QtGui
from . import resource
from .widgets import ScalingImage, IconButton
from .exc import ValidationError


class BaseControl(QtCore.QObject):
    '''Composite Control Object. Used as a base class for all Control Types.
    Subclasses must implement init_widgets, set_value, and get_value methods.
    '''

    changed = QtCore.Signal()
    validate = QtCore.Signal()
    properties = dict(
        valid=True,
    )

    def __init__(self, name, labeled=True, label_on_top=True,
                 default=None, validators=None, *args, **kwargs):
        super(BaseControl, self).__init__(*args, **kwargs)

        self._name = name
        self._labeled = labeled
        self._label_on_top = label_on_top

        self._init_widgets()
        self._init_properties()

        self.validators = validators

        if default:
            self.set_value(default)

    @property
    def name(self):
        '''Property that adjusts the name and label of this control.'''

        return self._name

    @name.setter
    def name(self, value):
        if self.label:
            self.label.setText(self._name)
        self._name = value

    @property
    def labeled(self):
        '''Determines whether this label is visible or hidden.'''

        return self._labeled

    @labeled.setter
    def labeled(self, value):
        self._labeled = value
        if self._labeled:
            self.label.show()
        else:
            self.label.hide()

    @property
    def label_on_top(self):
        '''Determines where the label is drawn, on top or left.'''

        return self._label_on_top

    @label_on_top.setter
    def label_on_top(self, value):
        self._label_on_top = value
        if self._label_on_top:
            self.layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
        else:
            self.layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            self.layout.setSpacing(10)
            if isinstance(self.widget, QtWidgets.QCheckBox):
                self.label.setAlignment(
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                )
            else:
                self.label.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    @property
    def valid(self):
        return self.get_property('valid')

    @valid.setter
    def valid(self, value):
        self.set_property('valid', value)

    def validate(self):
        '''Validate this control'''
        if not self.validators:
            return

        value = self.get_value()

        for v in self.validators:
            try:
                v(value)
            except ValidationError as e:
                self.valid = False
                self.errlabel.setText('*' + str(e))
                return

        if not self.valid:
            self.valid = True
            self.errlabel.setText('')

    def emit_changed(self, *args):
        self.changed.emit()
        self.validate()

    def get_property(self, name):
        '''Used to get the value of a property of this control.'''

        return self.properties[name]

    def set_property(self, name, value):
        '''Used to set the value of a property of this control. Consequently
        sets a Qt Property of the same name on all widgets this control
        manages. Allowing the use of these properties in stylesheets.
        '''

        for w in self.widgets:
            w.setProperty(name, value)
        self.properties[name] = value
        self.update_style()

    def update_style(self):
        '''Used to update the style of all widgets this control manages.'''

        for w in self.widgets:
            w.style().unpolish(w)
            w.style().polish(w)

    def init_widgets(self):
        '''Subclasses must implement this method...

        Used to build the widgets for this control.
        Must return a tuple of widgets, where the first element is the main
        widget used to parent this control to a layout. Additionally users
        must attach their widgets to emit the changed signal of this control
        to properly allow for active form validation.
        '''

        raise NotImplementedError()

    def _init_widgets(self):
        '''Binds the widgets returned by init_widgets to self.widget and
        self.widgets.
        '''

        self.widgets = self.init_widgets()
        self.widget = self.widgets[0]

        self.errlabel = QtWidgets.QLabel()
        self.errlabel.setFixedHeight(14)
        self.errlabel.setProperty('err', True)
        self.errlayout = QtWidgets.QHBoxLayout()
        self.errlayout.addWidget(self.errlabel)

        self.label = QtWidgets.QLabel(self.name)
        if isinstance(self.widget, QtWidgets.QCheckBox):
            self.label.setProperty('clickable', True)

            def _mousePressEvent(event):
                self.widget.toggle()
                self.emit_changed()

            self.label.mousePressEvent = _mousePressEvent
            self.errlabel.setAlignment(QtCore.Qt.AlignRight)

        self.widgets = tuple(list(self.widgets) + [self.label])

        if self.label_on_top:
            self.layout = QtWidgets.QBoxLayout(
                QtWidgets.QBoxLayout.TopToBottom
            )
        elif isinstance(self.widget, QtWidgets.QCheckBox):
            self.layout = QtWidgets.QBoxLayout(
                QtWidgets.QBoxLayout.RightToLeft
            )
        else:
            self.label.setAlignment(
                QtCore.Qt.AlignRight |
                QtCore.Qt.AlignVCenter
            )
            self.layout = QtWidgets.QBoxLayout(
                QtWidgets.QBoxLayout.LeftToRight
            )
            self.layout.setSpacing(10)

        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        self.grid.addWidget(self.widget, 1, 1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.label)
        self.layout.addLayout(self.grid)
        self.vlayout = QtWidgets.QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addStretch()
        self.vlayout.addLayout(self.layout)
        self.vlayout.addLayout(self.errlayout)

        if not self.labeled:
            self.label.hide()

        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.vlayout)

    def _init_properties(self):
        '''Initializes the qt properties on all this controls widgets.'''

        self.properties = deepcopy(self.properties)
        for p, v in self.properties.items():
            self.set_property(p, v)

    def get_value(self):
        '''Subclasses must implement this method...

        Must return the value of this control. Use the widgets you create in
        init_widgets, accessible through the widgets attribute after
        initialization.
        '''

        raise NotImplementedError()

    def set_value(self, value):
        '''Subclasses must implement this method...

        Must set the value of this control. Use the widgets you create in
        init_widgets, accessible through the widgets attribute after
        initialization.
        '''

        raise NotImplementedError()


class SpinControl(BaseControl):

    widget_cls = QtWidgets.QSpinBox

    def __init__(self, name, range=None, *args, **kwargs):
        self.range = range
        super(SpinControl, self).__init__(name, *args, **kwargs)

    def init_widgets(self):
        sb = self.widget_cls(parent=self.parent())
        sb.setFixedHeight(24)
        sb.valueChanged.connect(self.emit_changed)
        if self.range:
            sb.setRange(*self.range)
        return (sb,)

    def get_value(self):
        return self.widget.value()

    def set_value(self, value):
        self.widget.setValue(value)


class Spin2Control(BaseControl):

    widget_cls = QtWidgets.QSpinBox

    def __init__(self, name, range1=None, range2=None, *args, **kwargs):
        self.range1 = range1
        self.range2 = range2
        super(Spin2Control, self).__init__(name, *args, **kwargs)

    def init_widgets(self):

        sb1 = self.widget_cls(parent=self.parent())
        sb1.setFixedHeight(24)
        sb1.valueChanged.connect(self.emit_changed)
        sb2 = self.widget_cls(parent=self.parent())
        sb2.setFixedHeight(24)
        sb2.valueChanged.connect(self.emit_changed)
        if self.range1:
            sb1.setRange(*self.range1)
        if self.range2:
            sb2.setRange(*self.range2)

        w = QtWidgets.QWidget()
        w.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        l = QtWidgets.QHBoxLayout()
        l.setSpacing(10)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(sb1)
        l.addWidget(sb2)
        w.setLayout(l)

        return w, sb1, sb2

    def get_value(self):
        return self.widgets[1].value(), self.widgets[2].value()

    def set_value(self, value):
        self.widgets[1].setValue(value[0])
        self.widgets[2].setValue(value[1])


class IntControl(SpinControl):

    widget_cls = QtWidgets.QSpinBox


class Int2Control(Spin2Control):

    widget_cls = QtWidgets.QSpinBox


class FloatControl(SpinControl):

    widget_cls = QtWidgets.QDoubleSpinBox


class Float2Control(Spin2Control):

    widget_cls = QtWidgets.QDoubleSpinBox


class OptionControl(BaseControl):

    def __init__(self, name, options=None, *args, **kwargs):
        self._init_options = options
        super(OptionControl, self).__init__(name, *args, **kwargs)

    def init_widgets(self):
        c = QtWidgets.QComboBox(parent=self.parent())
        c.activated.connect(self.emit_changed)
        if self._init_options:
            c.addItems(self._init_options)
        return (c,)

    def set_options(self, options):
        self.widget.clear()
        self.widget.addItems(options)

    def get_data(self):
        return self.widget.itemData(
            self.widget.currentIndex(),
            QtCore.Qt.UserRole
        )

    def get_text(self):
        return self.widget.currentText()

    def set_text(self, value):
        self.widget.setCurrentIndex(self.widget.findText(value))

    def get_value(self):
        return self.widget.currentText()

    def set_value(self, value):
        self.widget.setCurrentIndex(self.widget.findText(value))


StringOptionControl = OptionControl


class IntOptionControl(OptionControl):

    def init_widgets(self):

        c = QtWidgets.QComboBox(parent=self.parent())
        c.activated.connect(self.emit_changed)
        return (c,)

    def get_value(self):
        return self.widget.currentIndex()

    def set_value(self, value):
        self.widget.setCurrentIndex(value)


class ButtonOptionControl(BaseControl):

    def __init__(self, name, options, *args, **kwargs):
        self.options = options
        super(ButtonOptionControl, self).__init__(name, *args, **kwargs)

    def init_widgets(self):
        w = QtWidgets.QWidget()
        w.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        l = QtWidgets.QHBoxLayout()
        l.setSpacing(20)
        w.setLayout(l)

        def group_changed(*args):
            self.emit_changed()

        def press_button(index):
            def do_press(*args):
                self.button_group.button(index).setChecked(True)
                self.emit_changed()
            return do_press

        self.button_group = QtWidgets.QButtonGroup()
        self.button_group.buttonClicked.connect(group_changed)

        for i, opt in enumerate(self.options):
            c = QtWidgets.QCheckBox(self.parent())
            if i == 0:
                c.setChecked(True)
            c.setFixedSize(20, 20)

            cl = QtWidgets.QLabel(opt)
            cl.setProperty('clickable', True)
            cl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            cl.mousePressEvent = press_button(i)

            bl = QtWidgets.QHBoxLayout()
            bl.setSpacing(0)
            bl.addWidget(c)
            bl.addWidget(cl)
            self.button_group.addButton(c, i)
            l.addLayout(bl)

        return (w,)

    def get_value(self):
        return self.options[self.button_group.checkedId()]

    def set_value(self, value):

        index = value if isinstance(value, int) else self.options.index(value)
        self.button_group.button(index).setChecked(True)


class IntButtonOptionControl(ButtonOptionControl):

    def get_value(self):
        return self.button_group.checkedId()


class BoolControl(BaseControl):

    def init_widgets(self):
        c = QtWidgets.QCheckBox(parent=self.parent())
        c.setFixedSize(20, 20)
        c.clicked.connect(self.emit_changed)
        return (c, )

    def get_value(self):
        return self.widget.isChecked()

    def set_value(self, value):
        self.widget.setChecked(value)


class StringControl(BaseControl):

    def init_widgets(self):
        le = QtWidgets.QLineEdit(parent=self.parent())
        le.textEdited.connect(self.emit_changed)
        return (le,)

    def get_value(self):
        return self.widget.text()

    def set_value(self, value):
        self.widget.setText(value)


class TextControl(BaseControl):

    def init_widgets(self):
        te = QtWidgets.QTextEdit(parent=self.parent())
        te.textChanged.connect(self.emit_changed)
        return (te,)

    def get_value(self):
        return self.widget.toPlainText()

    def set_value(self, value):
        self.blockSignals(True)
        self.widget.setText(value)
        self.blockSignals(False)


class BrowseControl(BaseControl):

    browse_method = QtWidgets.QFileDialog.getOpenFileName

    def __init__(self, name, caption=None, filters=None, *args, **kwargs):
        super(BrowseControl, self).__init__(name, *args, **kwargs)
        self.caption = caption or name
        self.filters = filters or ["Any files (*)"]

    def init_widgets(self):

        le = QtWidgets.QLineEdit(parent=self.parent())
        le.setProperty('browse', True)
        le.textEdited.connect(self.emit_changed)
        b = IconButton(
            icon=':/icons/browse_hover',
            tip='Browse',
            name='browse_button',
        )
        b.setProperty('browse', True)
        b.clicked.connect(self.browse)

        w = QtWidgets.QWidget(parent=self.parent())
        l = QtWidgets.QGridLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        l.setColumnStretch(0, 1)
        l.addWidget(le, 0, 0)
        l.addWidget(b, 0, 1)
        w.setLayout(l)

        return (w, le, b)

    def get_value(self):
        return self.widgets[1].text()

    def set_value(self, value):
        self.widgets[1].setText(value)

    @property
    def basedir(self):
        line_text = self.get_value()
        if line_text:
            line_dir = os.path.dirname(line_text)
            if os.path.exists(line_dir):
                return line_dir
        return ''

    def browse(self):
        value = self.browse_method(
            self.main_widget,
            caption=self.caption,
            dir=self.basedir)
        if value:
            if self.browse_method is QtWidgets.QFileDialog.getExistingDirectory:
                self.set_value(value)
                return
            self.set_value(value[0])


class FileControl(BrowseControl):

    browse_method = QtWidgets.QFileDialog.getOpenFileName


class FolderControl(BrowseControl):

    browse_method = QtWidgets.QFileDialog.getExistingDirectory


class SaveFileControl(BrowseControl):

    browse_method = QtWidgets.QFileDialog.getSaveFileName


class ImageControl(BaseControl):

    def init_widgets(self):
        w = QtWidgets.QWidget(parent=self.parent())
        i = ScalingImage(parent=w)
        f = FileControl(self.name + '_line', parent=w)
        f.changed.connect(self.emit_changed)
        self.file_control = f

        l = QtWidgets.QVBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(10)
        l.addWidget(i)
        l.addWidget(f.main_widget)
        w.setLayout(l)

        return [w, i] + list(f.widgets)

    def emit_changed(self, *args):
        self.changed.emit()
        self.widgets[1].set_image(self.get_value())

    def get_value(self):
        return self.file_control.get_value()

    def set_value(self, value):
        if QtCore.QFile.exists(value):
            self.file_control.set_value(value)


class ListControl(BaseControl):

    def __init__(self, name, options=None, *args, **kwargs):
        super(ListControl, self).__init__(name, *args, **kwargs)
        if options:
            self.widget.addItems(options)

    def init_widgets(self):
        l = QtWidgets.QListWidget()
        l.itemSelectionChanged.connect(self.emit_changed)
        return (l,)

    def add_item(self, label, icon=None, data=None):
        item_widget = QtWidgets.QListWidgetItem()
        if icon:
            item_widget.setIcon(QtGui.QIcon(icon))
        if data:
            item_widget.setData(QtCore.Qt.UserRole, data)
        self.widget.addItem(item_widget)

    def get_data(self):
        ''':return: Data for selected items in :class:`QtWidgets.QListWidget`
        :rtype: list'''
        items = self.widget.selectedItems()
        items_data = []
        for item in items:
            items_data.append(item.data(QtCore.Qt.UserRole))
        return items_data

    def get_value(self):
        ''':return: Value of the underlying :class:`QtWidgets.QTreeWidget`
        :rtype: str'''

        items = self.widget.selectedItems()
        item_values = []
        for item in items:
            item_values.append(item.text())
        return item_values

    def set_value(self, value):
        '''Sets the selection of the list to the specified value, label or
        index'''

        if isinstance(value, (str, unicode)):
            items = self.widget.findItems(value)
            if items:
                self.widget.setCurrentItem(items[0])
        elif isinstance(value, int):
            self.widget.setCurrentIndex(int)


control_map = {cls.__name__: cls for cls in BaseControl.__subclasses__()}
