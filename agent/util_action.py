from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from store import GlobalDataStore


# 选择宝箱开启者
@AgentServer.custom_action("choose_opener")
class ChooseOpener(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        print("选择宝箱开启者")
        context.tasker.controller.post_click(370, 930)

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
