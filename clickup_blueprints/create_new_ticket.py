import argparse
import sys
import requests
import re
from datetime import datetime
from ast import literal_eval
import shipyard_utils as shipyard
try:
    import exit_codes
except BaseException:
    from . import exit_codes


# create Artifacts folder paths
base_folder_name = shipyard.logs.determine_base_artifact_folder('clickup')
artifact_subfolder_paths = shipyard.logs.determine_artifact_subfolders(
    base_folder_name)
shipyard.logs.create_artifacts_folders(artifact_subfolder_paths)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-id', dest='list_id', required=True)
    parser.add_argument('--access-token', dest='access_token', required=True)
    parser.add_argument('--name', dest='name', required=True)
    parser.add_argument('--description', dest='description', required=True)
    parser.add_argument('--priority', dest='priority', required=False)
    parser.add_argument('--status', dest='status', required=False)
    parser.add_argument('--due-date', dest='due_date', required=False)
    parser.add_argument('--start-date', dest='start_date', required=False)
    parser.add_argument('--assigness', dest='assignees', required=False)
    parser.add_argument('--time_estimate', dest='time_estimate', required=False)
    parser.add_argument('--tags', dest='tags', required=False)
    parser.add_argument('--custom-json', dest='custom_json', required=False)
    parser.add_argument(
        '--source-file-name',
        dest='source_file_name',
        required=False)
    parser.add_argument(
        '--source-folder-name',
        dest='source_folder_name',
        default='',
        required=False)
    parser.add_argument('--source-file-name-match-type',
                        dest='source_file_name_match_type',
                        choices={'exact_match', 'regex_match'},
                        default='exact_match',
                        required=False)
    args = parser.parse_args()
    return args


def create_task(list_id, token, name, description, assignees=[], tags=[], status=None, priority=None,
                due_date=None, time_estimate=None, start_date=None, custom_fields=None):
    """ Triggers the Create Task API and adds a new task onto ClickUp
    see: https://jsapi.apiary.io/apis/clickup20/reference/0/tasks/create-task.html
    """
    
    create_task_api = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    headers = {
      'Authorization': token,
      'Content-Type': 'application/json'
    }
    payload = {
        "name": name,
        "description": description,
        "assignees": assignees,
        "tags": tags,
        "status": status,
        "due_date": due_date,
        "time_estimate": time_estimate,
        "notify_all": True,
    }
    if start_date:
        payload['start_date'] = start_date
    if priority:
        payload['priority'] = priority
    if custom_fields:
        payload['check_required_custom_fields'] = True
        payload['custom_fields'] = custom_fields

    response = requests.post(create_task_api, 
                             headers=headers, 
                             json=payload
                             )
    
    if response.status_code == 200: # created successfuly
        task_id =  response.json()['id']
        print(f"Task created successfully with task name: {task_id}")
        return response.json()
        
    elif response.status_code == 401: # Permissions Error
        print("Clickup permissions error: check if token is correct",
              f"and you have access to the specified list: {list_id}")
        sys.exit(exit_codes.INVALID_CREDENTIALS)

    elif response.status_code == 400: # Bad Request
        print("Clickup responded with Bad Request Error. ",
              f"Response message: {response.text}")
        sys.exit(exit_codes.BAD_REQUEST)

    else: # Some other error
        print(
            f"an Unknown HTTP Status {response.status_code} and response occurred when attempting your request: ",
            f"{response.text}"
        )
        sys.exit(exit_codes.UNKNOWN_ERROR)


def upload_file_attachment(token, task_id, file_path):
    """ Uploads files to Clickup API """

    upload_endpoint = f"https://api.clickup.com/api/v2/task/{task_id}/attachment"

    headers = {
      'Content-Type': 'multipart/form-data',
      "Authorization": token
    }
    file_payload = {
        "file": (file_path, open(file_path, "rb"), "application-type")
    }
    response = requests.post(upload_endpoint,
                             headers=headers,
                             files=file_payload)

    if response.status_code == 200:
        print(f'{file_path} was successfully uploaded to {task_id}')
    return response.json()


def get_member_ids_from_names(token, list_id, members):
    """Gets the Clickup Member id given array of members names and list ID"""
    get_url = f"https://api.clickup.com/api/v2/list/{list_id}/member"

    headers = {
        "Authorization": token
    }
    get_response = requests.get(get_url, headers=headers)
    if get_response.status_code == 200:
        member_data = get_response.json()
        # find and return the label
        member_ids = [
            member['id'] for member in member_data if member['name'] in members
        ]
        return member_ids


def date_to_epoch_time(shipyard_date):
    """ Converts a Shipayrd formatted date to epoch time"""
    str_as_date = datetime.strptime(shipyard_date, '%m/%d/%Y')
    converted_date = int(str_as_date.timestamp())
    return converted_date

def main():
    args = get_args()
    access_token = args.access_token
    list_id = args.list_id
    name = args.name
    description = args.description
    priority = args.priority
    if args.due_date:
        due_date = date_to_epoch_time(args.due_date)
    else:
        due_date = None
    if args.start_date:
        start_date = date_to_epoch_time(args.start_date)
    else: 
        start_date = None
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_file_name_match_type = args.source_file_name_match_type
    custom_fields = args.custom_json
    if args.assignees:
        assignees = get_member_ids_from_names(
                            access_token, 
                            list_id, 
                            literal_eval(args.assignees))
    else:
        assignees=[]
    
    if args.tags:
        tags = literal_eval(args.tags)
    else:
        tags = []

    task_data = create_task(
                    list_id, 
                    access_token, 
                    name, 
                    description, 
                    assignees, 
                    tags, 
                    args.status, 
                    priority,
                    due_date, 
                    args.time_estimate, 
                    start_date, 
                    custom_fields)

    task_id = task_data['id']
    
    if source_file_name_match_type == 'regex_match':
        all_local_files = shipyard.files.find_all_local_file_names(
            source_folder_name)
        matching_file_names = shipyard.files.find_all_file_matches(
            all_local_files, re.compile(source_file_name))
        for index, file_name in enumerate(matching_file_names):
            upload_file_attachment(access_token, 
                                task_id,
                                file_name)
    else:
        source_file_path = shipyard.files.combine_folder_and_file_name(
            source_folder_name, source_file_name)
        upload_file_attachment(access_token, 
                            task_id,
                            source_file_path)

    # save task response to responses artifacts
    task_data_filename = shipyard.files.combine_folder_and_file_name(
        artifact_subfolder_paths['responses'],
        f'create_ticket_{task_id}_response.json')
    shipyard.files.write_json_to_file(task_data, task_data_filename)

    

if __name__ == "__main__":
    main()