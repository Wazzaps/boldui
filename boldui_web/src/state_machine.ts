import {Communicator} from "./comm";
import {
    A2RReparentSceneVariantAfter,
    A2RReparentSceneVariantDisconnect,
    A2RReparentSceneVariantHide,
    A2RReparentSceneVariantInside,
    A2RReparentSceneVariantRoot,
    A2RUpdate,
    A2RUpdateScene,
    CmdsCommand,
    CmdsCommandVariantClear,
    CmdsCommandVariantDrawCenteredText,
    CmdsCommandVariantDrawRect,
    CmdsCommandVariantDrawRoundRect,
    EventTypeVariantClick,
    HandlerBlock,
    HandlerCmd,
    HandlerCmdVariantAllocateWindowId,
    HandlerCmdVariantDebugMessage,
    HandlerCmdVariantIf,
    HandlerCmdVariantNop,
    HandlerCmdVariantReparentScene,
    HandlerCmdVariantReply,
    HandlerCmdVariantUpdateVar,
    OpId,
    OpsOperation,
    OpsOperationVariantAbs,
    OpsOperationVariantAdd,
    OpsOperationVariantCos,
    OpsOperationVariantDiv,
    OpsOperationVariantEq,
    OpsOperationVariantGetTime,
    OpsOperationVariantGetTimeAndClamp,
    OpsOperationVariantMakePoint,
    OpsOperationVariantMakeRectFromPoints,
    OpsOperationVariantMakeRectFromSides,
    OpsOperationVariantMax,
    OpsOperationVariantMin,
    OpsOperationVariantMul,
    OpsOperationVariantNeg,
    OpsOperationVariantSin,
    OpsOperationVariantToString,
    OpsOperationVariantValue,
    OpsOperationVariantVar,
    R2AMessageVariantUpdate,
    R2AReply,
    R2AUpdate,
    Value,
    ValueVariantColor,
    ValueVariantDouble,
    ValueVariantPoint,
    ValueVariantRect,
    ValueVariantSint64,
    ValueVariantString,
    VarId
} from "boldui_protocol/boldui_protocol.ts";
import {debugFmt, htmlEscape, objectEquals} from "./utils.ts";


class SceneState {
    parent?: "root" | "hidden" | number;
    children: Array<number> = [];
    varVals = new Map<string, Value>();
    opResults: Value[] = [];
    dependsOnTime: boolean = false;
}

export class StateMachine {
    private scenes = new Map<number, A2RUpdateScene>();
    private sceneStates = new Map<number, SceneState>();
    private rootScenes = new Set();
    private context?: Value[];
    private startTime = new Date().getTime();
    private watchesToRun: HandlerBlock[] = [];
    public comm?: Communicator;

    public handleUpdate = (update: A2RUpdate) => {
        // console.log("Update:", update);

        // Update scene metadata
        let scenesAdded: number[] = [];
        for (let i = 0; i < update.updated_scenes.length; i++) {
            const scene = update.updated_scenes[i];
            if (!this.scenes.has(scene.id)) {
                scenesAdded.push(scene.id);
            }
            this.scenes.set(scene.id, scene);
            if (!this.sceneStates.has(scene.id)) {
                this.sceneStates.set(scene.id, new SceneState());
            }
        }

        // Initialize var vals
        for (const scnIdx of scenesAdded) {
            const scene = this.scenes.get(scnIdx)!;
            const state = this.sceneStates.get(scnIdx)!;
            scene.var_decls.forEach((v, k) => {
                state.varVals.set(k, v);
            });
        }

        // Run blocks
        for (let i = 0; i < update.run_blocks.length; i++) {
            const block = update.run_blocks[i];
            this.context = [];
            this.evalOpList(block.ops, this.context);
            for (let cmd of block.cmds) {
                this.evalHandlerCmd(cmd);
            }
            this.context = undefined;
        }

        if (this.rootScenes.size > 1) {
            throw new Error("BoldUI Web only supports one root scene");
        }

        // Remove scenes with no parent
        for (const [scnIdx, state] of this.sceneStates) {
            if (state.parent === undefined) {
                this.sceneStates.delete(scnIdx);
                this.scenes.delete(scnIdx);
            }
        }

        // Render to SVG
        // TODO: Decouple updates and re-renders, because watches might need to be triggered without re-rendering
        this.renderAndRunWatches();

        // if (!startedInteractor) {
        //   startedInteractor = true;
        //   gotResp = true;
        //   interactor();
        // }

        // const app = document.getElementById("app") as unknown as SVGElement;
        // let output = "";
    }

