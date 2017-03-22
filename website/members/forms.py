from django import forms
from django.contrib.sites.shortcuts import get_current_site
from django.core import validators
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailusers.forms import UserEditForm, UserCreationForm

from members.models import StudyProgram, Member


def send_confirmation_email(request, email, token):
    current_site = get_current_site(request)
    site_name = current_site.name
    domain = current_site.domain
    context = {
        'email': email,
        'domain': domain,
        'site_name': site_name,
        'token': token,
        'protocol': 'https' if request.is_secure() else 'http',
    }

    subject = loader.render_to_string(
        'members/email_change_subject.txt', context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string('members/email_change_email.html',
                                   context)

    email_message = EmailMultiAlternatives(subject, body, None, [email])

    email_message.send()


class MemberForm(forms.ModelForm):
    person_number = forms.CharField(
        max_length=13,
        min_length=12,
        help_text=_('Person number using the YYYYMMDD-XXXX format.'),
        validators=[validators.RegexValidator(
            regex=r'^\d{8}\-?\d{4}$',
            message=_('Use the format YYYYMMDD-XXXX for your person number.')
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYYMMDD-XXXX',
        })
    )
    new_email = forms.EmailField(label=_('email address'),
                                 widget=forms.EmailInput(
                                     attrs={'class': 'form-control'},
                                 ))

    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'phone_number',
                  'registration_year', 'study']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_year': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'study': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance is not None:
            kwargs.update(initial={
                'person_number': instance.person_number(),
                'new_email': instance.email,
            })

        super(MemberForm, self).__init__(*args, **kwargs)

    def save(self, request=None, commit=True):
        person_number = self.cleaned_data['person_number']
        self.instance.birthday = '%s-%s-%s' % (
            person_number[:4], person_number[4:6], person_number[6:8]
        )
        self.instance.person_number_ext = person_number[-4:]

        new_email = self.cleaned_data['new_email']
        token = self.instance.add_email_if_not_exists(new_email)
        if token is None:
            self.instance.set_primary_email(new_email)
        else:
            send_confirmation_email(request, new_email, token)

        return super(MemberForm, self).save(commit=commit)


class CustomUserEditForm(UserEditForm):
    """
    Custom form to edit users from within the wagtail admin interface.
    """
    birthday = forms.DateField(required=True, label=_('Birthday'))
    person_number_ext = forms.CharField(
        required=True,
        label=_('Person number extension')
    )
    phone_number = forms.CharField(
        required=False,
        label=_('Phone number')
    )
    registration_year = forms.CharField(
        required=False,
        label=_('Registration year')
    )
    study = forms.ModelChoiceField(
        required=False,
        queryset=StudyProgram.objects,
        label=_("Study Program")
    )


class CustomUserCreationForm(UserCreationForm):
    """
    Custom form to create user from within the Wagtail admin user interface.
    """
    birthday = forms.DateField(required=True, label=_('Birthday'))
    person_number_ext = forms.CharField(
        required=True,
        label=_('Person number extension')
    )
    phone_number = forms.CharField(
        required=False,
        label=_('Phone number')
    )
    registration_year = forms.CharField(
        required=False,
        label=_('Registration year')
    )
    study = forms.ModelChoiceField(
        required=False,
        queryset=StudyProgram.objects,
        label=_("Study Program")
    )
