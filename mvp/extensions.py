import os
from . import hooks
from .viewport import playblast


def default_handler(data, options):

    _, ext = os.path.splitext(data['filename'])
    is_qt = ext == '.mov'

    kwargs = dict(
        camera=data['camera'],
        state=data['state'],
        width=data['width'],
        height=data['height'],
    )

    if is_qt:
        kwargs.update(
            format='qt',
            compression='H.264',
            filename=data['filename'],
            sound=data['sound'],
        )
    else:
        # PNG settings
        # No sound
        # .png extension removed
        kwargs.update(
            format='image',
            compression='png',
            filename=data['filename'].rsplit('.', 1)[0],
        )

    return playblast(**kwargs)


hooks.register_extension(
    name='h.264',
    ext='.mov',
    handler=default_handler,
)

hooks.register_extension(
    name='png',
    ext='.png',
    handler=default_handler,
)
