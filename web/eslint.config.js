import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import * as parserVue from 'vue-eslint-parser'
import tseslint from '@typescript-eslint/eslint-plugin'
import * as parserTs from '@typescript-eslint/parser'

export default [
  // Ignore patterns
  {
    ignores: ['**/node_modules/**', '**/dist/**', '**/build/**'],
  },

  // JavaScript/TypeScript files
  {
    files: ['**/*.{js,mjs,cjs,ts,tsx,cts,mts}'],
    languageOptions: {
      parser: parserTs,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        console: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        module: 'readonly',
        require: 'readonly',
        exports: 'readonly',
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        fetch: 'readonly',
        URLSearchParams: 'readonly',
        RequestInit: 'readonly',
        Response: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended.rules,
    },
  },

  // Vue files
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: parserVue,
      parserOptions: {
        ecmaVersion: 'latest',
        parser: parserTs,
        sourceType: 'module',
      },
      globals: {
        console: 'readonly',
        process: 'readonly',
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        fetch: 'readonly',
        URLSearchParams: 'readonly',
        RequestInit: 'readonly',
        Response: 'readonly',
      },
    },
    plugins: {
      vue: pluginVue,
      '@typescript-eslint': tseslint,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...pluginVue.configs['vue3-recommended'].rules,
      ...tseslint.configs.recommended.rules,
      'vue/multi-word-component-names': 'off',
    },
  },
]
