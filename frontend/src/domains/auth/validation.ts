import { ApiError } from '../../shared/api/client'
export function validate(email: string, password: string, nickname?: string) {
  const errors: Record<string, string> = {}
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) || email.trim().length > 254)
    errors.email = '올바른 이메일 주소를 입력해 주세요.'
  if (!password.trim() || password.length < 12 || password.length > 128)
    errors.password = '비밀번호는 12자 이상, 128자 이하로 입력해 주세요.'
  else if (new TextEncoder().encode(password).length > 72)
    errors.password = '비밀번호는 UTF-8 기준 72바이트 이하여야 해요. 한글은 글자당 3바이트예요.'
  if (nickname && (!nickname.trim() || nickname.trim().length > 40))
    errors.nickname = '닉네임은 공백을 제외하고 1~40자로 입력해 주세요.'
  return errors
}
export function errorMessage(error: unknown) {
  if (!(error instanceof ApiError)) return '요청을 완료하지 못했어요. 다시 시도해 주세요.'
  const messages: Record<string, string> = {
    EMAIL_ALREADY_EXISTS: '이미 가입한 이메일이에요. 로그인해 주세요.',
    INVALID_CREDENTIALS: '이메일 또는 비밀번호를 다시 확인해 주세요.',
    INVALID_INPUT: '입력한 내용을 다시 확인해 주세요.',
    CSRF_INVALID: '요청 확인이 만료됐어요. 버튼을 눌러 다시 시도해 주세요.',
    AUTH_REQUIRED: '로그인이 만료됐어요. 다시 로그인해 주세요.',
    NETWORK_ERROR: '서버에 연결할 수 없어요. 연결 상태를 확인한 뒤 다시 시도해 주세요.',
    TIMEOUT: '응답이 늦어지고 있어요. 잠시 후 다시 시도해 주세요.',
    RATE_LIMITED: '요청이 잠시 몰렸어요. 잠시 후 다시 시도해 주세요.',
  }
  return messages[error.code] ?? '요청을 완료하지 못했어요. 잠시 후 다시 시도해 주세요.'
}
