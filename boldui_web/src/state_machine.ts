import {Communicator} from "./comm";
import {
    A2RUpdate,
    A2RUpdateScene,
    Color,
    HandlerBlock,
    HandlerCmd,
    OpId,
    OpsOperation,
    R2AMessageVariantOpen,
    R2AMessageVariantUpdate,
    R2AOpen,
    R2AReply,
    R2AUpdate,
    SceneAttr,
    SceneAttrVariantTransform,
    SceneAttrVariantUri,
    SceneAttrVariantSize,
    Value,
    ValueVariantColor,
    ValueVariantDouble,
    ValueVariantPoint,
    ValueVariantRect,
    ValueVariantSint64,
    ValueVariantString,
    VarId,
    SceneAttrVariantWindowTitle,
} from "boldui_protocol/boldui_protocol.ts";
import {debugFmt, objectEquals} from "./utils.ts";
import {CanvasRenderer, Renderer} from "./renderer.ts";

export type Point = { left: number, top: number };


class SceneState {
    parent?: "root" | "hidden" | number;
    children: Array<number> = [];
    opResults: Value[] = [];
    dependsOnTime: boolean = false;
    isNew = true;
}

class Resource {
    data: Uint8Array;
    ranges: number[][];
    imageBase64?: string;
    imageElem?: HTMLImageElement;
    private onImageLoadHandlers: (() => void)[] = [];

    constructor(offset: number, data: Uint8Array) {
        this.data = data;
        this.ranges = [[offset, data.length]];
    }

    addData(_offset: number, _data: Uint8Array) {
        this.imageBase64 = undefined;
        this.imageElem = undefined;
        throw new Error("Not implemented");
    }

    removeData(_offset: number, _length: number) {
        this.imageBase64 = undefined;
        this.imageElem = undefined;
        throw new Error("Not implemented");
    }

    getImage(): string {
        if (this.imageBase64 === undefined) {
            const encoded = btoa(
              new Uint8Array(this.data)
                .reduce((data, byte) => data + String.fromCharCode(byte), "")
            );
            this.imageBase64 = "data:image/png;base64," + encoded;
        }
        return this.imageBase64;
    }

    getImageElem(onload: () => void): HTMLImageElement {
        if (!this.imageElem) {
            this.imageElem = new Image();
            this.imageElem.src = this.getImage();
        }

        let preventImmedTrigger = true;
        this.onImageLoadHandlers.push(onload);
        this.imageElem.onload = () => {
            if (!preventImmedTrigger) {
                this.onImageLoaded();
            }
        };
        preventImmedTrigger = false;

        return this.imageElem;
    }

    private onImageLoaded = () => {
        this.onImageLoadHandlers.forEach((handler) => handler());
        this.onImageLoadHandlers = [];
    }
}


export class StateMachine {
    private scenes = new Map<number, A2RUpdateScene>();
    private sceneStates = new Map<number, SceneState>();
    public rootScenes = new Set<number>();
    public varVals = new Map<string, Value>();
    public resources = new Map<number, Resource>();
    private context?: Value[];
    private startTime = window.performance.now();
    private watchesToRun: HandlerBlock[] = [];
    public comm?: Communicator;
    private renderer: Renderer = new CanvasRenderer();
    private isRerenderRequested = false;

    public requestRerender = () => {
        if (!this.isRerenderRequested) {
            this.isRerenderRequested = true;
            requestAnimationFrame(this.renderAndRunWatches);
        }
    }

    public getSceneParent = (scnIdx: number): "root" | "hidden" | number | undefined => {
        return this.sceneStates.get(scnIdx)?.parent;
    }

