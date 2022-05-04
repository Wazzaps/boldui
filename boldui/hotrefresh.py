try:
    import jurigged
    import types


    def make_refresh(server):
        def refresh(self, path):
            self._orig_refresh(path)
            print('BoldUI: Hot refresh!')
            server.refresh_scene()

        return refresh


    def init(server):
        if jurigged.live.registry.precache_activity:
            watcher = jurigged.live.registry.precache_activity[0].__self__
            watcher._orig_refresh = watcher.refresh
            watcher.refresh = types.MethodType(make_refresh(server), watcher)

except ImportError:
    def init(_server):
        pass
