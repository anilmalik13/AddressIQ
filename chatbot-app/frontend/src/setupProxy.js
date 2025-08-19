const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5001',
      changeOrigin: true,
      logLevel: 'debug', // Add logging to see what's happening
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.status(500).send('Proxy error');
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log('Proxying request:', req.method, req.url);
      }
    })
  );
};
