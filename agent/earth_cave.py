from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from store import GlobalDataStore
import json


TARGET_MAP = {
    1: {"x": 615, "y": 820},
}


# 初始化
@AgentServer.custom_action("earth_cave_init_data")
class EarthCaveInitData(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        self.data.floor = 1
        self.data.index = 1
        self.data.count += 1

        prefix = "土之魔窟"

        context.override_pipeline(
            {
                # 执行入口
                "背包补充：【循环】补充完毕": {"next": [f"{prefix}：背包补充完毕"]},
                # 重启游戏
                "重启游戏：等待启动画面": {"next": [f"{prefix}：执行入口（重启版）"]},
                # 循环进入地图
                "打开地图": {"next": [f"{prefix}：【循环】进入地图"]},
                "宝箱：重新打开地图": {"next": [f"{prefix}：【循环】寻找目标"]},
                "战斗：【循环】": {"on_error": [f"{prefix}：【循环】进入地图"]},
                # 循环移动
                "点击自动移动": {"next": [f"{prefix}：【循环】移动中"]},
                "点击自动移动（识图）": {"next": [f"{prefix}：【循环】移动中"]},
                "无法找到路线": {"next": [f"{prefix}：执行入口"]},
                "战斗：回到行走画面": {"next": [f"{prefix}：【循环】移动中"]},
            }
        )
        print(f"{prefix}：参数重置完成，准备开始第 {self.data.count} 次运行")
        return True


# 点击继续行走到达一定次数后，重新选择目标
# 用于防卡死，比如和宝箱重叠时遇敌，遇敌后没有掉箱子，就会原地卡住
@AgentServer.custom_recognition("earth_cave_need_reset_target")
class EarthCaveNeedResetTarget(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if store.continue_move_count >= 15:
            print("EarthCaveNeedResetTarget: 超过预设次数，重新选择目标")
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            return CustomRecognition.AnalyzeResult(box=None, detail="")


# 是否已经达到要离开迷宫的条件
@AgentServer.custom_recognition("earth_cave_need_escape_dungeon")
class EarthCaveNeedEscapeDungeon(CustomRecognition):
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


# 判断是否需要背包补充
@AgentServer.custom_recognition("earth_cave_need_bag_supplement")
class EarthCaveNeedBagSupplement(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        store = GlobalDataStore.get_instance()
        if (store.count - 1) > 0 and (store.count - 1) % 30 == 0:
            context.override_next(argv.node_name, ["背包补充：【循环】打开前"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")
        else:
            context.override_next(argv.node_name, ["土之魔窟：执行入口"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 100, 100), detail="")


# 根据楼层选择目标
@AgentServer.custom_action("earth_cave_choose_target")
class EarthCaveChooseTarget(CustomAction):
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
            # return self.escape_dungeon(context, argv)

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


# 增加index计数器
@AgentServer.custom_action("earth_cave_mod_index")
class EarthCaveModIndex(CustomAction):
    data = GlobalDataStore.get_instance()

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 转str为字典
        custom_action_param = json.loads(argv.custom_action_param)
        self.data.index = custom_action_param["index"]
        # print(f"EarthCaveModIndex: 当前索引 {self.data.index}")
        return True
