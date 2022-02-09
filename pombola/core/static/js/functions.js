$(function () {

  //Initialize tooltips
  $('[data-toggle="tooltip"]').tooltip()

  // toggle former positions button on /person/person-slug/
  const toggleFormerElement = $('#toggle-former-positions');
  const showFormerPositionsText = $('#show-former-positions-text');
  const hideFormerPositionsText = $('#hide-former-positions-text');
  const hideFormerPositionsIcon = $('#hide-former-positions-icon');
  const showFormerPositionsIcon = $('#show-former-positions-icon');
  var showingAllFormerPositions = false;
  toggleFormerElement.on('click', function (e) {
    e.preventDefault();
    showingAllFormerPositions = !showingAllFormerPositions;
    if (showingAllFormerPositions) {
      showFormerPositionsText[0].style.display = 'none';
      showFormerPositionsIcon[0].style.display = 'none';

      hideFormerPositionsText[0].style.display = 'block';
      hideFormerPositionsIcon[0].style.display = 'flex';
    } else {
      showFormerPositionsText[0].style.display = 'block';
      hideFormerPositionsText[0].style.display = 'none';

      showFormerPositionsIcon[0].style.display = 'flex';
      hideFormerPositionsIcon[0].style.display = 'none';
    }
    var collapseElement = document.getElementById("truncate-former-section");
    collapseElement.classList.toggle("truncate-div");
    if (typeof ga === 'function') {
      ga('send', {
        hitType: 'event',
        eventCategory: 'collapsed-items',
        eventAction: showingAllFormerPositions ? 'expand' : 'collapse',
        eventLabel: 'former-positions'
      });
    }
  });
  // toggle current positions button on /person/person-slug/
  const toggleCurrentElement = $('#toggle-current-positions');
  const showCurrentPositionsText = $('#show-current-positions-text');
  const hideCurrentPositionsText = $('#hide-current-positions-text');
  const hideCurrentPositionsIcon = $('#hide-current-positions-icon');
  const showCurrentPositionsIcon = $('#show-current-positions-icon');
  var showingAllCurrentPositions = false;
  toggleCurrentElement.on('click', function (e) {
    e.preventDefault();
    showingAllCurrentPositions = !showingAllCurrentPositions;
    if (showingAllCurrentPositions) {
      showCurrentPositionsText[0].style.display = 'none';
      showCurrentPositionsIcon[0].style.display = 'none';

      hideCurrentPositionsText[0].style.display = 'block';
      hideCurrentPositionsIcon[0].style.display = 'flex';
    } else {
      showCurrentPositionsText[0].style.display = 'block';
      hideCurrentPositionsText[0].style.display = 'none';

      showCurrentPositionsIcon[0].style.display = 'flex';
      hideCurrentPositionsIcon[0].style.display = 'none';
    }
    var collapseElement = document.getElementById("truncate-current-section");
    collapseElement.classList.toggle("truncate-div");
    if (typeof ga === 'function') {
      ga('send', {
        hitType: 'event',
        eventCategory: 'collapsed-items',
        eventAction: showingAllCurrentPositions ? 'expand' : 'collapse',
        eventLabel: 'current-positions'
      });
    }
  });

  /*
   * auto complete
   */
  const searchInput = $('input.search-autocomplete-name');
  searchInput.each(function () {
    var element = $(this);
    var source = element.data('source') || "/search/autocomplete/";
    element.autocomplete({
      source: source,
      minLength: 2,
      html: true,
      select: function (event, ui) {
        if (ui.item) return window.location = ui.item.url;
      }
    });
    const elementAutocomplete = element.data('uiAutocomplete');
    elementAutocomplete._renderItem = function (ul, item) {
      var itemElement = $('<li>'), imageElement = $('<img>');
      imageElement.attr('src', item.image_url);
      imageElement.attr('width', '16');
      imageElement.attr('height', '16');
      itemElement.append(imageElement).append(' ' + item.name);
      if (item.extra_data) {
        itemElement.append(' ').append($('<i>').append(item.extra_data));
      }
      return itemElement.appendTo(ul);
    };
  });


  // auto-advance cycles through featured MPs; it also immediately replaces the
  // featured MP in the page (since we assume that has been frozen by caching)
  var auto_advance_enabled = false;
  var auto_advance_delay = 12000; // milliseconds
  var auto_advance_timeout = false;

  function transitionDiv(height) {
    return '<div class="featured-person featured-person-loading" style="height:'
      + $('#home-featured-person').height() + 'px"><p>loading...</p></div>';
  }

  $('.js-expanded-toggle').on('click', function (e) {
    e.preventDefault();
    if ($(this).attr('aria-expanded') === 'true') {
      $(this).attr('aria-expanded', false);
    } else {
      $(this).attr('aria-expanded', true);
    }
  });

  // important to delegate this (with on()) because the contents change each auto-advance
  $('#home-featured-person').on("click", '.feature-nav > a', function (e, is_auto_advancing) {
    e.preventDefault();
    if (!is_auto_advancing) { // user clicked
      auto_advance_enabled = false;
      if (auto_advance_timeout) {
        clearTimeout(auto_advance_timeout);
      }
    }

    var m = $(this).attr('href').match(/(before|after)=([-\w]+)$/);
    if (m.length == 3) { // wee sanity check: found direction [1] and slug [2]
      $('#home-featured-person .featured-person').replaceWith(transitionDiv());
      $.get("person/featured/" + m[1] + '/' + m[2]).done(function (html) {
        $('#home-featured-person .featured-person').replaceWith(html);
      });
    }
  });

  if (auto_advance_enabled) {
    $('#home-featured-person .featured-person').replaceWith(transitionDiv());
    $.get('person/featured/' + Math.floor(Math.random() * 100)).done(function (html) {
      // some random index of featured person
      $('#home-featured-person .featured-person').replaceWith(html);
    });
    function auto_advance() {
      if (auto_advance_enabled) {
        $('#home-featured-person a.feature-next').trigger("click", true);
        auto_advance_timeout = window.setTimeout(auto_advance, auto_advance_delay);
      }
    }
    auto_advance_timeout = window.setTimeout(auto_advance, auto_advance_delay);
  }

  /*
   * enable dialog based feedback links
   */
  $('a.feedback_link')
    .on(
      'click',
      function (event) {
        // Note - we could bail out here if the window is too small, as
        // we'd be on a mobile and it might be better just to send them to
        // the feedback page. Not done as this js should only be loaded on
        // a desktop.

        // don't follow the link to the feedback page.
        event.preventDefault();

        // create a div to use in the dialog
        var dialog_div = $('<div id="feedback_dialog_div">Loading...</div>');

        // Load the initial content for the dialog
        if (window.pombola_settings.google_recaptcha_site_key) {
          dialog_div.load(event.target.href + ' #ajax_dialog_subcontent', function () {
            grecaptcha.render('feedbackSubmit', {
              'sitekey': window.pombola_settings.google_recaptcha_site_key,
            });

          });
        } else {
          dialog_div.load(event.target.href + ' #ajax_dialog_subcontent');
        }

        // Submit feedback using AJAX, and only show the ajax_dialog_subcontent.
        window.handle_feedback_form_submission = function () {
          var form = $("#add_feedback");
          form.ajaxSubmit({
            success: function (responseText) {
              var dialog_div = $("#feedback_dialog_div");
              dialog_div.html($(responseText).find('#ajax_dialog_subcontent'));
            }
          });
        };

        // Show the dialog
        dialog_div.dialog({
          modal: true,
          minHeight: 320,
          width: 500,
          title: 'Leave Feedback'
        });

      }
    );

  /* carry search terms across when switching between search pages */
  $("#search-hansard-instead").click(function (e) {
    e.preventDefault();
    location.href = "/search/hansard?q=" + escape($('#core-search,#id_q,#loc').first().val());
  });
  $("#search-core-instead").click(function (e) {
    e.preventDefault();
    location.href = "/search?q=" + escape($('#id_q,#loc').first().val());
  });

  const showMessageToolsId = $("#show-message-tools-toggle")
  const messagesContainer = $("#message-tips-container")

  showMessageToolsId.click(function (e) {
    e.preventDefault()
    messagesContainer.toggle()
  });

  // Add input placeholder text to search form
  const subjectInputId = "id_draft-subject"
  const placeholder = "Write a short, descriptive subject..."
  const input = $("#" + subjectInputId)
  if (input) {
    input.attr("placeholder", placeholder)
    input.attr("required", "")
    input.attr("maxlength", "256")
  }

  const memberSalutationId = "member-salutation"
  const memberSalutation = $("#" + memberSalutationId).text()
  const bodyInputId = "id_draft-content"
  const bodyInput = $("#" + bodyInputId)
  if (bodyInput) {
    bodyInput.attr("placeholder", memberSalutation)
    bodyInput.attr("required", "")
    bodyInput.attr("maxlength", "5000")
  }

  const nameAndEmailIds = ["id_draft-author_name", "id_draft-author_email"]
  const nameAndEmailPlaceholders = ["eg. Jane Smith", "eg. jane@email.com"]

  for (var i = 0; i < nameAndEmailIds.length; i++) {
    if ($("#" + nameAndEmailIds[i])) {
      input.attr("placeholder", nameAndEmailPlaceholders[i])
      input.attr("required", "")
      input.attr("maxlength", "256")
    }
  }

  // Toggle rotation on accordion icons
  const toggleButton = $(".info-expand__trigger").add("#show-message-tools-toggle")
  const svgIconClass = ".is--arrow-toggle"
  toggleButton.click(function (e) {
    e.preventDefault();
    $(this).find(svgIconClass).toggleClass("info-expand__trigger--open");
  });

  if (window.location.pathname == "/write-committees/draft/") {
    $(".page-wrapper").css("display", "block");
  }
  const navOpen = $("#nav-open");
  const navClose = $("#nav-close");
  const wrapperSubnav = $("#main-menu");
  navOpen.click(function (e) {
    e.preventDefault();
    navOpen.hide();
    navClose.show();
    wrapperSubnav.show(100);
    $("body").css("overflow", "hidden");
  });
  navClose.click(function (e) {
    e.preventDefault();
    navOpen.show();
    navClose.hide();
    wrapperSubnav.hide(100);
    $("body").css("overflow", "scroll");
  });

  function menuHoverActions() {
    $(".dropdown").on("mouseenter", function () {
      var dropdown = $(this).find(".dropdown-content-nav").html();
      $("#sub-menu-placeholder .dropdown-content-nav").html(dropdown);
      $('[data-toggle="tooltip"]').tooltip()
      $("#sub-menu-placeholder").show();
      $("#sub-menu-placeholder .dropdown-content-nav").show();
      $('.dropdown').removeClass("active-nav-hover");
      $(this).addClass("active-nav-hover");
    }).on("mouseleave", function () {
      $("#sub-menu-placeholder").hide();
      $("#sub-menu-placeholder .dropdown-content-nav").hide();
    })

    $("#sub-menu-placeholder").on("mouseenter", function () {
      $(this).show();
      $(this).find(".dropdown-content-nav").show();
    }).on("mouseleave", function () {
      $(this).hide();
      $(this).find(".dropdown-content-nav").hide();
      $(".dropdown").removeClass("active-nav-hover");
      $("#sub-menu-placeholder .dropdown-content-nav").html("");
    });
  }
  function mobileMenuTouchActions() {
    $(".subnav-link").on("click", function () {
      $(this).next(".dropdown-content-nav").toggle();
      $(this).find(".svg-icon").toggleClass("info-expand__trigger--open");

    })
  }

  $("#nav-section").on('mouseleave', function () {
    $(".dropdown").removeClass("active-nav-hover");
    $("#sub-menu-placeholder .dropdown-content-nav").html("");
  })
  window.addEventListener('resize', function (event) {
    if (window.innerWidth > 767) {
      $("body").css("overflow", "scroll");
      wrapperSubnav.show();
      menuHoverActions();
    } else {
      $(".dropdown-content-nav").hide();
      mobileMenuTouchActions()
    }
  }, true);

  if (window.innerWidth > 767) {
    menuHoverActions();
  } else {
    mobileMenuTouchActions()
  }
});
