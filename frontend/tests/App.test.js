import { mount } from "@vue/test-utils"
import { describe, it, expect } from "vitest"
import App from "../src/App.vue"

describe("App", () => {
  it("mounts successfully", () => {
    const wrapper = mount(App, {
      global: {
        stubs: ["router-view"], // we don't care about routing here
      },
    })

    expect(wrapper.exists()).toBe(true)
  })
})
