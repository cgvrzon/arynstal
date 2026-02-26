# [STACK-ORPHEUS:CELERY] >>>
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:
    pass
# [STACK-ORPHEUS:CELERY] <<<
