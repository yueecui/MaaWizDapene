from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("my_action_111")
class MyCustomAction(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        node = context.get_task_job()
        # print(f"当前任务节点: {node.job_id}")
        # print(f"当前任务节点: {node}")

        result = context.tasker.get_task_detail(node.job_id)
        last = result.nodes[-1] if result.nodes else None
        print(f"当前任务节点数量: {len(result.nodes)}")
        if last is not None:
            context.override_next(argv.node_name, [last.name])

        return True
