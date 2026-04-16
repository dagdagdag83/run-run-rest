import { mount } from '@vue/test-utils'
import App from './App.vue'
import { describe, it, expect } from 'vitest'

describe('App.vue', () => {
  it('renders login overlay initially', () => {
    const wrapper = mount(App)
    expect(wrapper.find('#login-overlay').exists()).toBe(true)
    expect(wrapper.find('#app-content').exists()).toBe(false)
  })

  // To truly test the authenticated state, we would mock fetch or initial state.
  // We'll keep the test simple per KISS.
})
