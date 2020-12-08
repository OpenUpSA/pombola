# This command is intended to help with these issues:
#
#   https://github.com/mysociety/pombola/issues/599
#   https://github.com/mysociety/pombola/issues/600
#   https://github.com/mysociety/pombola/issues/601
#   https://github.com/mysociety/pombola/issues/602
#
# This script takes arguments are passed in on the command line.

from django.core.management.base import BaseCommand
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person, Position, PositionTitle, Place, Organisation


def yyyymmdd_to_approx(yyyymmdd):
    year, month, day = map(int, yyyymmdd.split('-'))
    return ApproximateDate(year, month, day)

class Command(BaseCommand):

    help = 'create new position for election winners, end aspirant positions'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

        parser.add_argument('--place',                help="The Place slug that the positions are linked to")
        parser.add_argument('--elected-organisation', help="The Organisation slug that the person is elected to")
        parser.add_argument('--aspirant-title',       help="The PositionTitle slug for aspirants")
        parser.add_argument('--aspirant-end-date',    help="The end date to apply to matching positions")
        parser.add_argument('--elected-person',       help="The Person slug of the winner")
        parser.add_argument('--elected-title',        help="The PositionTitle slug for elected position")
        parser.add_argument('--elected-subtitle',     help="Optional subtitle for elected position")
        parser.add_argument('--elected-start-date',   help="The start date to apply to matching positions")

    def handle(self, **options):
        
        print "Looking at '%s' in '%s'" % (options['elected_person'], options['place'] )

        # load up the place, org and positions
        place                 = Place.objects.get(slug=options['place'])
        organisation          = Organisation.objects.get(slug=options['elected_organisation'])
        aspirant_pos_title    = PositionTitle.objects.get(slug=options['aspirant_title'])
        elected_pos_title     = PositionTitle.objects.get(slug=options['elected_title'])
        elected_subtitle      = options['elected_subtitle'] or ''
        
        # convert the dates to approximate dates
        aspirant_end_date  = yyyymmdd_to_approx(options['aspirant_end_date'])
        elected_start_date = yyyymmdd_to_approx(options['elected_start_date'])
        future_date        = ApproximateDate(future=True)
        
        # get the winner
        elected = Person.objects.get(slug=options['elected_person'])

        # create (if needed) the elected positon.
        if options['commit']:
            elected_pos, created = Position.objects.get_or_create(
                person       = elected,
                title        = elected_pos_title,
                place        = place,
                organisation = organisation,
                start_date   = elected_start_date,
                defaults     = {
                    'end_date': future_date,
                    'subtitle': elected_subtitle,
                    'category': 'political',
                }
            )
            if created:
                print "  Created %s" % elected_pos
            

        # get all related aspirant positions
        for pos in Position.objects.filter(place=place, title=aspirant_pos_title).currently_active():
            print "  Ending %s" % pos
            pos.end_date = aspirant_end_date
            if options['commit']:
                pos.save()
