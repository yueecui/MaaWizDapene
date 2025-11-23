class GlobalDataStore:
    _instance = None
    continue_move_count = 0
    count = 0
    floar = 0
    index = 0
    chest_count = 0

    def __init__(self):
        self.floor = 0
        self.index = 0

    @staticmethod
    def get_instance():
        if not GlobalDataStore._instance:
            GlobalDataStore._instance = GlobalDataStore()
        return GlobalDataStore._instance
