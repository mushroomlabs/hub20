import { ActionPanel, FormGroupInput, Card, DropDown, Button } from "../widgets/index";

/**
 * You can register global components here and use them as a plugin in your main Vue instance
 */

const GlobalComponents = {
  install(Vue) {
    Vue.component("fg-input", FormGroupInput);
    Vue.component("drop-down", DropDown);
    Vue.component("card", Card);
    Vue.component("p-button", Button);
    Vue.component("action-panel", ActionPanel);
  }
};

export default GlobalComponents;
