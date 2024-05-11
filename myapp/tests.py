from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from allauth.socialaccount.models import SocialAccount

from .models import ReportCategory, ReportForm, SiteUser, SubmissionStatus2, UserFile

import os


class HomePageTests(TestCase):
    """Tests for the user homepage (/home)."""

    def test_can_view_home_page(self):
        """The home page works with no errors (i.e. Postgres, OAuth)."""
        response = self.client.get(reverse("myapp:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Report an Athlete Homepage")

    def test_can_view_anonymous_homepage(self):
        """The anonymous user homepage displays correctly."""
        response = self.client.get(reverse("myapp:home"), context={'site_user': None})

        self.assertContains(response, "Report an Athlete Homepage")
        self.assertContains(response, "anonymous")
        self.assertContains(response, "Log In")
        self.assertIs(response.context['site_user'], None)


class UserAccessTests(TestCase):
    def setUp(self):
        # Create a normal user and an admin user
        create_test_user('user', 'userpassword', 'user@example.com', '1', False)
        create_test_user('admin', 'adminpassword', 'admin@example.com', '2', True)

        self.client = Client()

    def test_admin_access(self):
        # Test that the admin user can access the admin files view
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse("myapp:admin_reports"))
        self.assertEqual(response.status_code, 200)

    def test_user_access_admin_page(self):
        # Test that a regular user cannot access the admin files view
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse("myapp:admin_reports"))
        self.assertEqual(response.status_code, 403)

    def test_user_access_user_page(self):
        # Test that a regular user can access the user files view
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse("myapp:user_reports"))
        self.assertEqual(response.status_code, 200)


class FileUploadTests(TestCase):
    def setUp(self):
        self.test_filename = 'testfile.txt'
        with open(self.test_filename, 'w') as file:
            file.write('Hello World')

    def test_file_upload(self):
        # Test anonymous file upload functionality
        with open(self.test_filename, 'rb') as file:
            uploaded_file = SimpleUploadedFile('testfile.txt', file.read(), content_type='text/plain')
            form_data = {
                'subject': 'test report',
                'category': ReportCategory.OTHER,
                'summary': 'uploading a test file',
                'file': uploaded_file,
            }
            response = self.client.post(reverse('myapp:report_form'), form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Report submitted successfully.', response.content.decode())

    def tearDown(self):
        os.remove(self.test_filename)  # Delete the test file


class FileResolutionTests(TestCase):
    def setUp(self):
        # Create an admin user
        create_test_user('admin', 'adminpassword', 'admin@example.com', '2', True)

        # Create a test report
        test_file = UserFile.objects.create(
            user=None, location='http://example.com/testfile.txt', file='testfile.txt'
        )
        self.test_report = ReportForm.objects.create(user_file=test_file)

    def test_file_resolution_by_admin(self):
        # Test that an admin can resolve a file
        self.client.login(username='admin', password='adminpassword')
        url = reverse(f'myapp:report_view', kwargs={'report_id': self.test_report.id})
        response = self.client.post(url, {'action': 'resolve', 'comments': 'Resolved by admin.'}, follow=True)
        self.test_report.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.test_report.comments, 'Resolved by admin.')
        self.assertEqual(self.test_report.status2, SubmissionStatus2.RESOLVED)


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')

    def test_home_page_renders(self):
        response = self.client.get(reverse('myapp:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'myapp/home.html')

    def test_upload_file_view(self):
        response = self.client.get(reverse('myapp:report_form'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'myapp/report_form.html')


# User Helper Functions
def create_test_user(username: str, password: str, email: str, uid: str, is_admin: bool = False):
    # Django user model
    user_object = User.objects.create_user(username=username, password=password, email=email)

    # Allauth user model
    extra_data = {'name': username, 'email': email}
    social_account_object = SocialAccount.objects.create(
        user=user_object, provider="google", uid=uid, extra_data=extra_data
    )

    # Whistleblower user model
    SiteUser.objects.create(
        oauth_user=social_account_object, username=username, email=email, is_admin=is_admin
    )
