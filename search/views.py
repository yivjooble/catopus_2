import ast
import base64
import json
import logging
import os
import uuid
from io import BytesIO

import pandas as pd
# import winrm # Commented out as per request
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from dotenv import load_dotenv

from catopus.utils.database import create_db_sqlalchemy_engine

from .models import RemoteLogs, SavedScripts, SearchResult
from .multiprocessing import run_select
from .tasks import run_sql_query_remotely

load_dotenv()

logger = logging.getLogger('search')


def _handle_remote_execution(request, query_field, selected_countries, list_of_countries):
    run_sql_query_remotely(request.user, query_field, selected_countries, list_of_countries)
    return JsonResponse({'status': 'processing', 'message': 'Remote execution started.'})


def _handle_save_table(request):
    identifier = request.POST.get('identifier')
    customer_table_name = request.POST.get('table_name')

    if not identifier or not customer_table_name:
        logger.warning("Identifier or table_name missing in 'save_table' request.")
        return JsonResponse({'status': 'error', 'message': 'Missing identifier or table name.'}, status=400)

    try:
        search_result = SearchResult.objects.get(identifier=identifier, user=request.user)
        parquet_file = search_result.search_results_file
        parquet_file.open('rb') # Ensure file pointer is at the beginning
        df_to_save = pd.read_parquet(BytesIO(parquet_file.read()))
        parquet_file.close()

        if df_to_save.empty:
            logger.info(f"DataFrame for identifier {identifier} is empty. Nothing to save.")
            return JsonResponse({'status': 'info', 'message': 'No data to save.'})

        post_factum_table = save_table_to_db(df_to_save, customer_table_name)
        logger.info(f"Table '{post_factum_table}' saved successfully for identifier {identifier}.")
        return JsonResponse({'post_factum_table': post_factum_table, 'status': 'success'})
    except SearchResult.DoesNotExist:
        logger.error(f"SearchResult with identifier {identifier} not found for user {request.user}.")
        return JsonResponse({'status': 'error', 'message': 'Invalid identifier or unauthorized.'}, status=404)
    except Exception as e:
        logger.error(f"Error saving table for identifier {identifier}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)


def _handle_query_execution(request, query_field, selected_countries, list_of_countries):
    customer_table_name = request.POST.get('custom_user_table_name')
    result = run_select(query_field, selected_countries, customer_table_name)

    result_df = pd.DataFrame()
    a_priori_table_name = None

    if isinstance(result, tuple) and len(result) == 2:
        result_df, a_priori_table_name = result
    elif isinstance(result, pd.DataFrame):
        result_df = result
    else:
        logger.error(f"Unexpected result type from run_select: {type(result)}")
        # Potentially return an error response or an empty DataFrame response
        return JsonResponse({'status': 'error', 'message': 'Failed to execute query.'}, status=500)


    if result_df is None or result_df.empty:
        logger.info(f"Query returned no results or an error occurred. Query: {query_field}, Countries: {selected_countries}")
        # Return an empty table or a message, but ensure identifier is still part of it for consistency if needed later
        # For now, returning render as original code did for empty df.
        # Consider if JsonResponse with a specific status/message is better.
        return render(request, 'search/index.html', {'message': 'No results found.'}) # Or JsonResponse

    # Save the DataFrame to a compressed file
    buffer = BytesIO()
    result_df.to_parquet(buffer, compression='gzip')
    buffer.seek(0)

    identifier = str(uuid.uuid4())
    search_result_instance = SearchResult(
        identifier=identifier,
        user=request.user,
        sql_query=query_field,
        countries=selected_countries,
        countries_list=list_of_countries
    )
    search_result_instance.search_results_file.save(f"{identifier}.parquet.gzip", ContentFile(buffer.getvalue()))
    # search_result_instance.save() # .save() is called by search_results_file.save() if instance is new

    table_html = result_df.to_html(
        justify="left",
        index=False,
        border=0,
        classes="table table-hover table-sm",
        table_id="results-table"
    )
    return JsonResponse({
        'table_html': table_html,
        'identifier': identifier,
        'table_name': a_priori_table_name if a_priori_table_name else None,
        'status': 'success'
    })


def save_table_to_db(result_df, table_name: str):
    logger.info(f"User provides custom table name to save into db: {table_name}")
    db_table_name = str(table_name) + '_' + timezone.now().strftime("%Y%m%d_%H_%M_%S")

    result_df.to_sql(
        db_table_name,
        con=create_db_sqlalchemy_engine(
            settings.DATABASES['default']['HOST'],
            settings.DATABASES['default']['NAME'],
            settings.DATABASES['default']['USER'],
            settings.DATABASES['default']['PASSWORD']),
        schema='catopus',
        index=False,
        chunksize=10000)
    return db_table_name


@login_required
def index(request):
    if request.method == 'POST':
        try:
            query_field = request.POST.get('query')
            list_of_countries = request.POST.get('list_of_countries')
            selected_countries_row = request.POST.getlist('selected_countries')
            # Ensure selected_countries is a list, even if empty
            selected_countries = [country.split(',') for country in selected_countries_row][0] if selected_countries_row and selected_countries_row[0] else []


            if request.POST.get('is_remote') == 'remote_start':
                if not query_field or not selected_countries:
                    logger.warning("Missing query_field or selected_countries for remote_start.")
                    return JsonResponse({'status': 'error', 'message': 'Query and countries are required for remote execution.'}, status=400)
                return _handle_remote_execution(request, query_field, selected_countries, list_of_countries)
            
            elif request.POST.get('action') == 'save_table':
                return _handle_save_table(request)
            
            else:
                # Default action: execute query
                if not query_field : # selected_countries can be empty for some queries
                    logger.warning("Missing query_field for query execution.")
                    return JsonResponse({'status': 'error', 'message': 'Query is required.'}, status=400)
                return _handle_query_execution(request, query_field, selected_countries, list_of_countries)

        except Exception as e:
            # General error logging for POST requests
            logger.error(f"Error processing POST request in index view: {e}", exc_info=True) # exc_info=True logs stack trace
            # Provide a user-friendly error message
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred. Please try again.'}, status=500)

    # For GET requests or if POST processing falls through without returning a response (should not happen with current logic)
    return render(request, 'search/index.html')


@login_required
def share_results(request, identifier):
    try:
        search_result = SearchResult.objects.get(identifier=identifier)
        result_df = pd.read_parquet(BytesIO(search_result.search_results_file.read()))
        selected_countries = ast.literal_eval(search_result.countries)

        table_html = result_df.to_html(justify="left",
                                       index=False,
                                       border=0,
                                       classes="table table-hover table-sm")
        context = {'table_html': table_html, 
                   'identifier': identifier,
                   'input_query': search_result.sql_query,
                   'selected_countries': json.dumps(selected_countries)}
        
        return render(request, 'search/index.html', context)
    except SearchResult.DoesNotExist:
        raise Http404("Search result not found")
    

@login_required
def history(request):
    search_log = SearchResult.objects.filter(user=request.user).order_by('-created_at').values('user_id', 'created_at', 'sql_query', 'countries_list', 'countries')

    context = {'search_result': search_log}
    return render(request, 'search/history.html', context)


# @login_required
# def run_bat_file(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body.decode('utf-8'))
#             project_name = data.get('project_name')
#             path_to_project = {
#                 'Dagster_dwh_etl_DEV': r"C:\Users\yiv\dwh_projects\dagster-etl-dev\dagster-etl\dagster_etl_dev_git_pull.bat",
#                 'Dagster_dwh_etl_PROD': r"C:\Users\yiv\dwh_new\gitlab\dagster-etl\dagster_etl_prod_git_pull.bat",
#                 'DREDD_DEV': r"C:\Users\yiv\dwh_projects\dredd_stage_dev\dredd-significance-tool\dredd_dev_git_pull.bat",
#                 'DREDD_PROD': r"C:\Users\yiv\dwh_projects\dredd-significance-tool\dredd_git_pull.bat",
#                 'DWH_SCRIPTS': r"C:\Users\yiv\dwh_projects\dwh-scripts\remote_git_pull.bat"
#             }
            
#             session = winrm.Session(
#                 f"{os.environ.get('host')}:5985",
#                 auth=(os.environ.get('username'), os.environ.get('password')),
#                 transport='ntlm'
#             )
            
#             # Get the command to run based on the project name
#             cmd_to_run = path_to_project.get(project_name)
            
#             if cmd_to_run:
#                 result = session.run_cmd(cmd_to_run)
                
#                 if result.status_code == 0:
#                     return JsonResponse({'status': 'success'})
#                 else:
#                     return JsonResponse({
#                         'status': 'fail',
#                         'error': result.std_err.decode('utf-8')
#                     })
#             else:
#                 return JsonResponse({
#                     'status': 'fail',
#                     'error': f'Invalid project name: {project_name}'
#                 })
#         except Exception as e:
#             return JsonResponse({'status': 'fail', 'error': str(e)})

#     return JsonResponse({'status': 'fail', 'error': 'Not a POST request'})


@login_required
def python_etl(request):

    return render(request, 'search/python-etl.html')


@login_required
def remote(request):
    remote_log = RemoteLogs.objects.filter(user_id=request.user).order_by('-updated_on').values('user_id', 'status', 'sql_query', 'table_name_created', 'log_field', 'countries_list', 'countries', 'run_on', 'updated_on')

    context = {'remote_log': remote_log}
    return render(request, 'search/remote.html', context)


@login_required
def saved_scripts(request):
    if request.method == 'POST':
        user_id = request.user
        sql_query = request.POST.get('sql_query')
        countries_list = request.POST.get('countries_list')
        countries_row = request.POST.getlist('selected_countries')
        countries = [country.split(',') for country in countries_row][0] if countries_row else []

        to_save_script = SavedScripts(
            user_id=user_id,
            sql_query= sql_query,
            countries_list=countries_list,
            countries=countries)
        
        to_save_script.save()

    saved_scripts = SavedScripts.objects.filter(user_id=request.user).order_by('-saved_on').values('user_id', 'sql_query', 'countries_list', 'countries', 'saved_on', 'updated_on', 'deleted_on')

    context = {'saved_scripts': saved_scripts} 

    return render(request, 'search/saved-scripts.html', context)