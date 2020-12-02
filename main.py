import dropbox
import csv
import requests
import json


def update_menu_items(request):
    dropbox_access_token = "BQ_OJp7O7QAAAAAAAAAAAQs2ID_x5zT6ED0-aQp1QC9lpZwZSbc7C7UVRy03IBW_"
    dbx = dropbox.Dropbox(dropbox_access_token)
    list_folder_result = dbx.files_list_folder(path="/restaurants")
    for entry in list_folder_result.entries:
        restaurant_filename = entry.name
        metadata, res = dbx.files_download(path="/restaurants/" + restaurant_filename)
        content_decoded = res.content.decode('ascii')
        parsed_csv = csv.reader(content_decoded.splitlines(), delimiter=',')
        parsed_csv_list = list(parsed_csv)

        # remove column names
        parsed_csv_list.pop(0)

        for menu_item_row in parsed_csv_list:
            print(menu_item_row)
            restaurant_name = restaurant_filename.split('.')[0]
            menu_item = {'name': menu_item_row[0], 'description': menu_item_row[1],
                         'price': menu_item_row[2], 'restaurantName': restaurant_name}

            create_menu_item_url = "https://voltaire-api-gateway-cvy8ozaz.ew.gateway.dev/menu-items";
            headers = {'Content-type': 'application/json'}
            response = requests.post(url=create_menu_item_url, data=json.dumps(menu_item), headers=headers)

            if response.status_code == 201:
                with open("/tmp/" + restaurant_name + " - update successful", "w") as f:
                    f.close()
                with open("/tmp/" + restaurant_name + " - update successful", 'rb') as f:
                    dbx.files_upload(f.read(), "/restaurants/" + restaurant_name + " - update successful.txt")
            else:
                with open("/tmp/" + restaurant_name + " - update unsuccessful", "w") as f:
                    f.close()
                with open("/tmp/test.txt", 'rb') as f:
                    dbx.files_upload(f.read(), "/restaurants/" + restaurant_name + " - update unsuccessful.txt")

    return "Operation successful"
