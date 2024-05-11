"""
Forms for the views in the myapp application.
"""
from django import forms

from .models import UserFile, ReportForm


class FileUploadForm(forms.ModelForm):
    """Allows a user to attach a file upload to a report."""

    class Meta:  # Form metadata
        model = UserFile
        fields = ['file']

    file = forms.FileField(required=False)

    def clean_file(self):
        # Check the file type
        file = self.cleaned_data.get('file')
        if file:
            file_extension = file.name.split('.')[-1].lower()
            allowed_extensions = ['txt', 'pdf', 'jpg', 'jpeg', 'png']
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Only .txt, .pdf, .jpg, and .png files are allowed.")
        return file


class ProfileUploadForm(forms.ModelForm):
    """Allows a user to change their profile picture."""

    class Meta:  # Form metadata
        model = UserFile
        fields = ['profile_picture']

    profile_image = forms.ImageField(required=False)

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            print(f"prof pic: {profile_picture}")
            # Check the file type
            file_extension = profile_picture.name.split('.')[-1].lower()
            print(f"ext: {file_extension}")
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Only .jpg, .png, and .gif files are allowed.")
            # TODO Additional checks can be added here, e.g., file size
        return profile_picture


class SubmitReportForm(forms.ModelForm):
    """Allows a user to submit a report to the website."""

    class Meta:
        model = ReportForm
        fields = ['subject', 'category', 'summary']


class ResolveForm(forms.Form):
    """Marks a user submission as resolved and adds comments."""
    comments = forms.CharField(widget=forms.Textarea(attrs={'cols': 50, 'rows': 3}), required=True)
