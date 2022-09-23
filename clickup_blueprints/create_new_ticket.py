import argparse
import sys
import requests
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
    parser.add_argument('--status', dest='status', required=True)
    parser.add_argument('--priority', dest='priority', required=True)
    parser.add_argument('--due-date', dest='due_date', required=False)
    parser.add_argument('--custom-json', dest='custom_json', required=False)
    args = parser.parse_args()
    return args


def create_task(list_id, token, name, description, status, priority,
                due_date=None, custom_fields=None):
    """ Triggers the Create Task API and adds a new task onto CLickUp
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
      "status": status,
      "priority": priority,
      "due_date": due_date,
      "notify_all": True,
      "check_required_custom_fields": True,
    }
    if custom_fields:
        payload['custom_fields'] = custom_fields

    response = requests.post(create_task_api, 
                             headers=headers, 
                             data=payload
                             )
    
    if response.status_code == 200: # created successfuly
        task_id =  response.json()['id']
        print(f"Task created successfully with task name: {task_id}")
        return response.json()
        
    elif response.status_code == 401: # Permissions Error
        print("You do not have the required permissions to create an task in ",
              "this project")
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
    

def main():
    args = get_args()
    access_token = args.access_token
    list_id = args.list_id
    name = args.name
    description = args.description
    priority = args.priority
    status = args.status
    due_date = args.due_date
    custom_fields = args.custom_json
    task_data = create_task(list_id, access_token, name, description, status,
                priority, due_date, custom_fields)
    task_id = task_data['id']
    
    # save task response to responses artifacts
    task_data_filename = shipyard.files.combine_folder_and_file_name(
        artifact_subfolder_paths['responses'],
        f'create_ticket_{task_id}_response.json')
    shipyard.files.write_json_to_file(task_data, task_data_filename)

    

if __name__ == "__main__":
    main()