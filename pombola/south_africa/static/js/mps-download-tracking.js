$(".download-mps-link").on("click", function(e) {
  window.analytics.trackEvent({
    eventCategory: 'mps-download-as-excel-link',
    eventAction: 'click',
    eventLabel: 'MP download link clicked',
    'transport': 'beacon'
  });
});