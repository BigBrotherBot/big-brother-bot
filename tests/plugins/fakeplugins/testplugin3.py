from b3.plugin import Plugin


class Testplugin3Plugin(Plugin):
    requiresConfigFile = False
    requiresStorage = ["postgresql"]