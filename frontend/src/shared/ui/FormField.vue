<script setup lang="ts">
defineProps<{
  id: string
  label: string
  modelValue: string
  type?: string
  autocomplete?: string
  error?: string
  hint?: string
  required?: boolean
  maxlength?: number
}>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>
<template>
  <div class="field">
    <label :for="id">{{ label }} <span v-if="!required" class="field-optional">선택</span></label>
    <input
      :id="id"
      :name="id"
      :type="type ?? 'text'"
      :value="modelValue"
      :autocomplete="autocomplete"
      :required="required"
      :maxlength="maxlength"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${id}-error` : hint ? `${id}-hint` : undefined"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" :id="`${id}-error`" class="field-error">{{ error }}</p>
    <p v-else-if="hint" :id="`${id}-hint`" class="field-hint">{{ hint }}</p>
  </div>
</template>
