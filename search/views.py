import json
import pandas as pd
import logging
import uuid
import ast
import os
import winrm

# built in modules
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import Http404
from django.core.files.base import ContentFile
from django.utils import timezone

# third-party modules
from io import BytesIO
from dotenv import load_dotenv

# custom modules
from .multiprocessing import run_select
from .tasks import run_sql_query_remotely
from catopus.utils.database import create_db_sqlalchemy_engine

load_dotenv()

logger = logging.getLogger('search')




def save_table_to_db(result_df, table_name: str):
    logger.info(f"user provides custom table name to save into db: {table_name}")
    db_table_name = str(table_name) + '_' + timezone.now().strftime("%Y%m%d_%H_%M_%S")

    result_df.to_sql(
        db_table_name,
        con=create_db_sqlalchemy_engine(
            os.environ.get('DWH_HOST'),
            os.environ.get('DWH_DB'),
            os.environ.get('DWH_USER'),
            os.environ.get('DWH_PASSWORD')),
        schema='catopus',
        index=False,
        chunksize=10000)
    return db_table_name


@login_required
def index(request):
    # Move the import statement inside the view function
    from .models import SearchResult
    import base64

    try:
        if request.method == 'POST':
            # define all main variable to run sql query
            query_field = request.POST.get('query')
            list_of_countries = request.POST.get('list_of_countries')
            selected_countries_row = request.POST.getlist('selected_countries')
            selected_countries = [country.split(',') for country in selected_countries_row][0] if selected_countries_row else []

            result_df = pd.DataFrame()

            # if "remote_start", run sql query behind the main project by celery + redis
            if request.POST.get('is_remote') == 'remote_start':
                run_sql_query_remotely(request.user, query_field, selected_countries, list_of_countries)
            
            elif request.POST.get('action') == 'save_table':
                # Get the DataFrame from the session as a binary parquet string
                base64_parquet_data = request.session.get('result_df', None)

                if base64_parquet_data:
                    # Read the parquet binary string back as a DataFrame
                    parquet_data = base64.b64decode(base64_parquet_data)
                    get_result_df_from_session = pd.read_parquet(BytesIO(parquet_data))

                    # Step 1: get customer table name + dataframe to pass to saver
                    customer_table_name = request.POST.get('table_name')

                    # Step 2: get name of table already saved to db, pass it to html page
                    post_factum_table = save_table_to_db(get_result_df_from_session, customer_table_name)

                    # Step 3: pass name of saved table to a .html page, action: "save_table"
                    return JsonResponse({'post_factum_table': post_factum_table})
            
            else:
                # Default customer_table_name=None, if exists > will create a table in db
                customer_table_name = request.POST.get('custom_user_table_name')

                result = run_select(query_field, selected_countries, customer_table_name)

                if isinstance(result, tuple):
                    result_df, a_priori_table_name = result
                else:
                    result_df = result
                    a_priori_table_name = None

                if result_df is None:
                    logger.error(f'result_df is None: {result_df}')
                else:
                    # Save the DataFrame to a compressed file
                    buffer = BytesIO()
                    result_df.to_parquet(buffer, compression='gzip')
                    buffer.seek(0)

                    # Save the DataFrame in the session as a binary parquet string
                    request.session['result_df'] = base64.b64encode(buffer.getvalue()).decode()

                    # Generate a unique identifier
                    identifier = str(uuid.uuid4())

                    # Create a new SearchResult instance
                    search_result = SearchResult(identifier=identifier, user=request.user, sql_query=query_field, countries=selected_countries, countries_list=list_of_countries)
                    search_result.search_results_file.save(f"{identifier}.parquet.gzip", ContentFile(buffer.getvalue()))
                    search_result.save()


                if result_df.empty:
                    return render(request, 'search/index.html')
                else:
                    table_html = result_df.to_html(justify="left", 
                                                index=False,
                                                border=0,
                                                classes="table table-hover table-sm",
                                                table_id="results-table")
                    return JsonResponse({'table_html': table_html, 
                                         'identifier': identifier,
                                         'table_name': a_priori_table_name if a_priori_table_name else None})

        return render(request, 'search/index.html')
    except Exception as e:
        logger.error(f"index ERROR: {e}")
        return render(request, 'search/index.html')


@login_required
def share_results(request, identifier):
    from .models import SearchResult

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
    from .models import SearchResult

    search_log = SearchResult.objects.filter(user=request.user).order_by('-created_at').values('user_id', 'created_at', 'sql_query', 'countries_list', 'countries')

    context = {'search_result': search_log}
    return render(request, 'search/history.html', context)


@login_required
def run_bat_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            project_name = data.get('project_name')
            path_to_project = {
                'Dagster_dwh_etl_DEV': r"C:\Users\yiv\dwh_projects\dagster-etl-dev\dagster-etl\dagster_etl_dev_git_pull.bat",
                'Dagster_dwh_etl_PROD': r"C:\Users\yiv\dwh_new\gitlab\dagster-etl\dagster_etl_prod_git_pull.bat",
                'DREDD_DEV': r"C:\Users\yiv\dwh_projects\dredd_stage_dev\dredd-significance-tool\dredd_dev_git_pull.bat",
                'DREDD_PROD': r"C:\Users\yiv\dwh_projects\dredd-significance-tool\dredd_git_pull.bat",
                'DWH_SCRIPTS': r"C:\Users\yiv\dwh_projects\dwh-scripts\remote_git_pull.bat"
            }
            
            session = winrm.Session(
                f"{os.environ.get('host')}:5985",
                auth=(os.environ.get('username'), os.environ.get('password')),
                transport='ntlm'
            )
            
            # Get the command to run based on the project name
            cmd_to_run = path_to_project.get(project_name)
            
            if cmd_to_run:
                result = session.run_cmd(cmd_to_run)
                
                if result.status_code == 0:
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({
                        'status': 'fail',
                        'error': result.std_err.decode('utf-8')
                    })
            else:
                return JsonResponse({
                    'status': 'fail',
                    'error': f'Invalid project name: {project_name}'
                })
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})

    return JsonResponse({'status': 'fail', 'error': 'Not a POST request'})


@login_required
def python_etl(request):

    return render(request, 'search/python-etl.html')


@login_required
def remote(request):
    from .models import RemoteLogs

    remote_log = RemoteLogs.objects.filter(user_id=request.user).order_by('-updated_on').values('user_id', 'status', 'sql_query', 'table_name_created', 'log_field', 'countries_list', 'countries', 'run_on', 'updated_on')

    context = {'remote_log': remote_log}
    return render(request, 'search/remote.html', context)


@login_required
def saved_scripts(request):
    from .models import SavedScripts

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