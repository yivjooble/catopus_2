from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.conf import settings # Required for checking if settings.LOGIN_REDIRECT_URL is used

# Use Django's User model if appropriate, or a custom one if your project uses it.
User = get_user_model()

class LoginViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Ensure 'account' namespace is used if defined in account/urls.py
        # If app_name = 'account' is set in account/urls.py, then 'account:login'
        # If not, it might just be 'login' if it's a root URL in the project.
        # Based on previous subtasks, assuming 'account' app_name for URLs.
        try:
            self.login_url = reverse('account:login')
        except Exception:
            # Fallback if namespace isn't 'account' or URL name is different
            # This might happen if the project structure differs slightly.
            # For this exercise, we'll assume 'account:login' is correct.
            # If tests fail here, this is a point to check.
            self.login_url = reverse('login') # A common default name

    @patch('django.contrib.auth.authenticate')
    @patch('django.contrib.auth.login')
    def test_login_view_successful_login(self, mock_login, mock_authenticate):
        mock_user = MagicMock(spec=User)
        mock_authenticate.return_value = mock_user

        login_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }

        # Assuming the view uses request.POST.get('username') and request.POST.get('password')
        # The actual form field names in the template are 'username' and 'password'.
        response = self.client.post(self.login_url, data=login_data)

        mock_authenticate.assert_called_once_with(username='testuser', password='testpassword')
        mock_login.assert_called_once_with(response.wsgi_request, mock_user)

        # Check for redirect. Default is settings.LOGIN_REDIRECT_URL which is '/'
        # In this project, LOGOUT_REDIRECT_URL = '/account/login/'
        # LOGIN_REDIRECT_URL is not explicitly set, so Django's default is /accounts/profile/
        # However, the login_view in this app redirects to 'search:index' on success.
        self.assertRedirects(response, reverse('search:index'))

    @patch('django.contrib.auth.authenticate')
    @patch('django.contrib.auth.login')
    def test_login_view_failed_login(self, mock_login, mock_authenticate):
        mock_authenticate.return_value = None

        login_data = {
            'username': 'wronguser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data=login_data)

        mock_authenticate.assert_called_once_with(username='wronguser', password='wrongpassword')
        mock_login.assert_not_called()

        # The view returns HttpResponse('Invalid credentials')
        # This means status code 200 is expected, and the content should be checked.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_login_view_get_request(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        # Based on `account/templates/account/pages-login.html`
        self.assertTemplateUsed(response, 'account/pages-login.html')
