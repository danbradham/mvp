'''
Standard Validators
===================
'''
import re
from .exc import ValidationError


def regex(rstr, msg='Does not match regex'):
    r = re.compile(rstr)
    def check_string(value):
        match = r.search(value)
        if not match:
            raise ValidationError(msg)
        return True
    return check_string


def checked(value):
    if not value:
        raise ValidationError('Must be checked')
    return True


def email(value):
    r = re.compile(r'^[\w\d!#$%^&*(){\-_}|]+@[\w\d\-_]+[.][a-z]{2,4}')
    match = r.search(value)
    if not match:
        raise ValidationError('Not a valid email address')
    return True


def required(value):
    if not bool(value):
        raise ValidationError('Missing required field')
    return True


def min_length(num_characters):

    def check_length(value):
        if len(value) < num_characters:
            raise ValidationError('Min Length {0}'.format(num_characters))
    return check_length


def max_length(num_characters):

    def check_length(value):
        if len(value) > num_characters:
            raise ValidationError('Max Length {0}'.format(num_characters))
    return check_length

