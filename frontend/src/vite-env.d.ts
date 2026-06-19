/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ENABLE_INTERVIEW?: string
  readonly VITE_ENABLE_ADMIN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
