import Vue from 'vue';
import Vuex from 'vuex';
import createLogger from 'vuex/dist/logger';

import auth from './auth';
import account from './account';
import notifications from './notifications';
import password from './password';
import signup from './signup';
import stores from './stores';
import tokens from './tokens';

const debug = process.env.NODE_ENV !== 'production';

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    account,
    auth,
    notifications,
    password,
    signup,
    stores,
    tokens,
  },
  strict: debug,
  plugins: debug ? [createLogger()] : [],
});
