import datetime

from django import forms
from django.utils import timezone

from .models import Branch, JobApplication, Reservation


class StyledFormMixin:
    """Adds the site's input classes so templates can render fields directly."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            css = "field__input"
            if isinstance(widget, forms.Select):
                css = "field__input field__select"
            elif isinstance(widget, forms.Textarea):
                css = "field__input field__textarea"
            elif isinstance(widget, forms.ClearableFileInput):
                css = "field__input field__file"
            widget.attrs.setdefault("class", css)
            if field.required:
                widget.attrs.setdefault("required", "required")


class ReservationForm(StyledFormMixin, forms.ModelForm):
    # Hidden honeypot: real visitors never fill this in.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Reservation
        fields = ["branch", "date", "time", "guests", "occasion", "name", "phone", "email", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time", "min": "07:00", "max": "22:30", "step": 900}),
            "guests": forms.NumberInput(attrs={"min": 1, "max": 300}),
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your full name"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "07XX XXX XXX", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "Optional"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Allergies, seating preference, celebration details…"}),
        }
        labels = {"guests": "Number of guests", "occasion": "Occasion", "notes": "Anything we should know?"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].queryset = Branch.objects.filter(is_active=True)
        self.fields["branch"].empty_label = "Choose a branch"
        today = timezone.localdate()
        self.fields["date"].widget.attrs["min"] = today.isoformat()

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise forms.ValidationError("Please choose today or a future date.")
        if date > timezone.localdate() + datetime.timedelta(days=365):
            raise forms.ValidationError("We take bookings up to a year ahead.")
        return date

    def clean_guests(self):
        guests = self.cleaned_data["guests"]
        if not 1 <= guests <= 300:
            raise forms.ValidationError("Guests must be between 1 and 300.")
        return guests

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = [c for c in phone if c.isdigit()]
        if len(digits) < 9:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean(self):
        data = super().clean()
        date, time = data.get("date"), data.get("time")
        if date and time and date == timezone.localdate():
            now = timezone.localtime().time()
            if time < now:
                self.add_error("time", "That time has already passed today.")
        return data


class JobApplicationForm(StyledFormMixin, forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = JobApplication
        fields = ["first_name", "last_name", "email", "phone", "position", "start_date", "cv", "message"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "phone": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 4}),
            "cv": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx"}),
        }

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")
        if cv:
            if cv.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Please upload a file smaller than 5 MB.")
            if not cv.name.lower().endswith((".pdf", ".doc", ".docx")):
                raise forms.ValidationError("Please upload a PDF or Word document.")
        return cv
