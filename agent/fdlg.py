from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from store import GlobalDataStore

ROI_MAP = {
    1: {
        1: {"roi": [239, 476, 240, 471], "arrow": None},
        2: {"roi": [0, 513, 246, 429], "arrow": "Left"},
        3: {"roi": [8, 229, 339, 297], "arrow": None},
        4: {"roi": [366, 235, 334, 290], "arrow": None},
        5: {"roi": [473, 516, 243, 432], "arrow": "Right"},
        99: {"roi": [335, 229, 56, 56], "arrow": None},
    },
    2: {
        1: {"roi": [10, 268, 258, 210], "arrow": None},
        2: {"roi": [242, 266, 211, 340], "arrow": None},
        3: {"roi": [0, 477, 254, 434], "arrow": "Left"},
        99: {"roi": [211, 802, 44, 39], "arrow": None},
    },
    3: {
        1: {"roi": [400, 705, 307, 234], "arrow": None},
        2: {"roi": [475, 475, 236, 231], "arrow": "Right"},
        3: {"roi": [450, 242, 263, 232], "arrow": None},
        4: {"roi": [141, 242, 335, 230], "arrow": None},
        5: {"roi": [243, 451, 222, 249], "arrow": None},
        6: {"roi": [7, 238, 168, 291], "arrow": None},
        7: {"roi": [9, 533, 235, 274], "arrow": "Left"},
        8: {"roi": [139, 755, 183, 133], "arrow": None},
        9: {"roi": [318, 809, 55, 130], "arrow": None},
        99: {"roi": [113, 908, 31, 31], "arrow": None},
    },
}


# 初始化
@AgentServer.custom_action("fdlg_init_data")
class FDLGInitData(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        self.data.floor = 0
        self.data.index = 0

        prefix = "弗德莱戈"

        context.override_pipeline(
            {
                # 执行入口
                "背包补充：补充完毕": {"next": [f"{prefix}：执行入口"]},
                # 重启游戏
                "重启游戏：等待启动画面": {"next": [f"{prefix}：执行入口（重启版）"]},
                # 循环进入地图
                "打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
                "宝箱：重新打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
                "战斗：【循环】": {"on_error": [f"{prefix}：【循环】进入地图"]},
                # 循环移动
                "点击自动移动": {"next": [f"{prefix}：【循环】移动中"]},
                "战斗：回到行走画面": {"next": [f"{prefix}：【循环】移动中"]},
            }
        )
        print(f"{prefix}：参数重置完成")
        return True


# 识别地图是否需要拖动箭头
@AgentServer.custom_recognition("fdlg_drag_map_reco")
class FDLGDrageMapReco(CustomRecognition):
    data = GlobalDataStore.get_instance()

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # print("FDLGDrageMapReco analyze called")
        roi_config = ROI_MAP.get(self.data.floor, {}).get(self.data.index, None)
        if roi_config is None:
            return CustomRecognition.AnalyzeResult(None, "")

        arrow = roi_config.get("arrow", None)
        reco_detail = None
        if arrow is None:
            pass
        elif arrow == "Left":
            reco_detail = context.run_recognition(
                "FDLG_DRAG_MAP_LEFT",
                argv.image,
                {
                    "FDLG_DRAG_MAP_LEFT": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "TemplateMatch",
                        "template": "common\\地图左箭头.png",
                        "roi": [9, 589, 17, 21],
                    },
                },
            )
        elif arrow == "Right":
            reco_detail = context.run_recognition(
                "FDLG_DRAG_MAP_RIGHT",
                argv.image,
                {
                    "FDLG_DRAG_MAP_RIGHT": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "TemplateMatch",
                        "template": "common\\地图右箭头.png",
                        "roi": [694, 589, 17, 21],
                    },
                },
            )

        if reco_detail is None:
            # 没有找到箭头，直接返回
            return CustomRecognition.AnalyzeResult(None, "")

        # print(f"FDLGDrageMapReco: {reco_detail.best_result}")
        return CustomRecognition.AnalyzeResult(reco_detail.best_result.box, arrow)


