from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from store import GlobalDataStore

TARGET_MAP = {
    1: {"roi": [25, 257, 437, 221], "arrow": None},
    2: {"roi": [21, 476, 462, 211], "arrow": "Left"},
    3: {"roi": [477, 256, 234, 697], "arrow": "Right"},
    4: {"roi": [26, 725, 455, 201], "arrow": "Left"},
    99: {"roi": [335, 229, 56, 56], "arrow": None},
}


# 初始化
@AgentServer.custom_action("lbk_init_data")
class LBKInitData(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        self.data.floor = 1
        self.data.index = 1

        prefix = "卢比肯"

        context.override_pipeline(
            {
                # 执行入口
                "背包补充：【循环】补充完毕": {"next": [f"{prefix}：背包补充完毕"]},
                # 重启游戏
                "重启游戏：等待启动画面": {"next": [f"{prefix}：执行入口（重启版）"]},
                # 循环进入地图
                "打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
                "宝箱：重新打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
                "战斗：【循环】": {"on_error": [f"{prefix}：【循环】进入地图"]},
                # 循环移动
                "点击自动移动": {"next": [f"{prefix}：【循环】移动中"]},
                "点击自动移动（识图）": {"next": [f"{prefix}：【循环】移动中"]},
                "无法找到路线": {"next": [f"{prefix}：执行入口"]},
                "战斗：回到行走画面": {"next": [f"{prefix}：【循环】移动中"]},
            }
        )
        print(f"{prefix}：参数重置完成")
        return True


# 识别地图是否需要拖动箭头
@AgentServer.custom_recognition("lbk_drag_map_reco")
class LBKDrageMapReco(CustomRecognition):
    data = GlobalDataStore.get_instance()

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # print("LBKDrageMapReco analyze called")
        roi_config = TARGET_MAP.get(self.data.index, None)
        if roi_config is None:
            return CustomRecognition.AnalyzeResult(None, "")

        arrow = roi_config.get("arrow", None)
        reco_detail = None
        if arrow is None:
            pass
        elif arrow == "Left":
            reco_detail = context.run_recognition(
                "LBK_DRAG_MAP_LEFT",
                argv.image,
                {
                    "LBK_DRAG_MAP_LEFT": {
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
                "LBK_DRAG_MAP_RIGHT",
                argv.image,
                {
                    "LBK_DRAG_MAP_RIGHT": {
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

        # print(f"LBKDrageMapReco: {reco_detail.best_result}")
        return CustomRecognition.AnalyzeResult(reco_detail.best_result.box, arrow)


# 执行拖动地图操作
@AgentServer.custom_action("lbk_drag_map")
class LBKDragMap(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        roi_config = TARGET_MAP.get(self.data.index, None)
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
@AgentServer.custom_recognition("lbk_need_reset_target")
class LBKNeedResetTarget(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if store.continue_move_count >= 20:
            print("LBKNeedResetTarget: 超过预设次数，重新选择目标")
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            return CustomRecognition.AnalyzeResult(box=None, detail="")


# 是否已经达到要离开迷宫的条件
@AgentServer.custom_recognition("lbk_need_escape_dungeon")
class LBKNeedEscapeDungeon(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if store.index >= 99:
            print(f"满足离开迷宫条件，进入离开循环")
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            return CustomRecognition.AnalyzeResult(box=None, detail="")


# 根据楼层选择目标
@AgentServer.custom_action("lbk_choose_target")
class LBKChooseTarget(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        store = GlobalDataStore.get_instance()
        store.continue_move_count = 0

        return self.run_find_next_chest(context, argv)

    def run_find_next_chest(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        if self.data.index >= 99:
            return True

        print(f"正在查找目标，索引: {self.data.index}")

        target_config = TARGET_MAP.get(self.data.index, None)
        assert (
            target_config is not None
        ), f"TARGET_CONFIG not found for index {self.data.index}"

        x = 0
        y = 0
        if target_config.get("roi", None) is not None:
            reco_detail = context.run_recognition(
                "FIND_NEXT_CHEST",
                context.tasker.controller.cached_image,
                {
                    "FIND_NEXT_CHEST": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "TemplateMatch",
                        "template": "common\\宝箱.png",
                        "roi": target_config.get("roi"),
                    },
                },
            )

            if reco_detail is None:
                # 该搜索下个区域了
                self.data.index += 1
                target_config = TARGET_MAP.get(self.data.index, None)
                if target_config is None:
                    # 该撤退了
                    self.data.index = 99
                elif target_config.get("arrow", None) is None:
                    return self.run_find_next_chest(context, argv)
                return True
            x = int(reco_detail.best_result.box[0] + reco_detail.best_result.box[2] / 2)
            y = int(reco_detail.best_result.box[1] + reco_detail.best_result.box[3] / 2)
        else:
            x = target_config.get("x", 0)
            y = target_config.get("y", 0)

        if x == 0 or y == 0:
            return False

        context.tasker.controller.post_click(x, y).wait()
        return True
