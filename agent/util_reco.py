from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from store import GlobalDataStore
from util import content_ocr


INN_MP_THRESHOLD = 30


# 识别地图是否需要拖动箭头
@AgentServer.custom_recognition("need_to_inn")
class NeedToInn(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        result = content_ocr(context, "/", [345, 1209, 51, 26])
        if result and result.best_result:
            best = result.best_result.text.replace("/", "")
            if best.isdigit():
                current_mp = int(best)
                if current_mp <= INN_MP_THRESHOLD:
                    return CustomRecognition.AnalyzeResult(
                        result.best_result.box, current_mp
                    )

        # 没有找到箭头，直接返回
        return CustomRecognition.AnalyzeResult(None, "")


# 识别地图是否需要拖动箭头
@AgentServer.custom_recognition("need_go_home")
class NeedToInn(CustomRecognition):
    data = GlobalDataStore.get_instance()

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        if self.data.gohome:
            return CustomRecognition.AnalyzeResult([0, 0, 100, 100], "")

        # 没有找到箭头，直接返回
        return CustomRecognition.AnalyzeResult(None, "")
