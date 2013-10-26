import os
import re
import urllib.request
from .cache import ShelveCache

# TODO: comments

class ItemTypes:
    """
    Storing content type models.

    """

    def __init__(self, models=None):

        self.models = {}

        if models:
            for i in models: self.set(**i)

    def __call__(self, extension):
        return self.get(extension)

    def get(self, extension):

        # Try to get type model by extension.

        if extension in self.models:
            return self.models[extension]

        # Try to get default model.

        if None in self.models:
            return self.models[None]

        raise KeyError('Default content type model not found!')


    def set(self, extension, loaders, renderers, deployers):

        self.models[extension] = {
            'extension': extension,
            'loaders': loaders,
            'renderers': renderers,
            'deployers': deployers,
        }




class ItemCache:

    def __init__(self, cache):
        self.cache = cache
        self.ids = []

    def __iter__(self):
        for i in self.ids[:]:
            yield self.cache.get(i)

    def save(self, content):
        self.ids.append(content.source)
        self.cache.save(content.source, content)

    def load(self, content_id):
        return self.cache.load(content_id)

    def clear(self):
        self.cache.clear()




class ItemManager:
    """Group objects used to manage items, for example items cache, loaders etc."""

    def __init__(self, loaders, types, cache):

        self.ids = []

        self.loaders = loaders
        self.types = ItemTypes(types)
        self.cache = ItemCache(cache)




class SiteItem(dict):
    """
    Represents thing used to create site. For example site source files.
    """

    def __init__(self, source, output, path=None):
        """
        Args:
            source: Item is recognized by source property. For example controllers
                use this.
            output: Path in output directory, where item will be written.
            path: Optionally full path to file which was used to create item.

        """

        # Absolute path to file which was used to create item for example: "a/b.html"
        self.path = path

        # Item is recognized by controllers using this property.
        self.source = source

        # Item content.
        self.data = None

        # Default output path set by item loader.
        self.default_output = output
        self.output = output
        # Title of output file, for example: 'b.html'
        self.filename = os.path.split(self.default_output)[1]

        # Stores objects which are used to generate and save item content.
        self.loaders = []
        self.renderers = []
        self.deployers = []


    # Properties.

    @property
    def content(self):
        return self.data
    @content.setter
    def content(self, value):
        self.data = value

    @property
    def metadata(self):
        """Metadata dict, for example used during content rendering."""
        return self
    @metadata.setter
    def metadata(self, value):
        self.clear()
        self.update(value)

    @property
    def url(self):
        """Item will be available using this url."""

        url_path = urllib.request.pathname2url(self.output)
        # Url should starts with leading slash.
        if not url_path.startswith('/'):
            url_path = '/' + url_path

        return url_path

    @url.setter
    def url(self, value):
        """Set new item url."""

        keywords = re.findall("(:[a-zA-z]*)", value)
        destination = os.path.normpath(value)

        items = {
            'path': os.path.split(self.default_output)[0],
            'filename': self.filename,
            'name': os.path.splitext(self.filename)[0],
            'extension': os.path.splitext(self.filename)[1][1:],
        }

        for key in keywords:
            # :filename => filename
            if key[1:] in items:
                destination = destination.replace(key, str(items[key[1:]]))

        #//home/a.html => home/a.html
        self.output = destination.lstrip(os.sep)


    # Methods.

    def is_page(self):
        """Returns True if item is a page."""
        if self.output.endswith('.html'):
            return True


    def set_type(self, type):
        """Sets item loaders, renderers and deployer. Also sets item url using
        deployer url pattern."""

        # For example: "html"
        self.type = type['extension']

        # Lists.
        self.loaders = type['loaders']
        self.renderers = type['renderers']
        # Deployer object.
        self.deployer = type['deployers']
        print(self.deployer)

        if self.deployer.url:
            self.url = self.deployer.url


    def dump(self):
        """Returns new dict with item metadata."""

        i = {}
        i.update(self)
        return i


    # Loading , rendering, deploying.

    def load(self):
        """Load content metadata and data using each loader."""

        for loader in self.loaders:
            if callable(loader):
                print(loader)
                data, metadata = loader(self.data)
            else:
                data, metadata = loader.load(self.data)

            self.data = data
            self.metadata = metadata


    def render(self):
        """Renders content data using each renderer. After each rendering previous
        data is overwritten with new rendered one."""

        for renderer in self.renderers:
            if callable(renderer):
                self.data = renderer(self.data, self.metadata.dump())
            else:
                self.data = renderer.render(self.data, self.metadata.dump())


    def deploy(self, path):
        """Writes page to output directory in given path"""

        self.deployer.deploy(self, os.path.join(path, self.output))
