$(function () {
  // If Google Analytics is loaded, try send events when elements are visible in viewport
  if (typeof ga === 'function') {
    const TIMEOUT_BEFORE_FIRING_ANALYTICS = 1000;
    var elementsToTrackScrollEvents = {
      "#membersinterests": {
        "category": "person-page-tab-membersinterests",
        "action": "activate",
        "label": "members-interests"
      },
      "#member-experience": {
        "category": "person-page-tab-experience",
        "action": "activate",
        "label": "member-experience"
      },
      "#apperances": {
        "category": "person-page-tab-appearances",
        "action": "activate",
        "label": "member-apperances"
      },
      "#messages-section": {
        "category": "person-page-tab-messages",
        "action": "activate",
        "label": "messages"
      },
      "#attendance": {
        "category": "person-page-tab-attendance",
        "action": "activate",
        "label": "attendance"
      },
    };

    var elementsToTrackExpandDefinitionEvents = {
      "#members-interests-section": {
        "category": "collapsed-definition",
        "action": "expand",
        "label": "members-interests"
      },
      "#plenary-apperances-section": {
        "category": "collapsed-definition",
        "action": "expand",
        "label": "plenary-apperances"
      },
      "#committee-meetings-title": {
        "category": "collapsed-definition",
        "action": "expand",
        "label": "committee-meetings"
      },
      "#minister-questions-title": {
        "category": "collapsed-definition",
        "action": "expand",
        "label": "questions-to-ministers"
      },
    };


    function sendAnalyticsEvent(category, action, label) {
      // we use a timeout to ensure that the event is sent after user has
      // scrolled over the element considerably
      setTimeout(function () {
        ga('send', {
          hitType: 'event',
          eventCategory: category,
          eventAction: action,
          eventLabel: label
        });
      }, TIMEOUT_BEFORE_FIRING_ANALYTICS);
    }

    $(Object.keys(elementsToTrackScrollEvents)).each(function (_, element) {
      $(element).one('inview', function (_, isInView) {
        if (isInView) {
          var elementAttributes = elementsToTrackScrollEvents[element];
          var category = elementAttributes.category,
            action = elementAttributes.action,
            label = elementAttributes.label;
          sendAnalyticsEvent(category, action, label);
        }
      });
    });
    $(Object.keys(elementsToTrackExpandDefinitionEvents)).each(function (_, element) {
      $(element).click(function () {
        var elementAttributes = elementsToTrackExpandDefinitionEvents[element];
        var category = elementAttributes.category,
          action = elementAttributes.action,
          label = elementAttributes.label;
        sendAnalyticsEvent(category, action, label);
      });
    });
  }
});
