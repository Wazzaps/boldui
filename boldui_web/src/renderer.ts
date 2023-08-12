import {A2RUpdateScene, CmdsCommand} from "boldui_protocol/boldui_protocol.ts";
import {htmlEscape} from "./utils.ts";
import {Point, StateMachine} from "./state_machine.ts";
import {bool} from "../../utils/serde-generate/runtime/typescript/serde/types.ts";

const textDecoder = new TextDecoder();

export interface Renderer {
    beginScene(transformVec: Point, scn: A2RUpdateScene, sm: StateMachine): void;
    endScene(scn: A2RUpdateScene, sm: StateMachine): void;
    getCanvasSize(scn: A2RUpdateScene): Point;
    setCanvasSize(scn: A2RUpdateScene, size: Point): void;
    evalDrawCmd(cmd: CmdsCommand, scn: A2RUpdateScene, sm: StateMachine): void;
    endRender(sm: StateMachine): void;
    createScene(sceneId: number, size: Point, sm: StateMachine): void;
    setSceneIsRoot(isRoot: bool, sceneId: number, sm: StateMachine): void;
    setSceneUriAndTitle(uri: string, title: string, sceneId: number, sm: StateMachine): void;
}

// noinspection JSUnusedGlobalSymbols
export class SvgRenderer implements Renderer {
    canvas: SVGElement = null as unknown as SVGElement;
    output: string = ""

    beginScene(transformVec: Point, scn: A2RUpdateScene, _sm: StateMachine) {
        let offset = "";
        if (transformVec.left || transformVec.top) {
            offset = `transform="translate(${transformVec.left} ${transformVec.top})"`;
        }
        this.output += `<g id="scn${scn.id}" ${offset}>`;
    }

    endScene(_scn: A2RUpdateScene, _sm: StateMachine) {
        this.output += "</g>";
    }

    getCanvasSize(): Point {
        return {
            left: this.canvas.clientWidth,
            top: this.canvas.clientHeight,
        };
    }

    setCanvasSize(_scn: A2RUpdateScene, size: Point): void {
        // @ts-ignore
        this.canvas.width.baseVal.value = size.left;
        // @ts-ignore
        this.canvas.height.baseVal.value = size.top;
    }

    evalDrawCmd(cmd: CmdsCommand, _scn: A2RUpdateScene, sm: StateMachine): void {
        this.output += cmd.match({
            Clear: clear => {
                // FIXME: only supports one root scene
                const rootScene = sm.rootScenes.values().next().value;
                let paint = sm.asRGBAColor(sm.lookupOp(clear.color));
                let width = sm.asDouble(sm.varVals.get(`:width_${rootScene}`)!);
                let height = sm.asDouble(sm.varVals.get(`:height_${rootScene}`)!);
                return `<rect x="0" y="0" width="${width}" height="${height}" style="fill:${paint};" />`;
            },
            DrawRect: drawRect => {
                let paint = sm.asRGBAColor(sm.lookupOp(drawRect.paint));
                let rect = sm.asRect(sm.lookupOp(drawRect.rect));
                return `<rect x="${rect.left}" y="${rect.top}" width="${rect.right - rect.left}" height="${rect.bottom - rect.top}" style="fill:${paint};" />`;
            },
            DrawRoundRect: drawRect => {
                let paint = sm.asRGBAColor(sm.lookupOp(drawRect.paint));
                let rect = sm.asRect(sm.lookupOp(drawRect.rect));
                let radius = sm.asDouble(sm.lookupOp(drawRect.radius));
                return `<rect x="${rect.left}" y="${rect.top}" width="${rect.right - rect.left}" height="${rect.bottom - rect.top}" style="fill:${paint};" rx="${radius}" />`;
            },
            DrawCenteredText: drawCenteredText => {
                const text = sm.lookupOp(drawCenteredText.text).match({
                    Resource: res => textDecoder.decode(sm.resources.get(res.value)!.data),
                    String: str => str.value,
                    _: _ => {
                        throw new Error("Invalid cast to string|resource");
                    },
                });
                let paint = sm.asRGBAColor(sm.lookupOp(drawCenteredText.paint));
                let center = sm.asPoint(sm.lookupOp(drawCenteredText.center));
                return `<text x="${center.left}" y="${center.top}" text-anchor="middle" dominant-baseline="central" font-size="20" font-family="sans" style="fill:${paint};">${htmlEscape(text)}</text>`;
            },
            DrawImage: img => {
                const res = sm.resources.get(sm.asSint64Num(sm.lookupOp(img.res)))!;
                const top_left = sm.asPoint(sm.lookupOp(img.top_left));
                // noinspection HtmlUnknownAttribute
                return `<image x="${top_left.left}" y="${top_left.top}" href='${res.getImage()}'/>`;
            }
        });
    }

