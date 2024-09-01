from django.apps import apps
from django.conf import settings
from django.core.checks import register, Tags, Warning, Error
from django.contrib.auth import get_user_model


# noinspection PyUnusedLocal
@register(Tags.compatibility)
def check_settings(app_configs, **kwargs):
    """ Check that settings are implemented properly
    :param app_configs: a list of apps to be checks or None for all
    :param kwargs: keyword arguments
    :return: a list of errors
    """
    checks = []
    if 'guardian.backends.ObjectPermissionBackend' not in settings.AUTHENTICATION_BACKENDS:
        msg = ("Guardian authentication backend is not hooked. You can add this in settings as eg: "
               "`AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', "
               "'guardian.backends.ObjectPermissionBackend')`.")
        checks.append(Warning(msg, id='guardian.W001'))

    # get the (custom) Group model
    CustomGroup = None
    try:
        CustomGroup = apps.get_model(settings.GUARDIAN_GROUP_MODEL)
    except LookupError:
        msg = "GUARDIAN_GROUP_MODEL refers to model '%s' that has not been registered." % settings.GUARDIAN_GROUP_MODEL
        checks.append(Error(msg, id='guardian.E001'))

    # get the auth.Group model
    Group = None
    try:
        Group = apps.get_model('auth.Group')
    except LookupError:
        msg = "Django auth.Group model has not been registered."
        checks.append(Error(msg, id='guardian.E002'))

    if None not in (Group, CustomGroup) and CustomGroup != Group:
        # check for multiple inheritance to auth.Group
        if CustomGroup._meta.get_field("group_ptr").remote_field.model != Group:
            msg = "GUARDIAN_GROUP_MODEL '%s' must inherit from 'auth.Group'" % settings.GUARDIAN_GROUP_MODEL
            checks.append(Error(msg, id='guardian.E003'))

        from .mixins import GuardianGroupMixin, GuardianUserMixin

        # check if Group model really needs to be monkey patched
        if settings.GUARDIAN_MONKEY_PATCH_GROUP and issubclass(CustomGroup, GuardianGroupMixin):
            msg = "Group model does not need to be monkey patched, as it already inherits from GuardianGroupMixin"
            checks.append(Warning(msg, id='guardian.W002'))
        if not settings.GUARDIAN_MONKEY_PATCH_GROUP and not issubclass(CustomGroup, GuardianGroupMixin):
            msg = "Group model needs to be monkey patched, as it does not inherit from GuardianGroupMixin"
            checks.append(Warning(msg, id='guardian.E004'))

        # check if User model really needs to be monkey patched
        User = get_user_model()
        if settings.GUARDIAN_MONKEY_PATCH_USER and issubclass(User, GuardianUserMixin):
            msg = "User model does not need to be monkey patched, as it already inherits from GuardianUserMixin"
            checks.append(Warning(msg, id='guardian.W003'))
        if not settings.GUARDIAN_MONKEY_PATCH_USER and not issubclass(User, GuardianUserMixin):
            msg = "User model needs to be monkey patched, as it does not inherit from GuardianUserMixin"
            checks.append(Warning(msg, id='guardian.E005'))

    return checks
