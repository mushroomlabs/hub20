module.exports = {
  chainWebpack: config => {
    config.module
      .rule('scss')
      .use('sass')
      .loader('vue-style-loader')
      .tap(options => ({
        ...options,
        sourceMap: true,
        sourceMapContents: false
      }))
  },
  css: {
    loaderOptions: {
      sass: {
        implementation: require('sass'),
        sourceMap: true,
        sourceMapContents: false
      }
    }
  }
}