    endRender(_sm: StateMachine) {
        this.canvas.innerHTML = this.output;
        this.output = "";
    }

    createScene(sceneId: number, size: Point, sm: StateMachine) {
        const canvas = document.createElement("svg");
        canvas.setAttribute("width", size.left.toString());
        canvas.setAttribute("height", size.top.toString());
        canvas.classList.add("canvas");
        document.getElementById("scenes")!.appendChild(canvas);
        this.canvas = canvas as unknown as SVGElement;

        canvas.onpointerdown = (e) => {
            sm.handleRectEvent("MouseDown", sceneId, e.offsetX, e.offsetY);
        }
        canvas.onpointerup = (e) => {
            sm.handleRectEvent("MouseUp", sceneId, e.offsetX, e.offsetY);
        }
        canvas.onpointermove = (e) => {
            sm.handleRectEvent("MouseMove", sceneId, e.offsetX, e.offsetY);
        }
    }

    setSceneIsRoot(_isRoot: bool, _sceneId: number, _sm: StateMachine) {
        console.error("Not implemented: setSceneIsRoot");
    }

    setSceneUriAndTitle(_uri: string, _title: string, _sceneId: number, _sm: StateMachine) {
        console.error("Not implemented: setSceneUriAndTitle");
    }
}

export class CanvasRenderer implements Renderer {
    canvases: { [scene_id: number]: HTMLCanvasElement | OffscreenCanvas } = {}
    contexts: { [scene_id: number]: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D } = {}
    canvasWrappers: { [scene_id: number]: HTMLDivElement } = {}
    sceneStack: number[] = []
    transformStack: Point[] = []

    beginScene(transformVec: Point, scn: A2RUpdateScene, _sm: StateMachine) {
        this.sceneStack.push(scn.id);
        this.transformStack.push(transformVec);
        const canvas = this.canvases[scn.id];
        const context = this.contexts[scn.id];
        context.clearRect(0, 0, canvas.width, canvas.height);
    }

    endScene(scn: A2RUpdateScene, _sm: StateMachine) {
        // this.contexts[scn.id].restore();
        const poppedSceneId = this.sceneStack.pop()!;
        const transform = this.transformStack.pop()!;
        if (poppedSceneId != scn.id) {
            throw new Error("Scene Stack Mismatch");
        }
        // Draw scene on parent canvas
        if (this.sceneStack.length > 0) {
            const parentId = this.sceneStack[this.sceneStack.length-1];
            const parentCtx = this.contexts[parentId];
            parentCtx.drawImage(this.canvases[scn.id], transform.left, transform.top);
        }
    }

    getCanvasSize(scn: A2RUpdateScene): Point {
        return {
            left: this.canvases[scn.id].width,
            top: this.canvases[scn.id].height,
        };
    }

    setCanvasSize(scn: A2RUpdateScene, size: Point): void {
        if (this.canvases[scn.id].width != size.left || this.canvases[scn.id].height != size.top) {
            this.canvases[scn.id].width = size.left;
            this.canvases[scn.id].height = size.top;
        }
    }

