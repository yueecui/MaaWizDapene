from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from store import GlobalDataStore


OPENER_CONFIG = {
    1: {"x": 160, "y": 930},
    2: {"x": 370, "y": 930, "fear_roi": [421, 865, 44, 44]},
}
OPENER_ORDER = [2, 1]


# 选择宝箱开启者
@AgentServer.custom_action("choose_opener")
class ChooseOpener(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        for opener in OPENER_ORDER:
            config = OPENER_CONFIG.get(opener, {})
            if not config:
                continue

            # 检查是否有恐惧状态
            if "fear_roi" in config:
                reco_detail = context.run_recognition(
                    "FDLG_CHECK_OPENER_FEAR",
                    context.tasker.controller.cached_image,
                    {
                        "FDLG_CHECK_OPENER_FEAR": {
                            "pre_delay": 0,
                            "post_delay": 0,
                            "recognition": "TemplateMatch",
                            "template": "图标宝箱恐惧.png",
                            "roi": config["fear_roi"],
                        },
                    },
                )
                if reco_detail is not None:
                    continue

            # 点击开启者位置
            print(f"选择宝箱开启者: {opener}")
            context.tasker.controller.post_click(config["x"], config["y"])
            return True

        print("选择宝箱开启者失败，未找到合适的开启者")
        return True


# 继续走，但是计数
@AgentServer.custom_action("continue_move")
class ContinueMove(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        store = GlobalDataStore.get_instance()
        context.tasker.controller.post_click(609, 227)
        store.continue_move_count += 1

        return True


# 点击网络错误重试，然后重新执行上一个任务
@AgentServer.custom_action("network_retry")
class NetworkRetry(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        # print(argv.box)
        # Rect(x=331, y=701, w=59, h=31) 是这样的格式
        context.tasker.controller.post_click(
            int(argv.box.x + argv.box.w / 2), int(argv.box.y + argv.box.h / 2)
        )

        # 设下一个任务节点为当前任务的上一个节点
        node = context.get_task_job()
        result = context.tasker.get_task_detail(node.job_id)
        last = result.nodes[-1] if result.nodes else None
        if last is not None:
            context.override_next(argv.node_name, [last.name])

        return True
