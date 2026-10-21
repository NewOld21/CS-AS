import js from '@eslint/js'
import ts from 'typescript-eslint'
import vue from 'eslint-plugin-vue'
import globals from 'globals'
export default [
  { ignores: ['dist/**', 'node_modules/**', 'test-results/**', 'playwright-report/**'] },
  js.configs.recommended, ...ts.configs.recommended, ...vue.configs['flat/essential'],
  { files: ['**/*.{ts,vue}'], languageOptions: { parserOptions: { parser: ts.parser }, globals: { ...globals.browser, ...globals.node } }, rules: { 'vue/multi-word-component-names': 'off' } },
]