    private renderToSVGAndSchedWatches = (scnIdx: number): string => {
        const scene = this.scenes.get(scnIdx)!;
        const state = this.sceneStates.get(scnIdx)!;
        state.dependsOnTime = false;

        // Eval op list
        this.evalOpList(scene.ops, state.opResults, state);

        // Schedule watches
        for (const watch of scene.watches) {
            if (this.asBool(this.lookupOp(watch.condition))) {
                this.watchesToRun.push(watch.handler);
            }
        }

        // Render to SVG
        let sceneResult = "";

        for (const cmd of scene.cmds) {
            sceneResult += this.evalDrawCmd(cmd);
        }

        let offset = [0, 0];
        return `<g id="scn${scnIdx}" transform="translate(${offset[0]} ${offset[1]})">
      ${sceneResult}
      ${state.children.map((childIdx) => this.renderToSVGAndSchedWatches(childIdx)).join("\n")}
    </g>`;
    }

    private renderAndRunWatches = () => {
        const app = document.getElementById("app") as unknown as SVGElement;
        const rootScene = this.rootScenes.values().next().value;
        if (rootScene) {
            const scene = this.scenes.get(rootScene)!;
            if (location.hash.slice(1) != scene.uri) {
                history.replaceState({}, "", `#${scene.uri}`);
            }
            const state = this.sceneStates.get(rootScene)!;
            let initial_size_x = state.varVals.get(":window_initial_size_x");
            let initial_size_y = state.varVals.get(":window_initial_size_y");
            if (initial_size_x && initial_size_y) {
                // @ts-ignore
                app.width.baseVal.value = this.asDouble(initial_size_x);
                // @ts-ignore
                app.height.baseVal.value = this.asDouble(initial_size_y);
            }
            // TODO: let title = state.varVals.get(":title");
            state.varVals.set(":width", new ValueVariantDouble(app.clientWidth));
            state.varVals.set(":height", new ValueVariantDouble(app.clientHeight));
            app.innerHTML = this.renderToSVGAndSchedWatches(rootScene);

            for (const watch of this.watchesToRun) {
                this.context = [];
                this.evalOpList(watch.ops, this.context, undefined);
                for (let cmd of watch.cmds) {
                    this.evalHandlerCmd(cmd);
                }
                this.context = undefined;
            }
            this.watchesToRun.length = 0;

            app.onpointerdown = (e) => {
                this.handleClick(rootScene, e.offsetX, e.offsetY);
            }
            if (state.dependsOnTime) {
                requestAnimationFrame(this.renderAndRunWatches);
            }
        }
    }

    public handleClick = (scnIdx: number, x: number, y: number) => {
        const scene = this.scenes.get(scnIdx)!;
        for (const [trigger, handler] of scene.event_handlers) {
            trigger.match({
                Click: (click: EventTypeVariantClick) => {
                    let rect = this.asRect(this.lookupOp(click.rect));
                    if (x >= rect.left && x < rect.right && y >= rect.top && y < rect.bottom) {
                        this.context = [];
                        this.evalOpList(handler.ops, this.context);
                        for (let cmd of handler.cmds) {
                            this.evalHandlerCmd(cmd);
                        }
                        this.context = undefined;
                    }
                },
            });
        }
    }

