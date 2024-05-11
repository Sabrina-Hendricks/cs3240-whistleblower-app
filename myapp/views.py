from django import template
from django.conf import settings
from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404

from .forms import FileUploadForm, ProfileUploadForm, ResolveForm, SubmitReportForm
from .models import ReportCategory, ReportForm, SiteUser, SubmissionStatus2
from .utils import apply_report_filters, get_site_user, is_admin_email, upload_file_to_s3

register = template.Library()


def index(request):
    """Redirect the user to the application homepage"""
    return redirect("myapp:home")


def home(request):
    """The user homepage, which displays after logging in."""
    site_user = get_site_user(request.user)
    is_logged_in = request.user.is_authenticated
    is_admin = is_logged_in and is_admin_email(request.user.email)
    user_file_form = FileUploadForm()

    context = {
        'site_user': site_user,
        'is_logged_in': is_logged_in,
        'is_admin': is_admin,
        'user_file_form': user_file_form,
    }
    return render(request, 'myapp/home.html', context)


def admin_reports(request):
    """List and review files uploaded by all users."""
    if not request.user.is_authenticated or not is_admin_email(request.user.email):
        return HttpResponse("You are not authorized to view this page.", status=403)

    site_user = get_site_user(request.user)
    report_objects = ReportForm.objects.order_by('-uploaded_at')
    return reports_view_helper(request, 'myapp/admin_reports.html', report_objects, site_user)


def user_reports(request):
    """List reports submitted by the current user."""
    if not request.user.is_authenticated:
        return HttpResponse("You must be logged in to view your reports.", status=403)

    site_user = get_site_user(request.user)
    report_objects = ReportForm.objects.filter(user=site_user).order_by('-uploaded_at')
    return reports_view_helper(request, 'myapp/user_reports.html', report_objects, site_user)


def reports_view_helper(request, template_name: str, report_objects: QuerySet, site_user: SiteUser) -> HttpResponse:
    """A helper method for generating user_reports and admin_reports views."""
    filter_all = 'All'  # Option to filter for all
    # filename_none = 'None'  # Option to search for no files
    sort_descending = 'Newest to Oldest'
    sort_ascending = 'Oldest to Newest'

    if request.method == "POST":
        filtered_reports = apply_report_filters(report_objects, filter_all, request, sort_ascending, sort_descending)
    else:
        filtered_reports = report_objects

    context = {
        'site_user': site_user,  # Needed for navbar
        'user_reports': filtered_reports,
        'category_choices': [filter_all] + ReportCategory.choices,
        'date_choices': [sort_descending, sort_ascending],
        'status_choices': [filter_all] + SubmissionStatus2.choices,
    }
    return render(request, template_name, context)


def report_view(request, report_id):
    """View and change the status of a user report."""
    user_report = get_object_or_404(ReportForm, id=report_id)
    is_admin = is_admin_email(request.user.email)
    site_user = get_site_user(request.user)

    if request.method == 'POST' and is_admin:
        resolve_form = ResolveForm(request.POST)
        if resolve_form.is_valid():
            action = request.POST.get('action')
            if action == 'update_comment':
                user_report.comments = resolve_form.cleaned_data['comments']
                user_report.save()
                messages.success(request, 'Comments updated successfully.')
            elif action == 'unresolve':
                user_report.comments = resolve_form.cleaned_data['comments']
                user_report.mark_unresolved()
                user_report.save()
                messages.success(request, 'Report marked as unresolved.')
            elif action == 'resolve':
                user_report.comments = resolve_form.cleaned_data['comments']
                user_report.mark_resolved()
                user_report.save()
                messages.success(request, 'Report marked as resolved.')
            return HttpResponseRedirect(request.path_info)
    else:
        # Initialize the form with existing comments
        resolve_form = ResolveForm(initial={'comments': user_report.comments})

    if is_admin and user_report.is_new():
        user_report.mark_in_progress()
        user_report.save()

    file_extension = user_report.user_file.get_extension() if user_report.user_file else None
    context = {
        'user_report': user_report,
        'file_extension': file_extension,
        'is_admin': is_admin,
        'resolve_form': resolve_form,
        'site_user': site_user
    }

    return render(request, 'myapp/report_view.html', context)


def report_form(request):
    if request.method == 'POST':
        form = SubmitReportForm(request.POST, request.FILES)

        if form.is_valid():
            # Upload the file
            user_file = None
            if 'file' in request.FILES:
                user_file = upload_file_to_s3(request)

            # Save the report to the DB
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.user = get_site_user(request.user)
            if user_file:
                report.user_file = user_file
            report.save()

            messages.success(request, 'Report submitted successfully.')
            return redirect('myapp:home')
    else:
        form = SubmitReportForm()

    site_user = get_site_user(request.user)
    user_is_admin = is_admin_email(request.user.email) if request.user.is_authenticated else False

    context = {
        'form': form,
        'category_choices': ReportCategory.choices,
        'is_admin': user_is_admin,
        'site_user': site_user
    }
    return render(request, 'myapp/report_form.html', context)


def faq(request):
    site_user = get_site_user(request.user)
    user_is_admin = is_admin_email(request.user.email) if request.user.is_authenticated else False

    context = {
        'is_admin': user_is_admin,
        'site_user': site_user
    }

    return render(request, 'myapp/faq.html', context)


def resources(request):
    site_user = get_site_user(request.user)
    user_is_admin = is_admin_email(request.user.email) if request.user.is_authenticated else False

    context = {
        'is_admin': user_is_admin,
        'site_user': site_user
    }

    return render(request, 'myapp/resources.html', context)


def manage_profile(request):
    site_user = get_site_user(request.user)

    if request.method == 'POST':
        form = ProfileUploadForm(request.POST, request.FILES)
        # TODO still displaying success message
        if form.is_valid():
            user_file = form.save(commit=False)
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                file_name = profile_picture.name.replace(' ', '_')
                user_file.location = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/uploads/{file_name}"
                user_file.save()

                site_user.profile_image = user_file.location
                site_user.save()

            messages.success(request, 'Profile picture updated successfully.')

        new_username = request.POST.get('username', '')
        if new_username and new_username != site_user.username:
            site_user.username = new_username
            site_user.save()
            messages.success(request, 'Username updated successfully.')

        return redirect('myapp:manage_profile')

    context = {
        'site_user': site_user,
        'form': ProfileUploadForm()  # Pass the form to your template
    }
    return render(request, 'myapp/manage_profile.html', context)


def delete_report(request, report_id):
    report = get_object_or_404(ReportForm, id=report_id)

    if request.method == 'POST' and 'confirm_delete' in request.POST:
        # Delete the associated file from Amazon S3
        if report.user_file:
            report.user_file.file.delete()
            report.user_file.delete()

        report.delete()
        messages.success(request, 'Report deleted successfully.')
        return redirect('myapp:user_reports')

    return render(request, 'myapp/user_reports.html', {'report': report, 'confirm_delete': True})


def aboutus(request):
    site_user = get_site_user(request.user)
    user_is_admin = is_admin_email(request.user.email) if request.user.is_authenticated else False

    context = {
        'is_admin': user_is_admin,
        'site_user': site_user
    }

    return render(request, 'myapp/aboutus.html', context)