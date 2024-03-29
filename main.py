import dropbox
import csv
import requests
import json
from dropbox.files import WriteMode
from dotenv import load_dotenv
import os
from dropbox.exceptions import ApiError, HttpError
import sentry_sdk


sentry_sdk.init(
    "https://9cece7c10b31476fb0ea7fe3e7287142@o495639.ingest.sentry.io/5568685",
    traces_sample_rate=1.0
)

load_dotenv()
dropbox_access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(dropbox_access_token)


def update_menu_items(request):
    list_folder_result = dbx.files_list_folder(path="/restaurants")
    for entry in list_folder_result.entries:
        restaurant_filename = entry.name
        metadata, res = dbx.files_download(path=f"/restaurants/{restaurant_filename}")
        content_decoded = res.content.decode('ascii')
        parsed_csv = csv.reader(content_decoded.splitlines(), delimiter=',')
        menu_items = list(parsed_csv)
        restaurant_name = restaurant_filename.split('.')[0]

        update_requests(restaurant_name, menu_items)

    return "Operation successful"


def update_requests(restaurant_name, menu_items):
    # removing column name and writing it as first row of new content
    new_content = ','.join(menu_items.pop(0)) + "\n"

    for menu_item_row in menu_items:
        new_row_content, row_input_valid = preprocess_input_row(menu_item_row)
        new_content += new_row_content

        if row_input_valid:
            menu_item = {'name': menu_item_row[0], 'description': menu_item_row[1],
                         'price': menu_item_row[2], 'restaurantName': restaurant_name}

            response = send_create_menu_item_request(menu_item)

            if response.status_code == 201:
                new_content += ",successful"
            elif response.status_code == 404:
                new_content += ",Restaurant name doesn't exist\n"
                new_content += rewrite_remaining_text(menu_items[1:])
                break
            else:
                new_content += ", Unexpected error"

        new_content += "\n"

    file_path = f"/tmp/{restaurant_name}.csv"

    with open(file_path, "w") as f:
        f.write(new_content)
    with open(file_path, 'rb') as f:
        try:
            dbx.files_upload(f.read(), f"/restaurants/misko.csv", mode=WriteMode.overwrite)
        except HttpError as ex:
            if ex.status_code == 413:
                print("File is too large")
        except ApiError:
            print("Error uploading file.")
    os.remove(file_path)


def preprocess_input_row(menu_item_row):
    new_row_content = ""
    if len(menu_item_row) < 3:
        new_row_content += ", , , invalid row length"
        return new_row_content, False

    menu_item_name = menu_item_row[0]
    menu_item_description = menu_item_row[1]
    menu_item_price = menu_item_row[2]

    new_row_content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price

    if menu_item_name == "":
        new_row_content += ", You must specify menu item name"
        return new_row_content, False

    if menu_item_price == "":
        new_row_content += ", You must specify menu item price"
        return new_row_content, False

    if not menu_item_price.isdecimal():
        new_row_content += ", Price must be a decimal number"
        return new_row_content, False

    return new_row_content, True


def send_create_menu_item_request(menu_item):
    create_menu_item_url = "https://voltaire-api-gateway-cvy8ozaz.ew.gateway.dev/menu-items"
    headers = {'Content-type': 'application/json'}
    return requests.post(url=create_menu_item_url, data=json.dumps(menu_item), headers=headers)


def rewrite_remaining_text(menu_items_remaining):
    content = ""

    for menu_item_row in menu_items_remaining:
        menu_item_name = menu_item_row[0]
        menu_item_description = menu_item_row[1]
        menu_item_price = menu_item_row[2]
        content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price + "\n"

    return content
