/// <reference types="react-scripts" />

declare module '*.css';

declare namespace NodeJS {
  interface ProcessEnv {
    readonly REACT_APP_API_URL?: string;
  }
}
