import dropbox
import csv
import requests
import json
from dropbox.files import WriteMode
from decimal import *

dropbox_access_token = "BQ_OJp7O7QAAAAAAAAAAAQs2ID_x5zT6ED0-aQp1QC9lpZwZSbc7C7UVRy03IBW_"
dbx = dropbox.Dropbox(dropbox_access_token)


def update_menu_items(request):
    list_folder_result = dbx.files_list_folder(path="/restaurants")
    for entry in list_folder_result.entries:
        restaurant_filename = entry.name
        metadata, res = dbx.files_download(path="/restaurants/" + restaurant_filename)
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

        if len(menu_item_row) < 3:
            continue
        menu_item_name = menu_item_row[0]
        menu_item_description = menu_item_row[1]
        menu_item_price = menu_item_row[2]

        new_content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price

        if menu_item_name == "":
            new_content += ", You must specify menu item name \n"
            continue

        if menu_item_price == "":
            new_content += ", You must specify menu item price \n"
            continue

        if not is_decimal(menu_item_price):
            new_content += ", Price must be a decimal number \n"
            continue

        menu_item = {'name': menu_item_row[0], 'description': menu_item_row[1],
                     'price': menu_item_row[2], 'restaurantName': restaurant_name}

        create_menu_item_url = "https://voltaire-api-gateway-cvy8ozaz.ew.gateway.dev/menu-items"
        headers = {'Content-type': 'application/json'}
        response = requests.post(url=create_menu_item_url, data=json.dumps(menu_item), headers=headers)

        if response.status_code == 201:
            new_content += ",successful"
        elif response.status_code == 404:
            new_content += ",Restaurant name doesn't exist\n"
            new_content += rewrite_remaining_text(menu_items[1:])
            break
        else:
            new_content += ", Unexpected error"

        new_content += "\n"

    with open("/tmp/" + restaurant_name + ".csv", "w") as f:
        f.write(new_content)
        f.close()
    with open("/tmp/" + restaurant_name + ".csv", 'rb') as f:
        dbx.files_upload(f.read(), "/restaurants/" + restaurant_name + ".csv", mode=WriteMode.overwrite)


# def preprocess_row(menu_item_row):
#     new_row_content = ""
#     if len(menu_item_row) < 3:
#         return
#
#     menu_item_name = menu_item_row[0]
#     menu_item_description = menu_item_row[1]
#     menu_item_price = menu_item_row[2]
#
#     new_row_content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price
#
#     if menu_item_name == "":
#         new_row_content += ", You must specify menu item name \n"
#         return new_row_content
#
#     if menu_item_price == "":
#         new_row_content += ", You must specify menu item price \n"
#         return new_row_content
#
#     if not is_decimal(menu_item_price):
#         new_row_content += ", Price must be a decimal number \n"
#         return new_row_content


def is_decimal(s):
    try:
        Decimal(s)
        return True
    except InvalidOperation:
        return False


def rewrite_remaining_text(menu_items_remaining):
    content = ""

    for menu_item_row in menu_items_remaining:
        menu_item_name = menu_item_row[0]
        menu_item_description = menu_item_row[1]
        menu_item_price = menu_item_row[2]
        content += menu_item_name + ",\"" + menu_item_description + "\"," + menu_item_price + "\n"

    return content

update_menu_items(None)

