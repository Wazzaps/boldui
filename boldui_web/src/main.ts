
import { Communicator } from './comm';
import { StateMachine } from './state_machine';
import './style.css'

let stateMachine = new StateMachine();
(window as any).stateMachine = stateMachine;

let comm = new Communicator(stateMachine);
(window as any).comm = comm;

// let state = 0;
// let gotResp = false;
// let startedInteractor = false;
// window.updatedFrames = 0;
// window.missedFrames = 0;
// function pushChr(chr) {
//   comm.send({Update: {replies: [{path: stateMachine.scenes.get(1).uri, params: [{String: chr}]}]}})
// }
// function interactor() {
//   if (window.updatedFrames == 0) {
//     console.time("120 frames");
//   }
//   if (gotResp) {
//     window.updatedFrames++;
//     if (state == 0) {
//       pushChr("1");
//       state = 1;
//     } else if (state == 1) {
//       pushChr("+");
//       state = 2;
//     } else if (state == 2) {
//       pushChr("1");
//       state = 3;
//     } else if (state == 3) {
//       pushChr("=");
//       state = 1;
//     }
//   } else {
//     window.missedFrames++;
//   }
//   if (window.updatedFrames == 120) {
//     console.timeEnd("120 frames");
//   }
//   requestAnimationFrame(interactor);
// }
// interactor()
