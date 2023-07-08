import {StateMachine} from './state_machine';
import {
    A2R_MAGIC, A2RHelloResponse, A2RMessage, A2RMessageVariantUpdate, A2RUpdate,
    LATEST_MAJOR_VER,
    LATEST_MINOR_VER,
    R2A_MAGIC,
    R2AHello,
    R2AMessage, R2AMessageVariantOpen, R2AOpen
} from "boldui_protocol/boldui_protocol.ts";
import {BincodeSerializer} from "boldui_protocol/boldui_protocol.ts";
import {BincodeDeserializer} from "boldui_protocol/boldui_protocol.ts";

function memeq(a: Uint8Array, b: Uint8Array) {
    if (a.length != b.length) {
        return false;
    }
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

export class Communicator {
    private sock: WebSocket;
    private recvRequest?: [number, (_: Uint8Array) => void] = undefined;
    private buf = new Uint8Array();
    private onUpdate: (update: A2RUpdate) => void;

    constructor(stateMachine: StateMachine) {
        stateMachine.comm = this;
        this.onUpdate = stateMachine.handleUpdate;
        if (location.hash === "" || location.hash === "#") {
            history.replaceState({}, "", `#/`);
        }
        let innerURL = location.hash.slice(1);
        if (innerURL.startsWith("/")) {
            innerURL = `ws://${location.hostname}:7770` + innerURL;
        }
        const websocketAddr = new URL(innerURL);
        const initialPath = websocketAddr.pathname.slice(1) + websocketAddr.search;
        websocketAddr.pathname = "";
        websocketAddr.search = "";
        websocketAddr.hash = "";
        this.sock = new WebSocket(websocketAddr.toString());
        this.sock.onopen = async () => {
            await this.onopen(initialPath)
        };
        this.sock.onmessage = async (m) => {
            await this.onmessage(new Uint8Array(await m.data.arrayBuffer()))
        };
    }

    private async onmessage(data: Uint8Array) {
        let newBuf = new Uint8Array(this.buf.length + data.length);
        newBuf.set(this.buf, 0);
        newBuf.set(data, this.buf.length);
        this.buf = newBuf;
        if (this.recvRequest) {
            const [count, readCallback] = this.recvRequest;
            if (this.buf.length >= count) {
                let response = new Uint8Array(count);
                response.set(this.buf.slice(0, count), 0);
                let newBuf = new Uint8Array(this.buf.length - count);
                newBuf.set(this.buf.slice(count), 0);
                this.buf = newBuf;
                readCallback(response);
                this.recvRequest = undefined;
            }
        }
    }

    private async recv(count: number): Promise<Uint8Array> {
        return await new Promise((resolve, reject) => {
            if (this.recvRequest) {
                reject(new Error("Only one concurrent read is allowed"));
                return;
            }
            if (this.buf.length >= count) {
                let response = new Uint8Array(count);
                response.set(this.buf.slice(0, count), 0);
                let newBuf = new Uint8Array(this.buf.length - count);
                newBuf.set(this.buf.slice(count), 0);
                this.buf = newBuf;
                resolve(response);
            } else {
                this.recvRequest = [count, resolve];
            }
        });
    }

    private async onopen(initialPath: string) {
        // Send Hello
        let helloSer = new BincodeSerializer();
        new R2AHello(LATEST_MAJOR_VER, LATEST_MINOR_VER, LATEST_MAJOR_VER, 0).serialize(helloSer);
        this.sock.send(new Blob([R2A_MAGIC, helloSer.getBytes()]));

        // Wait for Hello Response
        let magic = await this.recv(A2R_MAGIC.length);
        if (!memeq(magic, A2R_MAGIC)) {
            throw new Error("Invalid magic: " + magic.toString());
        }

        let helloResponse = await this.recv(9);
        let helloResponseDeser = new BincodeDeserializer(helloResponse);
        let helloResponseObj = A2RHelloResponse.deserialize(helloResponseDeser);
        console.log("Hello response:", JSON.stringify(helloResponseObj));

        // Send Open
        this.send(new R2AMessageVariantOpen(new R2AOpen(initialPath)));

        // Main loop
        while (true) {
            let msgLen = new Uint32Array((await this.recv(4)).buffer)[0];
            let msgDeser = new BincodeDeserializer(await this.recv(msgLen));
            let msg = A2RMessage.deserialize(msgDeser);
            if (msg instanceof A2RMessageVariantUpdate) {
                console.time("update");
                this.onUpdate(msg.value);
                console.timeEnd("update");
            } else {
                throw new Error("Unknown message type: " + JSON.stringify(msg));
            }
        }
    }

    public send(message: R2AMessage) {
        let ser = new BincodeSerializer();
        message.serialize(ser);
        const encoded = ser.getBytes();
        // FIXME: Doesn't work on big-endian archs
        let msgLen = new Uint32Array([encoded.length]).buffer;
        this.sock.send(msgLen);
        this.sock.send(encoded);
    }
}