    private evalDrawCmd = (cmd: CmdsCommand): string => {
        return cmd.match({
            Clear: (clear: CmdsCommandVariantClear) => {
                const rootScene = this.rootScenes.values().next().value;
                let paint = this.asRGBAColor(this.lookupOp(clear.color));
                let width = this.asDouble(this.sceneStates.get(rootScene)?.varVals.get(":width")!);
                let height = this.asDouble(this.sceneStates.get(rootScene)?.varVals.get(":height")!);
                return `<rect x="0" y="0" width="${width}" height="${height}" style="fill:${paint};" />`;
            },
            DrawRect: (drawRect: CmdsCommandVariantDrawRect) => {
                let paint = this.asRGBAColor(this.lookupOp(drawRect.paint));
                let rect = this.asRect(this.lookupOp(drawRect.rect));
                return `<rect x="${rect.left}" y="${rect.top}" width="${rect.right - rect.left}" height="${rect.bottom - rect.top}" style="fill:${paint};" />`;
            },
            DrawRoundRect: (drawRect: CmdsCommandVariantDrawRoundRect) => {
                let paint = this.asRGBAColor(this.lookupOp(drawRect.paint));
                let rect = this.asRect(this.lookupOp(drawRect.rect));
                let radius = this.asDouble(this.lookupOp(drawRect.radius));
                return `<rect x="${rect.left}" y="${rect.top}" width="${rect.right - rect.left}" height="${rect.bottom - rect.top}" style="fill:${paint};" rx="${radius}" />`;
            },
            DrawCenteredText: (drawCenteredText: CmdsCommandVariantDrawCenteredText) => {
                let text = this.asString(this.lookupOp(drawCenteredText.text));
                let paint = this.asRGBAColor(this.lookupOp(drawCenteredText.paint));
                let center = this.asPoint(this.lookupOp(drawCenteredText.center));
                return `<text x="${center.left}" y="${center.top}" text-anchor="middle" dominant-baseline="central" font-size="20" font-family="sans" style="fill:${paint};">${htmlEscape(text)}</text>`;
            },
        });
    }

    private evalHandlerCmd = (cmd: HandlerCmd) => {
        cmd.match({
            ReparentScene: (reparent: HandlerCmdVariantReparentScene) => {
                // Remove previous parent
                let state = this.sceneStates.get(reparent.scene)!;
                if (!state.parent) {
                    // Nothing to do
                } else if (state.parent === "root") {
                    this.rootScenes.delete(reparent.scene);
                } else {
                    let parent = this.sceneStates.get(state.parent)!;
                    // Remove ourselves from our parent's children
                    const childIdx = parent.children.indexOf(reparent.scene);
                    parent.children.splice(childIdx, 1);
                }

                state.parent = undefined;

                // Add new parent
                reparent.to.match({
                    Root: (_root: A2RReparentSceneVariantRoot) => {
                        this.rootScenes.add(reparent.scene);
                        state.parent = "root";
                    },
                    Inside: (inside: A2RReparentSceneVariantInside) => {
                        let newParent = this.sceneStates.get(inside.value)!;
                        newParent.children.push(reparent.scene);
                        state.parent = inside.value;
                    },
                    After: (after: A2RReparentSceneVariantAfter) => {
                        let sibling = this.sceneStates.get(after.value)!;
                        let newParentIdx = sibling.parent! as number;
                        let newParent = this.sceneStates.get(newParentIdx)!;
                        newParent.children.splice(after.value + 1, 0, reparent.scene);
                        state.parent = newParentIdx;
                    },
                    Disconnect: (_disconnect: A2RReparentSceneVariantDisconnect) => {
                        // Was already disconnected, nothing to do
                    },
                    Hide: (_hide: A2RReparentSceneVariantHide) => {
                        state.parent = "hidden";
                    },
                });
            },
            UpdateVar: (updateVar: HandlerCmdVariantUpdateVar) => {
                let value = this.lookupOp(updateVar.value);
                this.sceneStates.get(updateVar.var_.scene)!.varVals.set(updateVar.var_.key, value);
            },
            Reply: (reply: HandlerCmdVariantReply) => {
                let path = reply.path;
                let params = reply.params.map((p: OpId) => this.lookupOp(p));
                this.comm!.send(new R2AMessageVariantUpdate(new R2AUpdate([new R2AReply(path, params)])));
            },
            AllocateWindowId: (allocateWindowId: HandlerCmdVariantAllocateWindowId) => {
                throw new Error(`AllocateWindowId not implemented: ${debugFmt(allocateWindowId)}`);
            },
            DebugMessage: (debugMessage: HandlerCmdVariantDebugMessage) => {
                console.log("DebugMessage: " + debugMessage.msg);
            },
            If: (if_: HandlerCmdVariantIf) => {
                throw new Error(`If not implemented: ${debugFmt(if_)}`);
            },
            Nop: (_nop: HandlerCmdVariantNop) => {
            },
        });
    }