    evalDrawCmd(cmd: CmdsCommand, scn: A2RUpdateScene, sm: StateMachine): void {
        const context = this.contexts[scn.id];
        cmd.match({
            Clear: clear => {
                const canvas = this.canvases[scn.id];
                context.fillStyle = sm.asRGBAColor(sm.lookupOp(clear.color));
                context.fillRect(0, 0, canvas.width, canvas.height);
            },
            DrawRect: drawRect => {
                let rect = sm.asRect(sm.lookupOp(drawRect.rect));
                context.fillStyle = sm.asRGBAColor(sm.lookupOp(drawRect.paint));
                context.fillRect(rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top);
            },
            DrawRoundRect: drawRect => {
                let rect = sm.asRect(sm.lookupOp(drawRect.rect));
                let radius = sm.asDouble(sm.lookupOp(drawRect.radius));
                context.beginPath();
                context.fillStyle = sm.asRGBAColor(sm.lookupOp(drawRect.paint));
                context.roundRect(rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top, radius);
                context.fill();
            },
            DrawCenteredText: drawCenteredText => {
                const text = sm.lookupOp(drawCenteredText.text).match({
                    Resource: res => textDecoder.decode(sm.resources.get(res.value)!.data),
                    String: str => str.value,
                    _: _ => {
                        throw new Error("Invalid cast to string|resource");
                    },
                });
                let paint = sm.asRGBAColor(sm.lookupOp(drawCenteredText.paint));
                let center = sm.asPoint(sm.lookupOp(drawCenteredText.center));
                context.fillStyle = paint;
                context.textAlign = "center";
                context.textBaseline = "middle";
                context.font = "20px sans";
                context.fillText(text, center.left, center.top);
            },
            DrawImage: img => {
                const res = sm.resources.get(sm.asSint64Num(sm.lookupOp(img.res)))!;
                const top_left = sm.asPoint(sm.lookupOp(img.top_left));
                const imgElem = res.getImageElem(sm.requestRerender);
                context.drawImage(imgElem, top_left.left, top_left.top);
            }
        });
    }

    endRender(_sm: StateMachine) {
        if (this.sceneStack.length !== 0) {
            throw new Error("Ended render with scenes on the stack: " + this.sceneStack.toString())
        }
    }

    createScene(sceneId: number, size: Point, sm: StateMachine) {
        const canvasWrapper = document.createElement("div");
        canvasWrapper.classList.add("canvas-wrapper");
        if (sm.getSceneParent(sceneId) === "root") {
            canvasWrapper.classList.add("root-scene");
        }

        const windowUri = document.createElement("div");
        windowUri.classList.add("window-uri");
        canvasWrapper.appendChild(windowUri);

        const windowTitle = document.createElement("div");
        windowTitle.classList.add("window-title");
        canvasWrapper.appendChild(windowTitle);

        const canvas = document.createElement("canvas");
        canvas.width = size.left;
        canvas.height = size.top;
        const context = canvas.getContext("2d")!;
        canvas.classList.add("canvas");
        canvasWrapper.appendChild(canvas);

        document.getElementById("scenes")!.appendChild(canvasWrapper);

        this.canvases[sceneId] = canvas;
        this.contexts[sceneId] = context;
        this.canvasWrappers[sceneId] = canvasWrapper;

        canvas.onpointerdown = (e) => {
            sm.handleRectEvent("MouseDown", sceneId, e.offsetX, e.offsetY);
        }
        canvas.onpointerup = (e) => {
            sm.handleRectEvent("MouseUp", sceneId, e.offsetX, e.offsetY);
        }
        canvas.onpointermove = (e) => {
            sm.handleRectEvent("MouseMove", sceneId, e.offsetX, e.offsetY);
        }
    }

    setSceneIsRoot(isRoot: bool, sceneId: number, _sm: StateMachine) {
        let canvasWrapper = this.canvasWrappers[sceneId];
        if (!canvasWrapper) {
            // Scene not created yet, its root-ness will be determined by `createScene`
            return;
        }
        if (isRoot) {
            canvasWrapper.classList.add("root-scene");
        } else {
            canvasWrapper.classList.remove("root-scene");
        }
    }

    setSceneUriAndTitle(uri: string, title: string, sceneId: number, _sm: StateMachine) {
        const canvasWrapper = this.canvasWrappers[sceneId];
        (canvasWrapper.getElementsByClassName("window-uri")[0] as HTMLDivElement).innerText = `#${sceneId}: ${uri}`;
        (canvasWrapper.getElementsByClassName("window-title")[0] as HTMLDivElement).innerText = title;
    }
}