# 执行拖动地图操作
@AgentServer.custom_action("fdlg_drag_map")
class FDLGDragMap(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        roi_config = ROI_MAP.get(self.data.floor, {}).get(self.data.index, None)
        assert (
            roi_config is not None
        ), f"ROI not found for floor {self.data.floor}, index {self.data.index}"

        arrow = roi_config.get("arrow", None)
        if arrow is None:
            pass
        elif arrow == "Left":
            context.tasker.controller.post_swipe(325, 950, 375, 950, 200).wait()
        elif arrow == "Right":
            context.tasker.controller.post_swipe(375, 950, 325, 950, 200).wait()

        return True


# 点击继续行走到达一定次数后，重新选择目标
# 用于防卡死，比如和宝箱重叠时遇敌，遇敌后没有掉箱子，就会原地卡住
@AgentServer.custom_recognition("fdlg_need_reset_target")
class FDLGNeedResetTarget(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if store.continue_move_count >= 20:
            print("FDLGNeedResetTarget: 超过预设次数，重新选择目标")
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            return CustomRecognition.AnalyzeResult(box=None, detail="")


# 根据楼层选择目标
@AgentServer.custom_action("fdlg_choose_target")
class FDLGChooseTarget(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        store = GlobalDataStore.get_instance()
        store.continue_move_count = 0

        if self.data.floor == 0 or self.data.index == 99:
            reco_detail = context.run_recognition(
                "弗德莱戈：OCR楼层",
                context.tasker.controller.cached_image,
                {
                    "弗德莱戈：OCR楼层": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "OCR",
                        "expected": "弗德莱戈",
                        "roi": [65, 40, 604, 56],
                        "replace": [["R", "F"]],
                    },
                },
            )
            if reco_detail is not None:
                print(f"当前楼层检查: {reco_detail.best_result}")
                if reco_detail.best_result.text == "弗德莱戈的迷宫B1F":
                    if self.data.floor < 1:
                        self.data.floor = 1
                        self.data.index = 1
                elif reco_detail.best_result.text == "弗德莱戈的迷宫B2F":
                    if self.data.floor < 2:
                        self.data.floor = 2
                        self.data.index = 1
                elif reco_detail.best_result.text == "弗德莱戈的迷宫B3F":
                    if self.data.floor < 3:
                        self.data.floor = 3
                        self.data.index = 1

        # context.override_next(
        #     argv.node_name, [f"弗德莱戈：B{dataStore.floor}F_{dataStore.index}"]
        # )
        return self.run_find_next_chest(context, argv)

    def run_find_next_chest(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        print(f"正在查找目标：楼层: {self.data.floor}, 区块索引: {self.data.index}")
        if self.data.index >= 99:
            return self.run_find_next_floor(context, argv)

        roi_config = ROI_MAP.get(self.data.floor, {}).get(self.data.index, None)
        assert (
            roi_config is not None
        ), f"ROI not found for floor {self.data.floor}, index {self.data.index}"

        image = context.tasker.controller.cached_image
        reco_detail = context.run_recognition(
            "FDLG_FIND_NEXT_CHEST",
            image,
            {
                "FDLG_FIND_NEXT_CHEST": {
                    "pre_delay": 0,
                    "post_delay": 0,
                    "recognition": "TemplateMatch",
                    "template": "common\\宝箱.png",
                    "roi": roi_config.get("roi"),
                },
            },
        )
        if reco_detail is None:
            # 该搜索下个区域了
            self.data.index += 1
            roi_config = ROI_MAP.get(self.data.floor, {}).get(self.data.index, None)
            if roi_config is None:
                # 该搜索下个楼层了
                self.data.index = 99
            elif roi_config.get("arrow", None) is None:
                return self.run_find_next_chest(context, argv)
            return True

        # print(reco_detail.best_result)
        box = reco_detail.best_result.box
        context.tasker.controller.post_click(box[0], box[1]).wait()

        return True

    def run_find_next_floor(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        roi_config = ROI_MAP.get(self.data.floor, {}).get(99)
        image = context.tasker.controller.cached_image
        reco_detail = context.run_recognition(
            "FDLG_FIND_NEXT_FLOOR",
            image,
            {
                "FDLG_FIND_NEXT_FLOOR": {
                    "recognition": "TemplateMatch",
                    "pre_delay": 0,
                    "post_delay": 0,
                    "template": self.data.floor < 3
                    and "common\\地图图标下楼.png"
                    or "common\\地图图标哈肯.png",
                    "threshold": 0.9,
                    "roi": roi_config.get("roi"),
                },
            },
        )

        if reco_detail is None:
            # 可能是因为闪烁等原因导致图标找不到
            return False

        box = reco_detail.best_result.box
        context.tasker.controller.post_click(box[0], box[1]).wait()

        return True
