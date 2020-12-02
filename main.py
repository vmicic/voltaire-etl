import dropbox
import csv
import requests
import json
from dropbox.files import WriteMode

dropbox_access_token = "BQ_OJp7O7QAAAAAAAAAAAQs2ID_x5zT6ED0-aQp1QC9lpZwZSbc7C7UVRy03IBW_"
dbx = dropbox.Dropbox(dropbox_access_token)


def update_menu_items(request):
    list_folder_result = dbx.files_list_folder(path="/restaurants")
    for entry in list_folder_result.entries:
        restaurant_filename = entry.name
        metadata, res = dbx.files_download(path="/restaurants/" + restaurant_filename)
        content_decoded = res.content.decode('ascii')
        parsed_csv = csv.reader(content_decoded.splitlines(), delimiter=',')
        parsed_csv_list = list(parsed_csv)

        update_requests(restaurant_filename, parsed_csv_list)

    return "Operation successful"


def update_requests(restaurant_filename, menu_items_csv_list):
    # removing column name and writing it as first row of new content
    new_content = ','.join(menu_items_csv_list.pop(0)) + "\n"
    restaurant_name = restaurant_filename.split('.')[0]

    for menu_item_row in menu_items_csv_list:
        menu_item_name = menu_item_row[0]
        menu_item_description = menu_item_row[1]
        menu_item_price = menu_item_row[2]
        new_content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price

        menu_item = {'name': menu_item_row[0], 'description': menu_item_row[1],
                     'price': menu_item_row[2], 'restaurantName': restaurant_name}

        create_menu_item_url = "https://voltaire-api-gateway-cvy8ozaz.ew.gateway.dev/menu-items";
        headers = {'Content-type': 'application/json'}
        response = requests.post(url=create_menu_item_url, data=json.dumps(menu_item), headers=headers)

        if response.status_code == 201:
            new_content += ",successful"

        else:
            new_content += ",unsuccessful"

        new_content += "\n"

    with open("/tmp/" + restaurant_name + ".csv", "w") as f:
        f.write(new_content)
        f.close()
    with open("/tmp/" + restaurant_name + ".csv", 'rb') as f:
        dbx.files_upload(f.read(), "/restaurants/" + restaurant_name + ".csv", mode=WriteMode.overwrite)
