import { mount } from '@vue/test-utils'
import { beforeAll, describe, expect, it } from 'vitest'
import EvidencePanel from '../../src/domains/chat/EvidencePanel.vue'
import SafeAnswer from '../../src/domains/chat/SafeAnswer.vue'
import type { Source } from '../../src/domains/quiz/api'

const source: Source = {
  source_id: 'wiki',
  document_id: 'doc',
  revision: 'old-r1',
  chunk_id: 'chunk',
  index_version: 'v1',
  title: 'Threads',
  url: 'https://example.org/thread',
  locator: 'section:memory',
  evidence_text: '저장한 실제 청크',
  category: 'OS',
  technology_version: '17',
}
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '')
  }
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open')
  }
})
describe('citation evidence snapshots', () => {
  it('shows the saved revision, body and safe source and closes on cancel', async () => {
    const wrapper = mount(EvidencePanel, { props: { source, sources: [source] } })
    expect(wrapper.text()).toContain('저장한 실제 청크')
    expect(wrapper.text()).toContain('old-r1')
    expect(wrapper.get('a').attributes('rel')).toBe('noopener noreferrer')
    await wrapper.get('dialog').trigger('cancel')
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
  })
  it('does not replace missing historical text and blocks unsafe URLs', () => {
    const wrapper = mount(EvidencePanel, {
      props: {
        source: { ...source, evidence_text: null, url: 'javascript:alert(1)' },
        sources: [source],
      },
    })
    expect(wrapper.text()).toContain('이전 근거 본문을 확인할 수 없습니다')
    expect(wrapper.find('a').exists()).toBe(false)
    wrapper.unmount()
  })
  it('switches between multiple citations and emits an inline citation selection', async () => {
    const second = { ...source, chunk_id: 'second', title: 'Second' }
    const panel = mount(EvidencePanel, { props: { source, sources: [source, second] } })
    await panel.get('nav button:last-child').trigger('click')
    expect(panel.emitted('select')![0]).toEqual([second])
    const answer = mount(SafeAnswer, {
      props: { content: '근거입니다. [2] <script>bad</script>', sources: [source, second] },
    })
    await answer.get('button').trigger('click')
    expect(answer.emitted('evidence')![0]).toEqual([second])
    expect(answer.find('script').exists()).toBe(false)
    panel.unmount()
  })
})
