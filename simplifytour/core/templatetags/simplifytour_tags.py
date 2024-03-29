import os
from urllib.parse import quote, unquote

from django.utils.safestring import SafeText, mark_safe
from django.core.files.storage import default_storage
from django.core.files import File
from django.conf import settings

from simplifytour.utils.importing import import_dotted_path

from django import template

register = template.Library()


class FileSystemEncodingChanged(RuntimeError):
    def __init__(self):
        msg = ("Access was attempted on a file that contains unicode "
               "characters in its path, but somehow the current locale "
               "does not support utf-8. You may need to set 'LC_ALL' "
               "to a correct value, eg: 'en_US.UTF-8'.")
        RuntimeError.__init__(self, msg)


@register.filter
def richtext_filters(content):
    """
    Takes a value edited via the WYSIWYG editor, and passes it through
    each of the functions specified by the RICHTEXT_FILTERS setting.
    """
    for filter_name in settings.RICHTEXT_FILTERS:
        filter_func = import_dotted_path(filter_name)
        content = filter_func(content)
        if not isinstance(content, SafeText):
            # raise TypeError(
                # filter_name + " must mark it's return value as safe. See "
                # "https://docs.djangoproject.com/en/stable/topics/security/"
                # "#cross-site-scripting-xss-protection")
            import warnings
            warnings.warn(
                filter_name + " needs to ensure that any untrusted inputs are "
                "properly escaped and mark the html it returns as safe. In a "
                "future release this will cause an exception. See "
                "https://docs.djangoproject.com/en/stable/topics/security/"
                "cross-site-scripting-xss-protection",
                FutureWarning)
            content = mark_safe(content)
    return content


@register.simple_tag
def thumbnail(image_url, width, height, upscale=True, quality=95, left=.5,
              top=.5, padding=False, padding_color="#fff"):
    """
    Given the URL to an image, resizes the image using the given width
    and height on the first time it is requested, and returns the URL
    to the new resized image. If width or height are zero then original
    ratio is maintained. When ``upscale`` is False, images smaller than
    the given size will not be grown to fill that size. The given width
    and height thus act as maximum dimensions.
    """

    if not image_url:
        return ""
    try:
        from PIL import Image, ImageFile, ImageOps
    except ImportError:
        return ""

    image_url = unquote(str(image_url)).split("?")[0]
    if image_url.startswith(settings.MEDIA_URL):
        image_url = image_url.replace(settings.MEDIA_URL, "", 1)
    image_dir, image_name = os.path.split(image_url)
    image_prefix, image_ext = os.path.splitext(image_name)
    filetype = {".png": "PNG", ".gif": "GIF"}.get(image_ext.lower(), "JPEG")
    thumb_name = "%s-%sx%s" % (image_prefix, width, height)
    if not upscale:
        thumb_name += "-no-upscale"
    if left != .5 or top != .5:
        left = min(1, max(0, left))
        top = min(1, max(0, top))
        thumb_name = "%s-%sx%s" % (thumb_name, left, top)
    thumb_name += "-padded-%s" % padding_color if padding else ""
    thumb_name = "%s%s" % (thumb_name, image_ext)

    # `image_name` is used here for the directory path, as each image
    # requires its own sub-directory using its own name - this is so
    # we can consistently delete all thumbnails for an individual
    # image, which is something we do in filebrowser when a new image
    # is written, allowing us to purge any previously generated
    # thumbnails that may match a new image name.
    thumb_dir = os.path.join(settings.MEDIA_ROOT, image_dir,
                             settings.THUMBNAILS_DIR_NAME, image_name)
    if not os.path.exists(thumb_dir):
        try:
            os.makedirs(thumb_dir)
        except OSError:
            pass

    thumb_path = os.path.join(thumb_dir, thumb_name)
    thumb_url = "%s/%s/%s" % (settings.THUMBNAILS_DIR_NAME,
                              quote(image_name.encode("utf-8")),
                              quote(thumb_name.encode("utf-8")))
    image_url_path = os.path.dirname(image_url)
    if image_url_path:
        thumb_url = "%s/%s" % (image_url_path, thumb_url)

    try:
        thumb_exists = os.path.exists(thumb_path)
    except UnicodeEncodeError:
        # The image that was saved to a filesystem with utf-8 support,
        # but somehow the locale has changed and the filesystem does not
        # support utf-8.
        raise FileSystemEncodingChanged()
    if thumb_exists:
        # Thumbnail exists, don't generate it.
        return thumb_url
    elif not default_storage.exists(image_url):
        # Requested image does not exist, just return its URL.
        return image_url

    f = default_storage.open(image_url)
    try:
        image = Image.open(f)
    except:
        # Invalid image format.
        return image_url

    image_info = image.info

    # Transpose to align the image to its orientation if necessary.
    # If the image is transposed, delete the exif information as
    # not all browsers support the CSS image-orientation:
    # - http://caniuse.com/#feat=css-image-orientation
    try:
        orientation = image._getexif().get(0x0112)
    except:
        orientation = None
    if orientation:
        methods = {
           2: (Image.FLIP_LEFT_RIGHT,),
           3: (Image.ROTATE_180,),
           4: (Image.FLIP_TOP_BOTTOM,),
           5: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_90),
           6: (Image.ROTATE_270,),
           7: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_270),
           8: (Image.ROTATE_90,)}.get(orientation, ())
        if methods:
            image_info.pop('exif', None)
            for method in methods:
                image = image.transpose(method)

    to_width = int(width)
    to_height = int(height)
    from_width = image.size[0]
    from_height = image.size[1]

    if not upscale:
        to_width = min(to_width, from_width)
        to_height = min(to_height, from_height)

    # Set dimensions.
    if to_width == 0:
        to_width = from_width * to_height // from_height
    elif to_height == 0:
        to_height = from_height * to_width // from_width
    if image.mode not in ("P", "L", "RGBA") \
            and filetype not in ("JPG", "JPEG"):
        try:
            image = image.convert("RGBA")
        except:
            return image_url
    # Required for progressive jpgs.
    ImageFile.MAXBLOCK = 2 * (max(image.size) ** 2)

    # Padding.
    if padding and to_width and to_height:
        from_ratio = float(from_width) / from_height
        to_ratio = float(to_width) / to_height
        pad_size = None
        if to_ratio < from_ratio:
            pad_height = int(to_height * (float(from_width) / to_width))
            pad_size = (from_width, pad_height)
            pad_top = (pad_height - from_height) // 2
            pad_left = 0
        elif to_ratio > from_ratio:
            pad_width = int(to_width * (float(from_height) / to_height))
            pad_size = (pad_width, from_height)
            pad_top = 0
            pad_left = (pad_width - from_width) // 2
        if pad_size is not None:
            pad_container = Image.new("RGBA", pad_size, padding_color)
            pad_container.paste(image, (pad_left, pad_top))
            image = pad_container

    # Create the thumbnail.
    to_size = (to_width, to_height)
    to_pos = (left, top)
    try:
        image = ImageOps.fit(image, to_size, Image.ANTIALIAS, 0, to_pos)
        image = image.save(thumb_path, filetype, quality=quality, **image_info)
        # Push a remote copy of the thumbnail if MEDIA_URL is
        # absolute.
        if "://" in settings.MEDIA_URL:
            with open(thumb_path, "rb") as f:
                default_storage.save(unquote(thumb_url), File(f))
    except Exception:
        # If an error occurred, a corrupted image may have been saved,
        # so remove it, otherwise the check for it existing will just
        # return the corrupted image next time it's requested.
        try:
            os.remove(thumb_path)
        except Exception:
            pass
        return image_url
    return thumb_url
