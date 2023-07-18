import logging

import boldui
import dataclasses
from typing import Dict, Optional, List
from boldui_protocol import *
from boldui import ClientSide, st

# noinspection PyUnresolvedReferences
from boldui import eprint, print

app = boldui.BoldUIApplication()


@dataclasses.dataclass
class GLExampleState:
    gl_scene: Optional[SceneId] = None


@app.view("/")
def main_view(state: GLExampleState):
    s = boldui.get_current_scene()

    s.cmd_clear(s.hex_color(0x242424))
    s.op(OpsOperation__GetTime())

    # hnd = boldui.make_handler_block_factory(s.app)
    # hnd.hcmd_reply(
    #     f"/?action=ext_widget_loaded&session={s.session_id}",
    #     hnd.open_external_widget(app=Value__ExternalApp("boldui_example_py_gl_widget"), uri="/"),
    # )

    # if state.gl_scene is not None:
    #     hnd.push_hcmd(
    #         HandlerCmd__ReparentScene(
    #             scene=state.gl_scene,
    #             to=A2RReparentScene__Inside(s.scene.id),
    #         )
    #     )

    s.create_window(
        title="GL Example",
        initial_size=(512, 512),
        # extra_handler_block=hnd.scene,
        external_app_requests=[
            ExternalAppRequest(
                scene_id=s.scene.id,
                uri="cmd:python boldui_example_py_gl_widget",
            ),
        ],
    )


# @app.reply_handler("/")
# def main_reply_handler(state: GLExampleState, query_params: Dict[str, str], value_params: List[Value]):
#     action = query_params.get("action")
#     if action == "ext_widget_loaded":
#         external_widget = value_params[0]
#         assert isinstance(external_widget, Value__ExternalWidget)
#         logging.info(f"External widget loaded: {external_widget}")
#         state.gl_scene = external_widget.scene_id


if __name__ == "__main__":
    app.setup_logging()
    app.main_loop()
