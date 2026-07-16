(function(h,o,u,n,d) {
  h=h[d]=h[d]||{q:[],onReady:function(c){h.q.push(c)}}
  d=o.createElement(u);d.async=1;d.src=n;d.crossOrigin=''
  n=o.getElementsByTagName(u)[0];n.parentNode.insertBefore(d,n)
})(window,document,'script','https://www.datadoghq-browser-agent.com/us1/v7/datadog-rum.js','DD_RUM')
window.DD_RUM.onReady(function() {
  window.DD_RUM.init({
      applicationId: '5549d108-8b7d-4b6f-871e-a81362a4709d',
      clientToken: 'puba78acef0d46d943bc13040deafe12de8',
      site: 'datadoghq.com',
      service: 'payflow-frontend',
      env: 'demo',
      version: '1.0.0',
      sessionSampleRate: 100,
      sessionReplaySampleRate: 100,
      trackResources: true,
      trackUserInteractions: true,
      trackLongTasks: true,
      defaultPrivacyLevel: 'mask-user-input'
  });
})
