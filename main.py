import math

import json
from typing import Optional

from rapidfuzz import process

from streamlit.runtime.uploaded_file_manager import UploadedFile


def search_button_node(nodes: dict[str, dict], node_id: str) -> dict:
    for node_key, node in nodes.items():
        for _, button in node["buttons"].items():
            if button["button_link"] == node_id:
                yield node


def search_node(nodes: dict[str, dict], node_id: str) -> Optional[dict]:
    return nodes.get(node_id)


def next_node_to_connect__(next_node: str, tree: dict[str, dict], nodes_settings: dict) -> str:
    if (node_found := nodes_settings.get(next_node)) and node_found['include'] == '1':
        return next_node

    if next_node in tree['nodes']:
        temp_node = tree['nodes'][next_node]["buttons"]["0"]["button_link"]
        del tree['nodes'][next_node]

        next_node_to_connect__(temp_node, tree, nodes_settings)


def delete_node(nodes: dict[str, dict], node_id: str):
    if node_id not in nodes['nodes']:
        return

    del nodes['nodes'][node_id]


def next_node_to_connect(next_node: str, tree: dict[str, dict], nodes_settings: dict) -> str:
    if (node_found := nodes_settings.get(next_node)) and node_found['include']:
        return next_node
    elif next_node not in nodes_settings:
        return next_node

    if next_node in tree['nodes']:
        temp_node = tree['nodes'][next_node]["buttons"]["0"]["button_link"]
        return next_node_to_connect(temp_node, tree, nodes_settings)


# get the node that should no be included
# find the next node of that node that is included and delete all the childs that are not included
# find out the node that have that node


# test_2()
def match_name(
    key: str
) -> str:
    positions = {
        "1. May I kindly ask in which city and state is the applicant's currently residing?": '39',
     "2. What is the applicant's date of birth?": '40',
        '3. Which country was the applicant born in?': '41',
     '4. When did the applicant first enter the United States?': '42',
     "5. When was the applicant's most recent entry into the United States?": '70',
     '6. How did the applicant last enter the United States?': '44',
     '7. Has the applicant ever submitted applications for any immigration benefits?': '47',
     "8. Are or were the applicant's parents or grandparents citizens of the United States?": '48',
     '9. Is the applicant presently married?': '49', '10. Has the applicant previously been married?': '50',
     '13. Does the applicant have any children in common with a US citizen or Legal Permanent Resident?': '54',
     '14. Does the applicant have a family member that is a United States citizen (Spouse, parents, siblings, partners, children) who is willing to petition?': '55',
     '15. Has the applicant previously worked in the United States?': '56',
     '16. Can I kindly ask if the applicant has ever been involved in any activities that might have been considered a crime?': '57',
     '17. Does the applicant have any concerns or reasons to fear returning to their home country?': '58',
     '18. Has the applicant ever experienced domestic abuse by a partner, spouse, parent, or child?': '60',
     '20. Has the applicant ever been the victim of a crime or physically hurt while in the United States?': '62',
     '22. Was the applicant recruited by anyone in their home country to work in the United States?"': '64',
     '23. Did the applicant experience coercion or deception that led the applicant to work in the United States?': '65',
     '24. Was the applicant obligated to work without receiving pay or were you paid less than what was legally expected or agreed upon?': '66',
     '25. Has the applicant ever been abandoned, abused, or neglected by a parent?': '67',
     "11. In which country did the applicant's marriage take place?": '51',
     "12. What is the applicant's current relationship status with their partner?": '52',
     "19. Does the applicant's partner/spouse/parent or child hold US citizenship status or possess Legal Permanent Resident status?": '61',
     '21. Did the applicant report the incident to the police or cooperate with any criminal investigation or prosecution related to it?': '63',
     '26. Is the applicant currently under the jurisdiction of a juvenile court, such as in a dependency, '
     'delinquency, or probate guardianship case?': '68'}
    key_found, *_ = process.extractOne(key, positions.keys())
    return positions.get(key_found)

def load_settings(file_uploaded: UploadedFile):

    settings = {}

    import pandas as pd

    data = pd.read_csv(file_uploaded)
    for index, key in enumerate(data):
        temp = data[key]
        if isinstance(temp[0], str) or math.isnan(temp[0]):
            continue

        value = temp[0].tolist()

        if isinstance(value, bool):
            settings[match_name(str(key))] = {'include': value, 'node': match_name(str(key))}


    return settings



def create_tree(zoho_report: UploadedFile, zingtree_json: Optional[UploadedFile] = None):

    if zingtree_json is None:
        with open('example.json', 'r') as fp:
            zingtree = json.load(fp)
    else:
        zingtree = json.loads(zingtree_json.read())

    #with open(file_name.name, 'r') as fp:
    #    settings = {row['node']: row for row in csv.DictReader(fp)}
    settings = load_settings(zoho_report)
    node_deletes = []
    for node_ide, setting in settings.items():
        if not setting['include']:
            result = next_node_to_connect(setting['node'], zingtree, settings)
            node_deletes.append(node_ide)
            for node_button in search_button_node(zingtree["nodes"], setting['node']):
                # delete_node(zingtree, setting['node'])
                if node_button:
                    project = node_button['project_node_id']
                    for key in zingtree["nodes"][project]["buttons"]:
                        button = zingtree["nodes"][project]["buttons"][key]
                        button['button_link'] = result

    for node in node_deletes:
        delete_node(zingtree, node)

    node_deletes = set()
    for node in zingtree["nodes"]:
        while not list(search_button_node(zingtree["nodes"], node)):
            if node in node_deletes or node == "5":
                break

            node_deletes.add(node)


    for node in node_deletes:
        delete_node(zingtree, node)

    return zingtree


