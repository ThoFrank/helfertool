from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_bleach.models import BleachField
from collections import OrderedDict

from badges.models import BadgeDefaults


@python_2_unicode_compatible
class Job(models.Model):
    """ A job that contains min. 1 shift.

    Columns:
        :event: event of this job
        :name: name of the job, e.g, Bierstand
        :infection_instruction: is an instruction for the handling of food
                                necessary?
        :description: longer description of the job
        :job_admins: users, that can see and edit the helpers
        :public: job is visible publicly
        :badge_design: badge design for this job
    """

    event = models.ForeignKey(
        'Event',
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
    )

    public = models.BooleanField(
        default=False,
        verbose_name=_("This job is visible publicly"),
    )

    infection_instruction = models.BooleanField(
        default=False,
        verbose_name=_("Instruction for the handling of food necessary"),
    )

    description = BleachField(
        blank=True,
        verbose_name=_("Description"),
    )

    job_admins = models.ManyToManyField(
        User,
        blank=True,
    )

    coordinators = models.ManyToManyField(
        'Helper',
        blank=True,
    )

    badge_defaults = models.OneToOneField(
        BadgeDefaults,
        blank=True,
        null=True,
    )

    archived_number_coordinators = models.IntegerField(
        default=0,
        verbose_name=_("Number of coordinators for archived event"),
    )

    def __str__(self):
        return "%s" % self.name

    @property
    def num_coordinators(self):
        if self.event.archived:
            return self.archived_number_coordinators
        else:
            return self.coordinators.count()

    def is_admin(self, user):
        """ Check, if a user is admin of this job and returns a boolean.

        Superusers and admins of the event are also admins of a shift.

        :param user: the user
        :type user: :class:`django.contrib.auth.models.User`

        :returns: True or False
        """
        return self.event.is_admin(user) or \
            self.job_admins.filter(pk=user.pk).exists()

    def helpers_and_coordinators(self):
        helpers = Helper.objects.filter(shifts__job=self).distinct()
        coordinators = self.coordinators.distinct()
        return helpers | coordinators

    def shifts_by_day(self, shifts=None):
        """ Returns all shifts grouped sorted by day and sorted by time.

        The result is a dict with date objects as keys. Each item of the
        dictionary is a OrderedDict of shifts.

        :param shifts: list of shifts, must be shifts of this job (optional)
        :type shifts: list of Shift objects
        """
        tmp_shifts = dict()

        # no shifts are given -> use all shifts of this job
        if not shifts:
            shifts = self.shift_set.all()

        # iterate over all shifts and group them by day
        # (itertools.groupby is strange...)
        for shift in shifts:
            day = shift.begin.date()

            # add to list
            if day in tmp_shifts:
                tmp_shifts[day].append(shift)
            # or create begin list
            else:
                tmp_shifts[day] = [shift, ]

        # sort days
        ordered_shifts = OrderedDict(sorted(tmp_shifts.items(),
                                     key=lambda t: t[0]))

        # sort shifts
        for day in ordered_shifts:
            ordered_shifts[day] = sorted(ordered_shifts[day],
                                         key=lambda s: s.begin)

        return ordered_shifts


@receiver(pre_save, sender=Job, dispatch_uid='job_pre_save')
def job_pre_save(sender, instance, using, **kwargs):
    """ Add badge defaults if necessary.

    This is a signal handler, that is called, before a job is saved. It
    adds the badge defaults if badge creation is enabled and it is not
    there already.
    """
    if instance.event.badges and not instance.badge_defaults:
        defaults = BadgeDefaults()
        defaults.save()

        instance.badge_defaults = defaults

# moving the import down here fixes a problem with a circular import
from .helper import Helper
