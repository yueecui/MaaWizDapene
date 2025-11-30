from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from store import GlobalDataStore
from util import update_pipeline

ROI_MAP = {
    1: {
        1: {"roi": [241, 476, 447, 435], "arrow": None},
        2: {"roi": [248, 269, 433, 216], "arrow": None},
        99: {"roi": [284, 286, 51, 53], "arrow": None},
    },
    2: {
        1: {"roi": [36, 269, 436, 211], "arrow": None},
        2: {"roi": [41, 478, 432, 231], "arrow": None},
        3: {"roi": [471, 267, 209, 426], "arrow": "Right"},
        99: {"roi": [337, 509, 48, 54], "arrow": None},
        100: {"roi": [239, 640, 34, 44], "arrow": None},
    },
    3: {
        1: {"roi": [243, 273, 211, 310], "arrow": None},
        2: {"roi": [40, 273, 210, 638], "arrow": "Left"},
        3: {"roi": [246, 574, 232, 338], "arrow": None},
        99: {"roi": [389, 568, 43, 47], "arrow": None},
    },
}


# 初始化
@AgentServer.custom_action("bieli_init_data")
class BIELIInitData(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        self.data.floor = 0
        self.data.index = 0

        prefix = "别离洞窟"

        update_pipeline(
            context, "背包补充：【循环】补充完毕", {"next": [f"{prefix}：背包补充完毕"]}
        )
        update_pipeline(
            context,
            "重启游戏：等待启动画面",
            {"next": [f"{prefix}：执行入口（重启版）"]},
        )
        update_pipeline(context, "打开地图", {"next": [f"{prefix}：【循环】进入地图"]})
        update_pipeline(
            context, "宝箱：重新打开地图", {"next": [f"{prefix}：【循环】进入地图"]}
        )
        update_pipeline(
            context, "恢复：回到主循环", {"next": [f"{prefix}：【循环】进入地图"]}
        )
        update_pipeline(
            context, "旅馆：回到主循环", {"next": [f"{prefix}：【循环】进入地图"]}
        )
        update_pipeline(
            context, "战斗：【循环】", {"on_error": [f"{prefix}：【循环】进入地图"]}
        )
        update_pipeline(
            context, "点击自动移动", {"next": [f"{prefix}：【循环】移动中"]}
        )
        update_pipeline(
            context, "点击自动移动（识图）", {"next": [f"{prefix}：【循环】移动中"]}
        )
        update_pipeline(context, "无法找到路线", {"next": [f"{prefix}：执行入口"]})
        update_pipeline(
            context, "战斗：回到行走画面", {"next": [f"{prefix}：【循环】移动中"]}
        )

        # context.override_pipeline(
        #     {
        #         # 执行入口
        #         "背包补充：【循环】补充完毕": {"next": [f"{prefix}：背包补充完毕"]},
        #         # 重启游戏
        #         "重启游戏：等待启动画面": {"next": [f"{prefix}：执行入口（重启版）"]},
        #         # 循环进入地图
        #         "打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
        #         "宝箱：重新打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
        #         "战斗：【循环】": {"on_error": [f"{prefix}：【循环】进入地图"]},
        #         # 循环移动
        #         "点击自动移动": {"next": [f"{prefix}：【循环】移动中"]},
        #         "点击自动移动（识图）": {"next": [f"{prefix}：【循环】移动中"]},
        #         "无法找到路线": {"next": [f"{prefix}：执行入口"]},
        #         "战斗：回到行走画面": {"next": [f"{prefix}：【循环】移动中"]},
        #     }
        # )
        print(f"{prefix}：参数重置完成！")
        return True


# 初始化
@AgentServer.custom_action("bieli_reset_gohome")
class BIELIResetGoHome(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        data = GlobalDataStore.get_instance()
        data.gohome = False
        print("回家标志已重置")
        return True


# 识别地图是否需要拖动箭头
@AgentServer.custom_recognition("bieli_drag_map_reco")
class BIELIDrageMapReco(CustomRecognition):
    data = GlobalDataStore.get_instance()

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # print("BIELIDrageMapReco analyze called")
        roi_config = ROI_MAP.get(self.data.floor, {}).get(self.data.index, None)
        if roi_config is None:
            return CustomRecognition.AnalyzeResult(None, "")

        arrow = roi_config.get("arrow", None)
        reco_detail = None
        if arrow is None:
            pass
        elif arrow == "Left":
            reco_detail = context.run_recognition(
                "BIELI_DRAG_MAP_LEFT",
                argv.image,
                {
                    "BIELI_DRAG_MAP_LEFT": {
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
                "BIELI_DRAG_MAP_RIGHT",
                argv.image,
                {
                    "BIELI_DRAG_MAP_RIGHT": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "TemplateMatch",
                        "template": "common\\地图右箭头.png",
                        "roi": [694, 589, 17, 21],
                    },
                },
            )

        if reco_detail is None or reco_detail.best_result is None:
            # 没有找到箭头，直接返回
            return CustomRecognition.AnalyzeResult(None, "")

        # print(f"BIELIDrageMapReco: {reco_detail.best_result}")
        return CustomRecognition.AnalyzeResult(reco_detail.best_result.box, arrow)


# 执行拖动地图操作
@AgentServer.custom_action("bieli_drag_map")
class BIELIDragMap(CustomAction):
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
@AgentServer.custom_recognition("bieli_need_reset_target")
class BIELINeedResetTarget(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if store.continue_move_count >= 20:
            print("BIELINeedResetTarget: 超过预设次数，重新选择目标")
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            return CustomRecognition.AnalyzeResult(box=None, detail="")


# 根据楼层选择目标
@AgentServer.custom_action("bieli_choose_target")
class BIELIChooseTarget(CustomAction):
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
                "别离洞窟：OCR楼层",
                context.tasker.controller.cached_image,
                {
                    "别离洞窟：OCR楼层": {
                        "pre_delay": 0,
                        "post_delay": 0,
                        "recognition": "OCR",
                        "expected": "别离洞窟",
                        "roi": [65, 40, 604, 56],
                        "replace": [["R", "F"]],
                    },
                },
            )
            if reco_detail.best_result is not None:
                print(f"当前楼层检查: {reco_detail.best_result}")
                if reco_detail.best_result.text == "别离洞窟B1F":
                    if self.data.floor < 1:
                        self.data.floor = 1
                        self.data.index = 1
                elif reco_detail.best_result.text == "别离洞窟B2F":
                    if self.data.floor < 2:
                        self.data.floor = 2
                        if self.data.gohome:
                            self.data.index = 100
                        else:
                            self.data.index = 1
                elif reco_detail.best_result.text == "别离洞窟B3F":
                    if self.data.floor < 3:
                        self.data.floor = 3
                        if self.data.gohome:
                            self.data.index = 99
                        else:
                            self.data.index = 1

        # context.override_next(
        #     argv.node_name, [f"别离洞窟：B{dataStore.floor}F_{dataStore.index}"]
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
            "BIELI_FIND_NEXT_CHEST",
            image,
            {
                "BIELI_FIND_NEXT_CHEST": {
                    "pre_delay": 0,
                    "post_delay": 0,
                    "recognition": "TemplateMatch",
                    "template": "common\\宝箱.png",
                    "roi": roi_config.get("roi"),
                },
            },
        )
        if reco_detail is None or reco_detail.best_result is None:
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

        template_name = "common\\地图图标下楼.png"
        config_index = 99
        if self.data.gohome:
            if self.data.floor >= 3:
                template_name = "common\\地图图标上楼.png"
            elif self.data.floor == 2:
                template_name = "common\\地图图标哈肯.png"
                config_index = 100
        elif self.data.floor >= 3:
            print("已到没有宝箱了，准备返回")
            self.data.gohome = True

        roi_config = ROI_MAP.get(self.data.floor, {}).get(config_index)
        image = context.tasker.controller.cached_image
        reco_detail = context.run_recognition(
            "BIELI_FIND_NEXT_FLOOR",
            image,
            {
                "BIELI_FIND_NEXT_FLOOR": {
                    "recognition": "TemplateMatch",
                    "pre_delay": 0,
                    "post_delay": 0,
                    "template": template_name,
                    "threshold": 0.9,
                    "roi": roi_config.get("roi"),
                },
            },
        )

        if reco_detail is None or reco_detail.best_result is None:
            # 可能是因为闪烁等原因导致图标找不到
            return False

        box = reco_detail.best_result.box
        context.tasker.controller.post_click(box[0], box[1]).wait()

        return True
