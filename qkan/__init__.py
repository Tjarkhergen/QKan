# -*- coding: utf-8 -*-
import os
import logging
import tempfile
from datetime import datetime as dt

# noinspection PyPep8Naming
from PyQt4.QtGui import QIcon, QAction, QMenu

# Aufsetzen des Logging-Systems
logger = logging.getLogger('QKan')

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s %(name)s-%(levelname)s: %(message)s')

    # Consolen-Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File-Handler
    dnam = dt.today().strftime("%Y%m%d")
    fnam = os.path.join(tempfile.gettempdir(), 'QKan{}.log'.format(dnam))
    fh = logging.FileHandler(fnam)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Warnlevel des Logging-Systems setzten
    logger.setLevel(logging.DEBUG)

    # Warnlever der Logging-Protokolle setzen
    ch.setLevel(logging.ERROR)
    fh.setLevel(logging.DEBUG)

    logger.info('Initialisierung logger erfolgreich!')
else:
    logger.info('Logger ist schon initialisiert')


def classFactory(iface):  # pylint: disable=invalid-name
    dummy = Dummy(iface)
    return dummy


class Dummy:
    instance = None

    def __init__(self, iface):
        from createunbeffl import application as createunbeffl
        from importdyna import application as importdyna
        from exportdyna import application as exportdyna
        from linkflaechen import application as linkflaechen
        from tools import application as tools
        self.plugins = [
            createunbeffl.CreateUnbefFl(iface),
            importdyna.ImportFromDyna(iface),
            exportdyna.ExportToKP(iface),
            linkflaechen.LinkFl(iface),
            tools.QKanTools(iface)
        ]
        Dummy.instance = self

        # Plugins
        self.instances = []

        # QGIS
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []

        actions = self.iface.mainWindow().menuBar().actions()
        self.menu = None
        for menu in actions:
            if menu.text() == 'QKan':
                self.menu = menu.menu()
                self.menu_action = menu
                break

        self.toolbar = self.iface.addToolBar('QKan')
        self.toolbar.setObjectName('QKan')

    def initGui(self):
        # Create and insert QKan menu after the 3rd menu
        if self.menu is None:
            self.menu = QMenu('QKan', self.iface.mainWindow().menuBar())

            actions = self.iface.mainWindow().menuBar().actions()
            prepend = actions[3]
            self.menu_action = self.iface.mainWindow().menuBar().insertMenu(prepend, self.menu)

        # Calls initGui on all known QKan plugins
        for plugin in self.plugins:
            plugin.initGui()

        self.sort_actions()

    def sort_actions(self):
        # Finally sort all actions
        self.actions.sort(key=lambda x: x.text().lower())
        self.menu.clear()
        self.menu.addActions(self.actions)

    def unload(self):
        from qgis.utils import unloadPlugin
        # Unload all other instances
        for instance in self.instances:
            print('Unloading ', instance.name)
            if not unloadPlugin(instance.name):
                print('Failed to unload plugin!')

        # Remove entries from own menu
        for action in self.menu.actions():
            self.menu.removeAction(action)

        # Remove entries from Plugin menu and toolbar
        for action in self.actions:
            self.iface.removeToolBarIcon(action)

        # Remove the toolbar
        del self.toolbar

        # Remove menu
        self.iface.mainWindow().menuBar().removeAction(self.menu_action)

        # Call unload on all loaded plugins
        for plugin in self.plugins:
            plugin.unload()

    def register(self, instance):
        self.instances.append(instance)

        self.plugins += instance.plugins

    def unregister(self, instance):
        self.instances.remove(instance)

        for plugin in instance.plugins:
            self.plugins.remove(plugin)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.__actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.menu.addAction(action)

        self.actions.append(action)

        return action