    private evalOpList = (ops: Array<OpsOperation>, resultArray: Array<Value>, currentSceneState?: SceneState) => {
        resultArray.length = 0;
        for (const op of ops) {
            resultArray.push(this.evalOp(op, currentSceneState));
        }
    }

    private lookupVar = ({scene, key}: VarId): Value => {
        let val = this.sceneStates.get(scene)!.varVals.get(key);
        if (val === undefined) {
            throw new Error("KeyError: scene " + scene + ", key " + key);
        }
        return val;
    }

    private lookupOp = ({scene_id, idx}: OpId): Value => {
        if (scene_id === 0 && this.context) {
            return this.context[idx];
        }
        return this.sceneStates.get(scene_id)!.opResults[idx]!;
    }

    private asDouble = (val: Value): number => {
        return val.match({
            Double: (v) => v.value,
            Sint64: (v) => Number(v.value),
            _: (_v) => {
                throw new Error("Invalid cast to double");
            },
        });
    }

    private asBool = (val: Value): boolean => {
        return val.match({
            Sint64: (v) => {
                if (v.value === BigInt(0)) {
                    return false;
                } else if (v.value === BigInt(1)) {
                    return true;
                } else {
                    throw new Error("Invalid cast to bool of value: " + v.value.toString());
                }
            },
            _: (_v) => {
                throw new Error("Invalid cast to bool");
            },
        });
    }

    private asString = (val: Value): string => {
        return val.match({
            String: v => v.value,
            Double: v => v.value.toString(),
            Sint64: v => v.value.toString(),
            _: (_v) => {
                throw new Error("Invalid cast to string");
            },
        });
    }

    private asRGBAColor = (val: Value): string => {
        return val.match({
            Color: (v: ValueVariantColor) => `rgba(${v.value.r * 255 / 65535}, ${v.value.g * 255 / 65535}, ${v.value.b * 255 / 65535}, ${v.value.a / 65535})`,
            _: (_v: Value) => {
                throw new Error("Invalid cast to color");
            },
        });
    }

    private asRect = (val: Value): { left: number, top: number, right: number, bottom: number } => {
        return val.match({
            Rect: (v: ValueVariantRect) => ({left: v.left, top: v.top, right: v.right, bottom: v.bottom}),
            _: (_v: Value) => {
                throw new Error("Invalid cast to rect");
            },
        });
    }

    private asPoint = (val: Value): { left: number, top: number } => {
        return val.match({
            Point: (v: ValueVariantPoint) => ({left: v.left, top: v.top}),
            _: (_v: Value) => {
                throw new Error("Invalid cast to point");
            },
        });
    }

