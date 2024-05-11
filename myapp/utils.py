"""
Helper functions for views in myapp application.
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils.functional import SimpleLazyObject

from allauth.socialaccount.models import SocialAccount

from .forms import FileUploadForm
from .models import SiteUser, UserFile


def is_admin_email(email: str) -> bool:
    """Checks whether a user has an admin email."""
    # Look up the custom user model by email
    users = SiteUser.objects.filter(email=email)
    if len(users) == 0:
        return False
    else:
        return users[0].is_admin


def get_site_user(user: SimpleLazyObject) -> SiteUser | None:
    """Get the custom SiteUser from the Django HTTP request."""
    if not user.is_authenticated:
        # User is anonymous
        return None

    # User is logged in through Google
    oauth_user = get_social_account(user)
    if oauth_user:
        return get_site_user_from_social_user(oauth_user)

    # User is logged in through Django (should be a superuser)
    django_user = get_django_user(user)
    if django_user:
        return get_site_user_from_django_user(django_user)

    return None


def get_social_account(user: SimpleLazyObject) -> SocialAccount | None:
    """Get the social account user from the Django HTTP request."""
    # Get the social account
    user_set = user.socialaccount_set.all()
    if len(user_set) == 0:
        # Avoid index out of range error
        return None
    return user_set[0]


def get_django_user(user: SimpleLazyObject) -> User | None:
    """Get the Django user from the Django HTTP request."""
    email = user.email
    users_with_email = User.objects.filter(email=email)
    if len(users_with_email) == 0:
        # Somehow no Django user was created
        return None
    return users_with_email[0]


def get_site_user_from_social_user(oauth_user: SocialAccount) -> SiteUser:
    """Get the site user from the social account user or create one."""
    user_data = oauth_user.extra_data
    username = user_data['name']
    email = user_data['email']

    # Check if the custom user model has been created
    # Find the user by social account
    site_users_with_account = SiteUser.objects.filter(oauth_user=oauth_user)
    if len(site_users_with_account) == 0:
        # Create a new user
        site_user = SiteUser(oauth_user=oauth_user, username=username, email=email)
        site_user.save()
    else:
        # Use the existing user
        site_user = site_users_with_account[0]
    return site_user


def get_site_user_from_django_user(user: User) -> SiteUser:
    """Get the site user from the Django user or create one."""
    # Find site user with email
    email = user.email
    username = f"{user.first_name} {user.last_name}".strip()
    site_users_with_email = SiteUser.objects.filter(email=email)
    if len(site_users_with_email) == 0:
        # Create a new user
        site_user = SiteUser(oauth_user=None, username=username, email=email)
        site_user.save()
    else:
        # Use the existing user
        site_user = site_users_with_email[0]
    return site_user


# TODO don't clear the form every time we filter
def apply_report_filters(report_objects: QuerySet, filter_all, request, sort_ascending, sort_descending) -> QuerySet:
    """Filters a set of reports based on a form."""

    # Sources
    # - https://pytutorial.com/django-search-function/
    # - https://djangocentral.com/django-orm-cheatsheet/
    # - https://stackoverflow.com/questions/1981524/django-filtering-on-foreign-key-properties
    # - https://stackoverflow.com/questions/739776/how-do-i-do-an-or-filter-in-a-django-query

    filtered_reports = report_objects

    # Filter for category
    category_filter = request.POST.get('category', None)
    if category_filter and category_filter != filter_all:
        filtered_reports = filtered_reports.filter(category=category_filter)

    # Filter for status
    status_filter = request.POST.get('status', None)
    if status_filter and status_filter != filter_all:
        filtered_reports = filtered_reports.filter(status2=status_filter)

    # Filter for filename
    # Note: due to SQL limitations this searches the entire location (including AWS URL)
    file_filter = request.POST.get('file', None)
    if file_filter and file_filter != '':
        filtered_reports = filtered_reports.filter(user_file__location__icontains=file_filter)

    # Search for subject (case-insensitive)
    subject_search = request.POST.get('subject', None)
    if subject_search and subject_search != '':
        filtered_reports = filtered_reports.filter(subject__icontains=subject_search)

    # Search for uploader name/email (case-insensitive)
    user_search = request.POST.get('user', None)
    if user_search and user_search != '':
        contains_user = filtered_reports.filter(user__username__icontains=user_search)
        contains_email = filtered_reports.filter(user__email__icontains=user_search)
        filtered_reports = contains_user | contains_email

    # Sort by date
    date_sort_by = request.POST.get('date', None)
    if date_sort_by and date_sort_by == sort_descending:
        filtered_reports = filtered_reports.order_by('-uploaded_at')
    elif date_sort_by and date_sort_by == sort_ascending:
        filtered_reports = filtered_reports.order_by('uploaded_at')

    return filtered_reports


def upload_file_to_s3(request) -> UserFile | None:
    """Uploads a file to Amazon S3 and adds it to the database."""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            user_file = form.save(commit=False)

            if request.user.is_authenticated:
                user_file.user = get_site_user(request.user)

            # Save the S3 location link to the model
            file_object = request.FILES['file']
            file_name = file_object.name.replace(' ', '_')  # Replace spaces with underscores for AWS
            user_file.location = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/uploads/{file_name}"
            user_file.save()
            return user_file

    # The form/file is not valid
    return None
