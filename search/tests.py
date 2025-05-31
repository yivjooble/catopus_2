from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO
from django.http import JsonResponse # For type checking if needed
from search.models import SearchResult # To check instance creation

User = get_user_model()

class IndexViewSyncQueryTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.index_url = reverse('search:index')

    @patch('search.views._handle_query_execution')
    def test_index_post_delegates_to_handle_query_execution_for_sync_query(self, mock_handle_query_execution):
        """
        Test that the main index view correctly delegates to _handle_query_execution
        for a standard synchronous query POST.
        """
        mock_response_data = {'table_html': '<table>query results</table>', 'identifier': 'uuid-test-sync', 'status': 'success'}
        # Simulate a JsonResponse object being returned by the handler
        mock_json_response = JsonResponse(mock_response_data)
        mock_handle_query_execution.return_value = mock_json_response

        post_data = {
            'query': 'SELECT * FROM table_sync',
            'selected_countries': ['US', 'CA'],
            'list_of_countries': 'US,CA',
            # No 'is_remote' and no 'action' implies synchronous query
        }
        response = self.client.post(self.index_url, data=post_data)

        self.assertTrue(mock_handle_query_execution.called)
        # Check that the first argument to the handler is the request object
        self.assertEqual(mock_handle_query_execution.call_args[0][1], post_data['query'])
        self.assertEqual(mock_handle_query_execution.call_args[0][2], post_data['selected_countries'])
        self.assertEqual(mock_handle_query_execution.call_args[0][3], post_data['list_of_countries'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_response_data)

    @patch('search.views.run_select')
    @patch('search.models.SearchResult.search_results_file.save') # Mock the file save part of the model field
    def test_handle_query_execution_successful_query(self, mock_file_field_save, mock_run_select):
        """
        Test the _handle_query_execution helper function's logic for a successful query.
        This is tested by calling the main index view which internally calls this helper.
        """
        # Prepare mock DataFrame
        mock_df_data = {'col1': [1, 2], 'col2': ['data1', 'data2']}
        mock_df = pd.DataFrame(mock_df_data)

        mock_run_select.return_value = (mock_df, None) # (result_df, a_priori_table_name)
        mock_file_field_save.return_value = None # search_results_file.save(...) doesn't need to return anything specific

        query_data = {
            'query': 'SELECT * FROM example_table',
            'selected_countries': ['FR', 'DE'],
            'list_of_countries': 'FR,DE',
            'custom_user_table_name': '' # Not saving to DB table initially
        }

        response = self.client.post(self.index_url, data=query_data)

        mock_run_select.assert_called_once_with(
            query_data['query'],
            query_data['selected_countries'],
            query_data['custom_user_table_name']
        )

        # Check that a SearchResult was created (implicitly, file was saved)
        self.assertTrue(mock_file_field_save.called)
        # Verify the name of the file being saved (optional, but good)
        # Example: mock_file_field_save.assert_called_once_with(ANY, ANY) where ANY are appropriate matchers
        # For now, just checking it was called is sufficient.

        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn('table_html', json_response)
        self.assertEqual(json_response['table_html'], mock_df.to_html(justify="left", index=False, border=0, classes="table table-hover table-sm", table_id="results-table"))
        self.assertIn('identifier', json_response)
        self.assertIsNotNone(json_response['identifier'])
        self.assertEqual(json_response['status'], 'success')
        self.assertIsNone(json_response['table_name']) # Since custom_user_table_name was empty

        # Verify SearchResult object creation
        # The identifier is random, so we fetch the latest SearchResult for this user
        self.assertTrue(SearchResult.objects.filter(user=self.user, sql_query=query_data['query']).exists())


    @patch('search.views.run_select')
    def test_handle_query_execution_empty_dataframe_result(self, mock_run_select):
        """
        Test _handle_query_execution when run_select returns an empty DataFrame.
        """
        empty_df = pd.DataFrame()
        mock_run_select.return_value = (empty_df, None)

        query_data = {
            'query': 'SELECT * FROM non_existent_table',
            'selected_countries': ['XX'],
            'list_of_countries': 'XX',
        }
        response = self.client.post(self.index_url, data=query_data)

        mock_run_select.assert_called_once_with(
            query_data['query'],
            query_data['selected_countries'],
            None # custom_user_table_name defaults to None if not provided
        )

        # According to views._handle_query_execution, an empty df renders a template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/index.html')
        self.assertContains(response, 'No results found.')

    def tearDown(self):
        # Logout the user if logged in during setUp
        self.client.logout()
        # Any other cleanup, though Django's TestCase usually handles DB rollback.
        # If SearchResult objects were created and not cleaned by transaction rollback (e.g. if file saving had side effects not in DB)
        # SearchResult.objects.all().delete() # But this is usually not needed.
        pass