    public handleUpdate = (update: A2RUpdate) => {
        // console.log("Update:", update);

        // Update resources
        for (const resourceDealloc of update.resource_deallocs) {
            this.resources.get(resourceDealloc.id)!.removeData(Number(resourceDealloc.offset), Number(resourceDealloc.length));
        }
        for (const resourceChunk of update.resource_chunks) {
            const res = this.resources.get(resourceChunk.id);
            if (res === undefined) {
                this.resources.set(resourceChunk.id, new Resource(Number(resourceChunk.offset), new Uint8Array(resourceChunk.data)));
            } else {
                res.addData(Number(resourceChunk.offset), new Uint8Array(resourceChunk.data));
            }
        }

        // Update scene metadata
        for (let i = 0; i < update.updated_scenes.length; i++) {
            const scene = update.updated_scenes[i];
            this.scenes.set(scene.id, scene);
            if (!this.sceneStates.has(scene.id)) {
                this.sceneStates.set(scene.id, new SceneState());
            }
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

        // Remove scenes with no parent
        for (const [scnIdx, state] of this.sceneStates) {
            if (state.parent === undefined) {
                this.sceneStates.delete(scnIdx);
                this.scenes.delete(scnIdx);
            }
        }

        // Render to canvas
        // TODO: Decouple updates and re-renders, because watches might need to be triggered without re-rendering
        this.renderAndRunWatches();

        // if (!startedInteractor) {
        //   startedInteractor = true;
        //   gotResp = true;
        //   interactor();
        // }
    }

    private renderWithRendererAndSchedWatches = (scnIdx: number) => {
        const scene = this.scenes.get(scnIdx)!;
        const state = this.sceneStates.get(scnIdx)!;
        state.dependsOnTime = false;

        let initial_size = this.getSceneAttr(scene, SceneAttrVariantSize);
        if (state.isNew) {
            this.renderer.createScene(scene.id, this.asPoint(initial_size || new ValueVariantPoint(400, 300)), this);
            state.isNew = false;
        } else {
            // TODO: How does resizing work?
            // this.renderer.setCanvasSize(scene, this.asPoint(initial_size));
        }

        const sceneSize = this.renderer.getCanvasSize(scene);
        this.varVals.set(`:width_${scnIdx}`, new ValueVariantDouble(sceneSize.left));
        this.varVals.set(`:height_${scnIdx}`, new ValueVariantDouble(sceneSize.top));

        // Get transform.
        // The transform cannot access the scene's op results for performance reasons, so it's before the op eval below.
        // In this implementation there's no performance benefit yet since it's naive, but we shouldn't encourage it.
        const transform = this.getSceneAttr(scene, SceneAttrVariantTransform);
        let transformVec = { left: 0, top: 0 };
        if (transform !== undefined) {
            transformVec = this.asPoint(transform);
        }

        // Eval op list
        this.evalOpList(scene.ops, state.opResults, state);

        // Schedule watches
        for (const watch of scene.watches) {
            if (this.asBool(this.lookupOp(watch.condition))) {
                this.watchesToRun.push(watch.handler);
            }
        }

        // Render
        this.renderer.beginScene(transformVec, scene, this);
        for (const cmd of scene.cmds) {
            this.renderer.evalDrawCmd(cmd, scene, this);
        }

        // Display URI and Title
        const title = this.asString(this.getSceneConstantAttr(scene, SceneAttrVariantWindowTitle) || new ValueVariantString("BoldUI Application"));
        const uri = this.asString(this.getSceneConstantAttr(scene, SceneAttrVariantUri) || new ValueVariantString(""));
        this.renderer.setSceneUriAndTitle(uri, title, scnIdx, this);

        // Render children
        state.children.forEach((childIdx) => {
            this.renderWithRendererAndSchedWatches(childIdx);
        })

        this.renderer.endScene(scene, this);
    }

    private getSceneConstantAttr = (scene: A2RUpdateScene, attr: typeof SceneAttr): Value | undefined => {
        let op_id = scene.attrs.get(attr._tag);
        if (op_id !== undefined) {
            let op = this.scenes.get(op_id.scene_id)?.ops[op_id.idx];
            return op?.match({
                Value: val => val.value,
                Var: var_ => this.varVals.get(var_.value.key),
                _: _ => { throw new Error("This attr must depend on a constant value") },
            });
        }
    }

    private getSceneAttr = (scene: A2RUpdateScene, attr: typeof SceneAttr): Value | undefined => {
        const opId = scene.attrs.get(attr._tag);
        if (opId !== undefined) {
            // Try getting a constant value
            let op = this.scenes.get(opId.scene_id)?.ops[opId.idx];
            return op?.match({
                Value: val => val.value,
                Var: var_ => this.varVals.get(var_.value.key),
                // Otherwise get the value from the scene's op results
                _: _ => this.lookupOp(opId),
            });
        }
        return undefined;
    }


    private renderAndRunWatches = () => {
        this.isRerenderRequested = false;
        // Stats
        const sceneCount = this.scenes.size;
        let opCount = 0;
        let drawCmdCount = 0;
        let hndCmdCount = 0;
        let evtHndCount = 0;
        let watchCount = 0;
        let scnAttrCount = 0;

        const sortedRootScenes = [...this.rootScenes.values()];
        sortedRootScenes.sort((a, b) => a - b);

        for (const rootScene of this.rootScenes.values()) {
            // console.time("render");
            const scene = this.scenes.get(rootScene)!;
            if (rootScene == sortedRootScenes[0]) {
                let uri = this.asString(this.getSceneConstantAttr(scene, SceneAttrVariantUri)!);
                if (location.hash.slice(1) != uri) {
                    history.replaceState({}, "", `#${uri}`);
                }
            }

            this.renderWithRendererAndSchedWatches(rootScene);
            this.renderer.endRender(this);

            for (const watch of this.watchesToRun) {
                this.context = [];
                this.evalOpList(watch.ops, this.context, undefined);
                for (let cmd of watch.cmds) {
                    this.evalHandlerCmd(cmd);
                }
                this.context = undefined;
            }
            this.watchesToRun.length = 0;

            let anyDependOnTime = false;
            for (const [_, state] of this.sceneStates) {
                if (state.dependsOnTime) {
                    anyDependOnTime = true;
                }
            }
            if (anyDependOnTime) {
                this.requestRerender();
            }
            // console.timeEnd("render");

            // Collect stats
            for (const [_, scn] of this.scenes) {
                opCount += scn.ops.length;
                drawCmdCount += scn.cmds.length;
                evtHndCount += scn.event_handlers.length;
                for (const hnd of scn.event_handlers) {
                    opCount += hnd.handler.ops.length;
                    hndCmdCount += hnd.handler.cmds.length;
                }
                watchCount += scn.watches.length;
                for (const hnd of scn.watches) {
                    opCount += hnd.handler.ops.length;
                    hndCmdCount += hnd.handler.cmds.length;
                }
                scnAttrCount += scn.attrs.size;
            }
        }

        document.getElementById("stats")!.innerText = `Scenes=${sceneCount} Ops=${opCount} DrawCmds=${drawCmdCount} HandlerCmds=${drawCmdCount} EventHandlers=${evtHndCount} Watches=${watchCount} SceneAttrs=${scnAttrCount}`;
    }

    public handleRectEvent = (eventType: string, scnIdx: number, x: number, y: number) => {
        const scene = this.scenes.get(scnIdx)!;
        for (let i = scene.event_handlers.length-1; i >= 0; i--) {
            const evt_hnd = scene.event_handlers[i];
            let do_continue = true;
            let handlers = { _: (_: any) => {} }
            // @ts-ignore
            handlers[eventType] = (eventParams: { rect: OpId }) => {
                let rect = this.asRect(this.lookupOp(eventParams.rect));
                if (x >= rect.left && x < rect.right && y >= rect.top && y < rect.bottom) {
                    if (eventType == "MouseDown" || eventType == "MouseUp") {
                        this.varVals.set(":click_x", new ValueVariantDouble(x));
                        this.varVals.set(":click_y", new ValueVariantDouble(y));
                    } else if (eventType == "MouseMove") {
                        this.varVals.set(":mouse_x", new ValueVariantDouble(x));
                        this.varVals.set(":mouse_y", new ValueVariantDouble(y));
                    } else {
                        throw new Error("unimplemented event type: " + eventType);
                    }
                    this.context = [];
                    this.evalOpList(evt_hnd.handler.ops, this.context);
                    for (let cmd of evt_hnd.handler.cmds) {
                        this.evalHandlerCmd(cmd);
                    }
                    do_continue = this.asBool(this.lookupOp(evt_hnd.continue_handling));
                    this.context = undefined;
                }
            };
            evt_hnd.event_type.match(handlers);
            if (!do_continue) {
                break;
            }
        }
        this.requestRerender(); // TODO: Remove when var deps work
    }

    private evalHandlerCmd = (cmd: HandlerCmd) => {
        cmd.match({
            ReparentScene: reparent => {
                const reparentScene = this.asSint64Num(this.lookupOp(reparent.scene));

                // Remove previous parent
                let state = this.sceneStates.get(reparentScene)!;
                if (!state.parent) {
                    // Nothing to do
                } else if (state.parent === "root") {
                    this.rootScenes.delete(reparentScene);
                } else {
                    let parent = this.sceneStates.get(state.parent as number)!;
                    // Remove ourselves from our parent's children
                    const childIdx = parent.children.indexOf(reparentScene);
                    parent.children.splice(childIdx, 1);
                }

                state.parent = undefined;

                // Add new parent
                reparent.to.match({
                    Root: _root => {
                        this.rootScenes.add(reparentScene);
                        state.parent = "root";
                    },
                    Inside: inside => {
                        const insideVal = this.asSint64Num(this.lookupOp(inside.value));
                        let newParent = this.sceneStates.get(insideVal)!;
                        newParent.children.push(reparentScene);
                        state.parent = insideVal;
                    },
                    After: after => {
                        const afterVal = this.asSint64Num(this.lookupOp(after.value));
                        let sibling = this.sceneStates.get(afterVal)!;
                        let newParentIdx = sibling.parent! as number;
                        let newParent = this.sceneStates.get(newParentIdx)!;
                        newParent.children.splice(afterVal + 1, 0, reparentScene);
                        state.parent = newParentIdx;
                    },
                    Disconnect: _disconnect => {
                        // Was already disconnected, nothing to do
                    },
                    Hide: _hide => {
                        state.parent = "hidden";
                    },
                });

                this.renderer.setSceneIsRoot(state.parent == "root", reparentScene, this);
            },
            SetVar: setVar => {
                let value = this.lookupOp(setVar.value);
                if (setVar.var_.key != "/drag_controller/drag_pos") {
                    console.log(`SetVar ${setVar.var_.key} = ${debugFmt(value)}`);
                }
                this.varVals.set(setVar.var_.key, value);
            },
            SetVarByRef: setVar => {
                let var_ = this.asVarRef(this.lookupOp(setVar.var_));
                let value = this.lookupOp(setVar.value);
                if (var_.key != "/drag_controller/drag_pos") {
                    console.log(`SetVar ${var_.key} = ${debugFmt(value)}`);
                }
                this.varVals.set(var_.key, value);
            },
            DeleteVar: deleteVar => {
                this.varVals.delete(deleteVar.var_.key);
            },
            DeleteVarByRef: deleteVar => {
                let var_ = this.asVarRef(this.lookupOp(deleteVar.var_));
                this.varVals.delete(var_.key);
            },
            Reply: reply => {
                let path = reply.path;
                let params = reply.params.map((p: OpId) => this.lookupOp(p));
                this.comm!.send(new R2AMessageVariantUpdate(new R2AUpdate([new R2AReply(path, params)])));
            },
            Open: open => {
                this.comm!.send(new R2AMessageVariantOpen(new R2AOpen(open.path)));
            },
            AllocateWindowId: allocateWindowId => {
                throw new Error(`AllocateWindowId not implemented: ${debugFmt(allocateWindowId)}`);
            },
            DebugMessage: debugMessage => {
                console.log("DebugMessage: " + debugMessage.msg);
            },
            If: if_ => {
                let cmds = this.asSint64(this.lookupOp(if_.condition)) ? if_.then : if_.or_else;
                for (let cmd of cmds) {
                    this.evalHandlerCmd(cmd);
                }
            },
            Nop: _nop => {
            },
        });
    }

    private evalOpList = (ops: Array<OpsOperation>, resultArray: Array<Value>, currentSceneState?: SceneState) => {
        resultArray.length = 0;
        for (const op of ops) {
            resultArray.push(this.evalOp(op, currentSceneState));
        }
    }

    private lookupVar = ({ key }: VarId): Value => {
        let val = this.varVals.get(key);
        if (val === undefined) {
            throw new Error(`KeyError: var: ${key}`);
        }
        return val;
    }

    public lookupOp = ({ scene_id, idx }: OpId): Value => {
        if (scene_id === 0 && this.context) {
            return this.context[idx];
        }
        return this.sceneStates.get(scene_id)!.opResults[idx]!;
    }

    public asDouble = (val: Value): number => {
        return val.match({
            Double: (v) => v.value,
            Sint64: (v) => Number(v.value),
            _: (_v) => {
                throw new Error("Invalid cast to double");
            },
        });
    }

    public asSint64 = (val: Value): bigint => {
        return val.match({
            Sint64: (v) => v.value,
            _: (_v) => {
                throw new Error("Invalid cast to Signed Int64");
            },
        });
    }

    public asSint64Num = (val: Value): number => {
        return Number(this.asSint64(val));
    }

    public asBool = (val: Value): boolean => {
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

    public asString = (val: Value): string => {
        return val.match({
            String: v => v.value,
            Double: v => v.value.toString(),
            Sint64: v => v.value.toString(),
            _: (_v) => {
                throw new Error("Invalid cast to string");
            },
        });
    }

    public asRGBAColor = (val: Value): string => {
        return val.match({
            Color: (v: ValueVariantColor) => `rgba(${v.value.r * 255 / 65535}, ${v.value.g * 255 / 65535}, ${v.value.b * 255 / 65535}, ${v.value.a / 65535})`,
            _: (_v: Value) => {
                throw new Error("Invalid cast to color");
            },
        });
    }

    public asRect = (val: Value): { left: number, top: number, right: number, bottom: number } => {
        return val.match({
            Rect: (v: ValueVariantRect) => ({ left: v.left, top: v.top, right: v.right, bottom: v.bottom }),
            _: (_v: Value) => {
                throw new Error("Invalid cast to rect");
            },
        });
    }

    public asPoint = (val: Value): Point => {
        return val.match({
            Point: (v: ValueVariantPoint) => ({ left: v.left, top: v.top }),
            _: (_v: Value) => {
                throw new Error("Invalid cast to point");
            },
        });
    }

    public asVarRef = (val: Value): VarId => {
        return val.match({
            VarRef: (v) => v.value,
            _: (v) => {
                throw new Error("Invalid cast to VarRef: " + debugFmt(v));
            },
        });
    }

    public asAddable = (val: Value): number | Point => {
        return val.match<number | Point>({
            Double: (v) => v.value,
            Sint64: (v) => Number(v.value),
            Point: (v: ValueVariantPoint) => ({ left: v.left, top: v.top }),
            _: (_v) => {
                throw new Error("Invalid cast to double or Point");
            },
        });
    }

    private evalOp = (op: OpsOperation, currentSceneState?: SceneState): Value => {
        // console.log("Op:", op);


        return op.match({
            Value: value => value.value,
            Var: ({ value: var_ }) => {
                return this.lookupVar(new VarId(var_.key))!;
            },
            Add: add => {
                let a = this.asAddable(this.lookupOp(add.a));
                let b = this.asAddable(this.lookupOp(add.b));
                if (typeof a == "number" && typeof b == "number") {
                    return new ValueVariantDouble(a + b);
                } else if (typeof a == "object" && typeof b == "object") {
                    return new ValueVariantPoint(a.left + b.left, a.top + b.top);
                } else {
                    throw new Error(`Can't add ${a} and ${b}`)
                }
            },
            Mul: mul => {
                let a = this.asDouble(this.lookupOp(mul.a));
                let b = this.asDouble(this.lookupOp(mul.b));
                return new ValueVariantDouble(a * b);
            },
            Min: min => {
                let a = this.asDouble(this.lookupOp(min.a));
                let b = this.asDouble(this.lookupOp(min.b));
                return new ValueVariantDouble(Math.min(a, b));
            },
            Max: max => {
                let a = this.asDouble(this.lookupOp(max.a));
                let b = this.asDouble(this.lookupOp(max.b));
                return new ValueVariantDouble(Math.max(a, b));
            },
            GreaterThan: gt => {
                let a = this.asDouble(this.lookupOp(gt.a));
                let b = this.asDouble(this.lookupOp(gt.b));
                return new ValueVariantSint64(BigInt(a > b));
            },
            If: if_ => {
                let condition = this.asSint64(this.lookupOp(if_.condition));
                return condition ? this.lookupOp(if_.then) : this.lookupOp(if_.or_else);
            },
            And: and => {
                let a = this.asSint64(this.lookupOp(and.a));
                let b = this.asSint64(this.lookupOp(and.b));
                return new ValueVariantSint64(BigInt(a && b));
            },
            Or: or => {
                let a = this.asSint64(this.lookupOp(or.a));
                let b = this.asSint64(this.lookupOp(or.b));
                return new ValueVariantSint64(BigInt(a || b));
            },
            Abs: abs => {
                let a = this.asDouble(this.lookupOp(abs.a));
                return new ValueVariantDouble(Math.abs(a));
            },
            Sin: sin => {
                let a = this.asDouble(this.lookupOp(sin.a));
                return new ValueVariantDouble(Math.sin(a));
            },
            Cos: cos => {
                let a = this.asDouble(this.lookupOp(cos.a));
                return new ValueVariantDouble(Math.cos(a));
            },
            Neg: neg => {
                let a = this.asDouble(this.lookupOp(neg.a));
                return new ValueVariantDouble(-a);
            },
            Div: div => {
                let a = this.asDouble(this.lookupOp(div.a));
                let b = this.asDouble(this.lookupOp(div.b));
                if (b === 0) {
                    return new ValueVariantDouble(Infinity);
                }
                return new ValueVariantDouble(a / b);
            },
            FloorDiv: div => {
                let a = this.asDouble(this.lookupOp(div.a));
                let b = this.asDouble(this.lookupOp(div.b));
                if (b === 0) {
                    return new ValueVariantDouble(Infinity);
                }
                return new ValueVariantSint64(BigInt(Math.floor(a / b)));
            },
            MakeRectFromSides: makeRectFromSides => {
                let left = this.asDouble(this.lookupOp(makeRectFromSides.left));
                let top = this.asDouble(this.lookupOp(makeRectFromSides.top));
                let right = this.asDouble(this.lookupOp(makeRectFromSides.right));
                let bottom = this.asDouble(this.lookupOp(makeRectFromSides.bottom));
                return new ValueVariantRect(left, top, right, bottom);
            },
            MakeRectFromPoints: makeRectFromPoints => {
                let left_top = this.asPoint(this.lookupOp(makeRectFromPoints.left_top));
                let right_bottom = this.asPoint(this.lookupOp(makeRectFromPoints.right_bottom));
                return new ValueVariantRect(left_top.left, left_top.top, right_bottom.left, right_bottom.top);
            },
            MakePoint: makePoint => {
                let left = this.asDouble(this.lookupOp(makePoint.left));
                let top = this.asDouble(this.lookupOp(makePoint.top));
                return new ValueVariantPoint(left, top);
            },
            MakeColor: makeColor => {
                let r = this.asSint64Num(this.lookupOp(makeColor.r));
                let g = this.asSint64Num(this.lookupOp(makeColor.g));
                let b = this.asSint64Num(this.lookupOp(makeColor.b));
                let a = this.asSint64Num(this.lookupOp(makeColor.a));
                return new ValueVariantColor(new Color(r, g, b, a));
            },
            GetTime: _getTime => {
                if (currentSceneState) {
                    // console.log("depends on time");
                    currentSceneState.dependsOnTime = true;
                }
                return new ValueVariantDouble((window.performance.now() - this.startTime) / 1000);
            },
            GetTimeAndClamp: getTimeAndClamp => {
                let low = this.asDouble(this.lookupOp(getTimeAndClamp.low));
                let high = this.asDouble(this.lookupOp(getTimeAndClamp.high));
                let val = (window.performance.now() - this.startTime) / 1000;
                if (currentSceneState && val < high) {
                    // console.log("depends on time until" + high);
                    currentSceneState.dependsOnTime = true;
                }
                return new ValueVariantDouble(Math.min(high, Math.max(low, val)));
            },
            Eq: eq => {
                let a = this.lookupOp(eq.a);
                let b = this.lookupOp(eq.b);
                return new ValueVariantSint64(BigInt(objectEquals(a, b)));
            },
            Neq: eq => {
                let a = this.lookupOp(eq.a);
                let b = this.lookupOp(eq.b);
                return new ValueVariantSint64(BigInt(!objectEquals(a, b)));
            },
            ToString: toString => {
                let a = this.lookupOp(toString.a);
                return new ValueVariantString(a.toString());
            },
            GetImageDimensions: getImageDimensions => {
                let imageResId = this.asSint64(this.lookupOp(getImageDimensions.res));
                let image = this.resources.get(Number(imageResId))!.getImageElem(this.requestRerender);
                console.log("TODO: Probably wrong: image dimensions", image.width, image.height);
                return new ValueVariantPoint(image.width, image.height);
            },
            GetPointLeft: getPointLeft => {
                const point = this.asPoint(this.lookupOp(getPointLeft.point));
                return new ValueVariantDouble(point.left);
            },
            GetPointTop: getPointTop => {
                const point = this.asPoint(this.lookupOp(getPointTop.point));
                return new ValueVariantDouble(point.top);
            },
        });
    }
}
