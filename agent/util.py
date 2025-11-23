from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RecognitionDetail


def content_ocr(
    context: Context,
    expected: str | list[str],
    roi: list[int],
) -> RecognitionDetail | None:
    if isinstance(expected, str):
        expected = [expected]

    image = context.tasker.controller.cached_image
    reco_detail = context.run_recognition(
        "CONTENT_OCR",
        image,
        {
            "CONTENT_OCR": {
                "pre_delay": 0,
                "post_delay": 0,
                "recognition": "OCR",
                "expected": expected,
                "roi": roi,
            },
        },
    )
    return reco_detail


def click_auto_move(
    context: Context,
    argv: CustomAction.RunArg,
) -> bool:
    reco_detail = content_ocr(context, "自动移动", [0, 144, 720, 823])
    if reco_detail is None:
        return False
    if reco_detail and reco_detail.best_result:
        context.tasker.controller.post_click(
            reco_detail.best_result.box[0], reco_detail.best_result.box[1]
        ).wait()
        return True
