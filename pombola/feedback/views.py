from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

from pombola.core.recaptcha import recaptcha_client

from models import Feedback
from forms import FeedbackForm

import re


@csrf_protect
def add(request):
    """Gather feedback for a page, and if it is ok show a thanks message and link back to the page."""

    submit_was_success = False
    return_to_url      = None
    submit_error_message  = None

    # If it is a post request try to create the feedback
    if request.method == 'POST':
        form = FeedbackForm( request.POST )
        recaptcha_response = request.POST.get("g-recaptcha-response", None)

        if form.is_valid():
            feedback = Feedback()
            feedback.url      = form.cleaned_data['url']
            feedback.email    = form.cleaned_data['email']
            feedback.comment  = form.cleaned_data['comment']

            submit_was_success = True

            if not recaptcha_client.verify(recaptcha_response):
                submit_was_success = False
                submit_error_message = "Sorry, something went wrong. Please try again or email us at <a href='mailto:contact@pa.org.za'>contact@pa.org.za</a>"
            
            # if the comment starts with an html tag it is probably spam
            if re.search('\A\s*<\w+>', form.cleaned_data['comment']):
                feedback.status = 'spammy'

            if request.user.is_authenticated():
                feedback.user = request.user

            if submit_was_success:
                feedback.save()

            return_to_url = feedback.url or None
        
    else:
        # use GET to grab the url if set
        form = FeedbackForm(initial=request.GET)
        
    
    return render_to_response(
        'feedback/add.html',
        {
            'form':               form,
            'submit_was_success': submit_was_success,
            'return_to_url':      return_to_url,
            'submit_error_message': submit_error_message
        },
        context_instance=RequestContext(request)
    )
