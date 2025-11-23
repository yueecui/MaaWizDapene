class GlobalDataStore:
    _instance = None
    continue_move_count = 0

    def __init__(self):
        self.after_open_chest_entry = "弗德莱戈：打开地图"

    @staticmethod
    def get_instance():
        if not GlobalDataStore._instance:
            GlobalDataStore._instance = GlobalDataStore()
        return GlobalDataStore._instance
