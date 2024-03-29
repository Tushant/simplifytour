from importlib import import_module

from django.apps import apps

def import_dotted_path(path):
    """
    Takes a dotted path to a member name in a module, and returns
    the member after importing it.
    """
    try:
        module_path, member_name = path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, member_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ImportError("Could not import the name: %s: %s" % (path, e))

def get_app_name_list():
    for app in apps.get_app_configs():
        yield app.name