    private evalOp = (op: OpsOperation, currentSceneState?: SceneState): Value => {
        // console.log("Op:", op);


        return op.match({
            Value: (value: OpsOperationVariantValue) => value.value,
            Var: ({value: var_}: OpsOperationVariantVar) => {
                return this.lookupVar(new VarId(var_.scene, var_.key))!;
            },
            Add: (add: OpsOperationVariantAdd) => {
                let a = this.asDouble(this.lookupOp(add.a));
                let b = this.asDouble(this.lookupOp(add.b));
                return new ValueVariantDouble(a + b);
            },
            Mul: (mul: OpsOperationVariantMul) => {
                let a = this.asDouble(this.lookupOp(mul.a));
                let b = this.asDouble(this.lookupOp(mul.b));
                return new ValueVariantDouble(a * b);
            },
            Min: (min: OpsOperationVariantMin) => {
                let a = this.asDouble(this.lookupOp(min.a));
                let b = this.asDouble(this.lookupOp(min.b));
                return new ValueVariantDouble(Math.min(a, b));
            },
            Max: (max: OpsOperationVariantMax) => {
                let a = this.asDouble(this.lookupOp(max.a));
                let b = this.asDouble(this.lookupOp(max.b));
                return new ValueVariantDouble(Math.max(a, b));
            },
            Abs: (abs: OpsOperationVariantAbs) => {
                let a = this.asDouble(this.lookupOp(abs.a));
                return new ValueVariantDouble(Math.abs(a));
            },
            Sin: (sin: OpsOperationVariantSin) => {
                let a = this.asDouble(this.lookupOp(sin.a));
                return new ValueVariantDouble(Math.sin(a));
            },
            Cos: (cos: OpsOperationVariantCos) => {
                let a = this.asDouble(this.lookupOp(cos.a));
                return new ValueVariantDouble(Math.cos(a));
            },
            Neg: (neg: OpsOperationVariantNeg) => {
                let a = this.asDouble(this.lookupOp(neg.a));
                return new ValueVariantDouble(-a);
            },
            Div: (div: OpsOperationVariantDiv) => {
                let a = this.asDouble(this.lookupOp(div.a));
                let b = this.asDouble(this.lookupOp(div.b));
                if (b === 0) {
                    return new ValueVariantDouble(Infinity);
                }
                return new ValueVariantDouble(a / b);
            },
            FloorDiv: (div: OpsOperationVariantDiv) => {
                let a = this.asDouble(this.lookupOp(div.a));
                let b = this.asDouble(this.lookupOp(div.b));
                if (b === 0) {
                    return new ValueVariantDouble(Infinity);
                }
                return new ValueVariantSint64(BigInt(Math.floor(a / b)));
            },
            MakeRectFromSides: (makeRectFromSides: OpsOperationVariantMakeRectFromSides) => {
                let left = this.asDouble(this.lookupOp(makeRectFromSides.left));
                let top = this.asDouble(this.lookupOp(makeRectFromSides.top));
                let right = this.asDouble(this.lookupOp(makeRectFromSides.right));
                let bottom = this.asDouble(this.lookupOp(makeRectFromSides.bottom));
                return new ValueVariantRect(left, top, right, bottom);
            },
            MakeRectFromPoints: (makeRectFromPoints: OpsOperationVariantMakeRectFromPoints) => {
                let left_top = this.asPoint(this.lookupOp(makeRectFromPoints.left_top));
                let right_bottom = this.asPoint(this.lookupOp(makeRectFromPoints.right_bottom));
                return new ValueVariantRect(left_top.left, left_top.top, right_bottom.left, right_bottom.top);
            },
            MakePoint: (makePoint: OpsOperationVariantMakePoint) => {
                let left = this.asDouble(this.lookupOp(makePoint.left));
                let top = this.asDouble(this.lookupOp(makePoint.top));
                return new ValueVariantPoint(left, top);
            },
            GetTime: (_getTime: OpsOperationVariantGetTime) => {
                if (currentSceneState) {
                    currentSceneState.dependsOnTime = true;
                }
                return new ValueVariantDouble(((new Date().getTime()) - this.startTime) / 1000);
            },
            GetTimeAndClamp: (getTimeAndClamp: OpsOperationVariantGetTimeAndClamp) => {
                let low = this.asDouble(this.lookupOp(getTimeAndClamp.low));
                let high = this.asDouble(this.lookupOp(getTimeAndClamp.high));
                let val = ((new Date().getTime()) - this.startTime) / 1000;
                if (currentSceneState && val < high) {
                    currentSceneState.dependsOnTime = true;
                }
                return new ValueVariantDouble(Math.min(high, Math.max(low, val)));
            },
            Eq: (eq: OpsOperationVariantEq) => {
                let a = this.lookupOp(eq.a);
                let b = this.lookupOp(eq.b);
                return new ValueVariantSint64(BigInt(objectEquals(a, b)));
            },
            ToString: (toString: OpsOperationVariantToString) => {
                let a = this.lookupOp(toString.a);
                return new ValueVariantString(a.toString());
            }
        });
    }
}
