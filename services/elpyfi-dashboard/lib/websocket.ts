import { io, Socket } from "socket.io-client";
import { Position, Signal } from "./api";

interface WebSocketEvents {
  positionUpdate: (position: Position) => void;
  signalUpdate: (signal: Signal) => void;
  error: (error: Error) => void;
  connect: () => void;
  disconnect: () => void;
}

class WebSocketManager {
  private socket: Socket | null = null;
  private url: string;
  private listeners: Partial<WebSocketEvents> = {};

  constructor(url: string = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001") {
    this.url = url;
  }

  connect() {
    if (this.socket?.connected) return;

    this.socket = io(this.url, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.listeners.connect?.();
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
      this.listeners.disconnect?.();
    });

    this.socket.on("position:update", (data: Position) => {
      this.listeners.positionUpdate?.(data);
    });

    this.socket.on("signal:new", (data: Signal) => {
      this.listeners.signalUpdate?.(data);
    });

    this.socket.on("error", (error: Error) => {
      console.error("WebSocket error:", error);
      this.listeners.error?.(error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on<K extends keyof WebSocketEvents>(event: K, callback: WebSocketEvents[K]) {
    this.listeners[event] = callback;
  }

  off<K extends keyof WebSocketEvents>(event: K) {
    delete this.listeners[event];
  }

  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsManager = new WebSocketManager();