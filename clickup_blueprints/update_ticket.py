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
    parser.add_argument('--task-id', dest='task_id', required=True)
    parser.add_argument('--access-token', dest='access_token', required=True)
    parser.add_argument('--name', dest='name', required=True)
    parser.add_argument('--description', dest='description', required=True)
    parser.add_argument('--priority', dest='priority', required=False)
    parser.add_argument('--due-date', dest='due_date', required=False)
    parser.add_argument('--custom-json', dest='custom_json', required=False)
    args = parser.parse_args()
    return args


def update_task(task_id, token, name, description, status, priority,
                due_date=None, custom_fields=None):
    """ Triggers the Update Task API and changes the data
    see: https://jsapi.apiary.io/apis/clickup20/reference/0/tasks/update-task.html
    """
    
    update_task_api = f"https://api.clickup.com/api/v2/task/{task_id}/"
    headers = {
      'Authorization': token,
      'Content-Type': 'application/json'
    }
    
    payload = {
      "name": name,
      "description": description,
      "priority": priority,
      "due_date": due_date,
    }
    if custom_fields:
        payload.update(custom_fields)

    response = requests.put(update_task_api, 
                             headers=headers, 
                             json=payload
                             )
    
    if response.status_code == 200: # created successfuly
        print(f"Task {task_id} updated successfully")
        return response.json()
        
    elif response.status_code == 401: # Permissions Error
        print("Clickup permissions error: check if token is correct",
              f"and you have access to the modify task: {task_id}")
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
    task_id = args.task_id
    name = args.name
    description = args.description
    priority = args.priority
    due_date = args.due_date
    custom_fields = args.custom_json
    task_data = update_task(task_id, access_token, name, description,
                priority, due_date, custom_fields)
    
    # save task response to responses artifacts
    task_data_filename = shipyard.files.combine_folder_and_file_name(
        artifact_subfolder_paths['responses'],
        f'update_ticket_{task_id}_response.json')
    shipyard.files.write_json_to_file(task_data, task_data_filename)

    

if __name__ == "__main__":
    main()