# -*- coding: utf-8 -*-
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from .Qt import QtWidgets, QtCore, QtGui

from .fields import FieldType, type_map, field_map
from .widgets import FormDialog, FormWidget, FormGroup
from .utils import Ordered, itemattrgetter


class FormMetaData(object):

    defaults = dict(
        title='No Title',
        description=None,
        icon=None,
        header=False,
        columns=1,
        labeled=True,
        labels_on_top=True,
        layout_horizontal=False,
        subforms_as_groups=False,
    )

    def __init__(self, **kwargs):
        self.__dict__.update(self.defaults)
        self.__dict__.update(kwargs)


class Form(Ordered):

    meta = FormMetaData()
    _max_width = None

    @classmethod
    def fields(cls):
        '''Returns FieldType objects in sorted order'''

        cls_fields = []
        for name, attr in cls.__dict__.items():
            if issubclass(attr.__class__, FieldType):
                cls_fields.append((name, attr))
        return sorted(cls_fields, key=itemattrgetter(1, '_order'))

    @classmethod
    def forms(cls):
        '''Returns Form objects in sorted order'''

        cls_forms = []
        for name, attr in cls.__dict__.items():
            if issubclass(attr.__class__, Form):
                cls_forms.append((name, attr))
        return sorted(cls_forms, key=itemattrgetter(1, '_order'))

    @classmethod
    def max_width(cls):
        if not cls._max_width:
            # Get the width of the maximum length label
            _max_label = max([y.nice_name for x, y in cls.fields()], key=len)
            _label = QtWidgets.QLabel(_max_label)
            cls._max_width = _label.sizeHint().width() + 20
        return cls._max_width

    @classmethod
    def _create_controls(cls):
        '''Create and return controls from Field objects.'''

        controls = OrderedDict()

        for name, field in cls.fields():
            control = field.create()
            control.setObjectName(name)
            if field.labeled is None:
                control.labeled = cls.meta.labeled
            if field.label_on_top is None:
                control.label_on_top = cls.meta.labels_on_top
            control.label.setFixedWidth(cls.max_width())
            if not control.label_on_top:
                control.errlayout.insertSpacing(0, cls.max_width() + 12)
            controls[name] = control

        return controls

    @classmethod
    def as_widget(cls, parent=None):
        '''Get this form as a widget'''

        form_widget = FormWidget(
            cls.meta.title,
            cls.meta.columns,
            cls.meta.layout_horizontal,
            parent=parent)

        if cls.meta.header:
            form_widget.add_header(
                cls.meta.title,
                cls.meta.description,
                cls.meta.icon
            )

        if cls.fields():
            controls = cls._create_controls()
            for name, control in controls.items():
                form_widget.add_control(name, control)

        for name, form in cls.forms():
            if cls.meta.subforms_as_groups:
                form_widget.add_form(name, form.as_group(form_widget))
            else:
                form_widget.add_form(name, form.as_widget(form_widget))

        return form_widget

    @classmethod
    def as_group(cls, parent=None):

        widget = cls.as_widget()
        group = FormGroup(widget.name, widget, parent=parent)
        return group

    @classmethod
    def as_dialog(cls, frameless=False, dim=False, parent=None):
        '''Get this form as a dialog'''

        dialog = FormDialog(cls.as_widget(), parent=parent)
        dialog.setWindowTitle(cls.meta.title)
        dialog.setWindowIcon(QtGui.QIcon(cls.meta.icon))

        window_flags = dialog.windowFlags()
        if frameless:
            window_flags |= QtCore.Qt.FramelessWindowHint
        dialog.setWindowFlags(window_flags)

        if dim:  # Dim all monitors when showing the dialog
            def _bg_widgets():
                qapp = QtWidgets.QApplication.instance()
                desktop = qapp.desktop()
                screens = desktop.screenCount()
                widgets = []

                for i in range(screens):
                    geo = desktop.screenGeometry(i)
                    w = QtWidgets.QWidget()
                    w.setGeometry(geo)
                    w.setStyleSheet('QWidget {background:black}')
                    w.setWindowOpacity(0.3)
                    widgets.append(w)

                def show():
                    for w in widgets:
                        w.show()

                def hide():
                    for w in widgets:
                        w.hide()

                return show, hide

            old_exec = dialog.exec_
            old_show = dialog.show

            def _exec_(*args, **kwargs):
                bgshow, bghide = _bg_widgets()
                bgshow()
                result = old_exec(*args, **kwargs)
                bghide()
                return result

            def _show(*args, **kwargs):
                bgshow, bghide = _bg_widgets()
                bgshow()
                result = old_show(*args, **kwargs)
                bghide()
                return result

            dialog.exec_ = _exec_
            dialog.show = _show

        return dialog


def generate_form(name, fields, **metadata):
    '''Generate a form from a name and a list of fields.'''

    metadata.setdefault('title', name.title())

    bases = (Form,)
    attrs = {'meta': FormMetaData(**metadata)}
    for field in fields:
        if field['type'] not in type_map:
            raise Exception('Invalid field type %s', field['type'])

        field_type = type_map[field['type']]
        name = field.pop('name')
        label = field.pop('label', name)
        form_field = field_type(label, **field)
        attrs[name] = form_field

    return type(name, bases, attrs)
