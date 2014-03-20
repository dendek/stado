import os
from stado import plugins
from tests.plugins import TestPlugin


class TestMustache(TestPlugin):
    """
    Plugin mustache
    """

    def setUp(self):
        super().setUp()
        self.plugin = plugins.load_plugin('mustache')()

    # supported types

    def test_string(self):
        """should substitute using string"""
        x = self.plugin.render_string('{{ a }}', context={'a': 'hello'})
        self.assertEqual('hello', x)

    def test_int(self):
        """should substitute using int"""
        x = self.plugin.render_string('{{ a }}', context={'a': 1})
        self.assertEqual('1', x)

    def test_function(self):
        """should substitute using result of called function"""

        def hello():
            return 'function'

        x = self.plugin.render_string('{{ a }}', context={'a': hello})
        self.assertEqual('function', x)

    def test_object(self):
        """should substitute using object attributes"""

        class hello:
            x = 2

        x = self.plugin.render_string('{{ a.x }}', context={'a': hello()})
        self.assertEqual('2', x)

    def test_item(self):
        """should substitute using item"""

        item = self.site.load('basic.html')
        item.context['b'] = 'badger'
        x = self.plugin.render_string('{{ a.source }}', context={'a': item})
        self.assertEqual('{{ title }}', x)
        x = self.plugin.render_string('{{ a.context.b }}', context={'a': item})
        self.assertEqual('badger', x)

    # loading

    def test_plugin_from_string(self):
        """can be loaded using plugins name"""

        self.site.build('basic.html', 'mustache', context={'title': 'hello'})
        self.assertTrue(os.path.exists('basic.html'))
        with open('basic.html') as page:
            self.assertEqual('hello', page.read())