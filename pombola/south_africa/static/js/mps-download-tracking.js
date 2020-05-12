$(".download-mps-link").on("click", function(e) {
  console.log("download-mps-link clicked")
  window.analytics.trackEvent({
    eventCategory: 'mps-download-as-excel-link',
    eventAction: 'click',
    eventLabel: 'MP download link clicked',
    'transport': 'beacon'
  });
});