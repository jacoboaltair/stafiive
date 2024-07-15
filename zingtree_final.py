import csv
import json
import os.path
from collections import defaultdict
from io import BytesIO, StringIO
from typing import Iterable, Tuple
from pydantic import BaseModel, Field
import itertools


def get_index(setence: str) -> list[int]:
    return [i for i, x in enumerate(setence) if x == ':']


class OutputFile(BaseModel):
    data: dict
    file_name: str

    def to_json(self) -> str:
        return json.dumps(self.data)


def convert(input_data: str) -> dict:
    output = []
    for index in get_index(input_data):
        current_index = index
        while 0 <= current_index:
            if input_data[current_index] == ',':
                break
            current_index -= 1

        if current_index != -1:
            output.append(current_index + 1)

    result = []
    part = slice(0, output[0])
    result.append(input_data[part].split(':'))

    for index in range(len(output) - 1):
        part = slice(output[index], output[index + 1] - 1)

        result.append(input_data[part].split(':'))

    part = slice(output[-1], len(input_data))
    result.append(input_data[part].split(':'))
    return dict(e for e in result if len(e) == 2)


class PointOfContacts(BaseModel):
    name: str = Field(..., alias="Name")
    last_name: str = Field("", alias="Last Name")
    reasons_to_reach: str = Field("", alias="Reasons to Reach out")
    email: str = Field("", alias='Email Address')
    phone: str = Field("", alias='Phone Number')
    availability: str = Field("", alias="Availability to reach out")
    other_notes: str = Field("", alias="Other Notes")
    no_answer: str = Field("", alias="If this person doesn’t answer what should we do?")
    position: str = Field("", alias="Position")


class GeneralInformation(BaseModel):
    working_hours: str = Field(..., alias="Working Hours")
    law_firm: str = Field(..., alias="Law Firm")
    address: str = Field(..., alias="Address")
    direction: str = Field(..., alias="Directions for clients to reach your office:")
    greeting: str = Field(..., alias="Do you agree to use this greeting for all callers?")
    phone_number: str = Field(...,
                              alias="Please write down the phone numbers that you will be forwarding the calls from")
    area_of_practice: list[str] = Field(..., alias="Which areas of Law do you Practice?")
    no_handle_case: list[str] = Field(default_factory=list)
    consult_length: str = Field(..., alias="How long are your consultations?")
    intro: str = ''
    paid_or_not: str = Field(..., alias="Are these paid or free consultations?")
    consultation_extension: str = Field(..., alias="How long are your consultations?")
    price: str = Field(..., alias="What's the price of each consultation?")
    languages: str = Field(..., alias='In which languages are consultations available?')
    consultation_manage: str = Field(..., alias="Do you want us to schedule consultations for you?")
    consultation_way: str = Field(...,
                                  alias="How do you conduct your first consultation: online, by phone, or in person?")
    requirements: str = Field(..., alias="What are the requirements to schedule a consultation for a new client?")
    general: str = ""
    link: str = ""
    principal: str = Field(..., alias="Person Filling the form")


class ZohoLoader:

    def __init__(self, data: bytes):

        # check if a file exists
        self._load_from_file(data)

    def _load_from_file(self, data: bytes):
        file = StringIO(data.decode())
        self._zoho_csv_loaded = list(csv.reader(file))
        self._zoho_form = self._get_columns(self._zoho_csv_loaded)

    def _get_columns(self, csv_data: list[list[str]]) -> dict[str, list[int]]:
        column_iterator = enumerate(csv_data[0])
        columns_map = defaultdict(list)
        columns = csv_data[0]
        while True:

            try:
                index, column = next(column_iterator)
            except StopIteration:
                break

            if 'Please, if you have' in column:
                columns_map[columns[index - 1]].append(index)
                columns_map[columns[index - 1]].append(index + 1)

            else:
                columns_map[column].append(index)
                while index + 1 < len(csv_data[0]) and csv_data[0][index + 1] == '':
                    try:
                        index, _ = next(column_iterator)
                    except StopIteration:
                        break
                columns_map[column].append(index + 1)

        return columns_map

    @property
    def law_firm(self) -> str:
        return self._zoho_csv_loaded[2][1]

    def point_of_contacts(self) -> Iterable[PointOfContacts]:

        columns = [
            'Legal Assistants -  Contact Information',
            'Paralegals -  Contact Information',
            'Law Firm Partners -  Contact Information',
            'Other -  Contact Information'
        ]
        output = []
        for column in columns:
            indexes = self._zoho_form[column]
            for column_index in itertools.batched(indexes, 2):
                for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                    if element:
                        position, *_ = column.strip().split('-')
                        # temp = dict(map(lambda x: x.split(':'), element.split(','))) | {'Position': position.strip()}

                        result = convert(element) | {'Position': position.strip()}

                        output.append(PointOfContacts(**result))

        return output

    def area_of_practice(self) -> GeneralInformation:

        columns = [
            "Working Hours",
            "Law Firm",
            "Address",
            "Directions for clients to reach your office:",
            "Do you agree to use this greeting for all callers?",
            "Please write down the phone numbers that you will be forwarding the calls from",
            "Which areas of Law do you Practice?",
            "Please insert here the url/urls for scheduling. If you have more than one, please explain when should we use each ."

        ]
        output = {}
        for column in columns:
            indexes = self._zoho_form[column]
            for column_index in itertools.batched(indexes, 2):
                for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                    output[column] = element

        output["Which areas of Law do you Practice?"] = output["Which areas of Law do you Practice?"].split('\n')
        output["Which areas of Law do you Practice?"] = [e for e in output["Which areas of Law do you Practice?"] if e]


        output["intro"] = (
        r"<p style='box-sizing: border-box; margin: 0px 0px 20px; color: rgb(68, 50, 94); font-family: Roboto, "
         r"\"Helvetica Neue\", Helvetica, Arial, sans-serif; font-size: 18px; font-style: normal; "
         r"font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; "
         r"orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; "
         r"-webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(245, 245, "
         r"245); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: "
         r"initial;'><strong><span style=\"color: rgb(255, 0, 0); font-size: 24px;\">&nbsp;{law_firm} [Reception &amp; "
         r"Intake] [CDT]<\/span><\/strong><\/p><p id=\"isPasted\" style='box-sizing: border-box; margin: 0px 0px 20px; "
         r"color: rgb(68, 50, 94); font-family: Roboto, \"Helvetica Neue\", Helvetica, Arial, sans-serif; font-size: "
         r"18px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; "
         r"letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; "
         r"word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(245, 245, "
         r"245); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: "
         r"initial;'><span style=\"box-sizing: border-box; font-size: 18px; font-family: Verdana, Geneva, sans-serif; "
         r"color: rgb(0, 0, 0);\"><span id=\"isPasted\" style=\"font-size: 24px; font-family: Verdana, Geneva, "
         r"sans-serif; color: rgb(0, 0, 0);\"><strong>E:&nbsp;<\/strong><\/span><\/span><span style=\"box-sizing: "
         r"border-box; background-color: rgb(204, 238, 255); font-size: 18px; font-family: Verdana, Geneva, "
         r"sans-serif; color: rgb(0, 0, 0);\">Hi! Thank you for calling {law_firm} My name is "
         r"#agent_name#.&nbsp;<\/span><\/p><p style='box-sizing: border-box; margin: 0px 0px 20px; color: rgb(68, 50, "
         r"94); font-family: Roboto, \"Helvetica Neue\", Helvetica, Arial, sans-serif; font-size: 18px; font-style: "
         r"normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: "
         r"normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: "
         r"0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(245, 245, "
         r"245); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: "
         r"initial;'><span style=\"box-sizing: border-box; background-color: rgb(255, 204, 255); font-size: 18px; "
         r"font-family: Verdana, Geneva, sans-serif; color: rgb(0, 0, 0);\">How can I assist you today?<\/span><\/p><p "
         r"style='box-sizing: border-box; margin: 0px 0px 20px; color: rgb(68, 50, 94); font-family: Roboto, "
         r"\"Helvetica Neue\", Helvetica, Arial, sans-serif; font-size: 18px; font-style: normal; "
         r"font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; "
         r"orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; "
         r"-webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(245, 245, "
         r"245); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: "
         r"initial;'><span style=\"box-sizing: border-box; font-size: 14px; color: rgb(124, 112, 107);\"><span "
         r"style=\"box-sizing: border-box; font-family: Verdana, Geneva, sans-serif;\"><em style=\"box-sizing: "
         r"border-box;\"><strong>Identify the subject of the call.<\/strong><\/em><\/span><\/span><\/p><p "
         r"id=\"isPasted\"><span style=\"font-size: 24px; font-family: Verdana, Geneva, sans-serif; color: rgb(0, 0, "
         r"0);\"><strong>S:<\/strong>&nbsp;<\/span><span style=\"font-size: 18px; font-family: Verdana, Geneva, "
         r"sans-serif; color: rgb(0, 0, 0); background-color: rgb(187, 222, 251);\">&iexcl;Hola! Gracias por llamar a "
         r"{law_firm} Mi nombre es&nbsp;#agent_name#.<\/span><\/p><p><span style=\"background-color: rgb(248, 187, "
         r"208); font-size: 18px; font-family: Verdana, Geneva, sans-serif; color: rgb(0, 0, 0);\">&iquest;C&oacute;mo "
         r"puedo ayudarle hoy?<\/span><\/p>").format(law_firm=output["Law Firm"])

        key = "Do you have a booking platform like Calendly so we can schedule consultations for you?"

        if output.get(key) == "Yes":
            k = "Please insert here the url/urls for scheduling. If you have more than one, please explain when should we use each ."
            temp = output[k]
            output["link"] = temp

        return GeneralInformation(**output)

    def consultations(self) -> GeneralInformation:
        columns = [
            "What's the price of each consultation?",
            "Working Hours",
            "Law Firm",
            "Address",
            "Directions for clients to reach your office:",
            "Do you agree to use this greeting for all callers?",
            "Please write down the phone numbers that you will be forwarding the calls from",
            "Which areas of Law do you Practice?",
            "Do you have a booking platform like Calendly so we can schedule consultations for you?",
            "Please insert here the url/urls for scheduling. If you have more than one, please explain when should we use each .",
            'Multi Line',
            'How long are your consultations?',
            'Are these paid or free consultations?',
            'If it depends, please explain here',
            'Do you want us to schedule consultations for you?',
            'In which languages are consultations available?',
            'How do you conduct your first consultation: online, by phone, or in person?',
            'What are the requirements to schedule a consultation for a new client?',
            'In which languages are consultations available?',
            'Person Filling the form',
            'What are the requirements to schedule a consultation for a new client?',
        ]

        output = {}
        for column in columns:
            indexes = self._zoho_form[column]
            for column_index in itertools.batched(indexes, 2):

                for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                    if column == 'If it depends, please explain here':
                        output['Are these paid or free consultations?'] = element
                    else:
                        output[column] = element

        output["Which areas of Law do you Practice?"] = output["Which areas of Law do you Practice?"].split('\n')

        output["intro"] = """E: Hi! Thank you for calling {law_firm}. My name is #agent_name#. 

        How can I assist you today?

        Identify the subject of the call..

        S: ¡Hola! Gracias por llamar a {law_firm}. Mi nombre es #agent_name#.

        ¿Cómo puedo ayudarle hoy?
                """.format(law_firm=output["Law Firm"]).replace("\n", "")

        output['no_handle_case'] = [e for e in output['Multi Line'].split('\n') if e]

        key = "Do you have a booking platform like Calendly so we can schedule consultations for you?"

        if output.get(key) and "Yes" in output.get(key):
            k = "Please insert here the url/urls for scheduling. If you have more than one, please explain when should we use each ."
            temp = output[k]
            output["link"] = temp

        return output, GeneralInformation(**output)

    def decisions(self):
        columns = [
            'What sales pitch would you like us to apply?',
            'How does the law firm currently identify and manage their existing clients within their system or database?',
            'How do you want us to manage an existing client who is calling?  (Existing client: a person who has an ongoing matter with the Law Firm)',
            'Please describe the situations in which we should transfer a call from an existing client to a team member.',
            'What information would you like us to gather for existing clients with an ongoing case with the firm?',
            'The client is calling for a follow-up call, how does you Law firm manage follow ups after a consultation?',
            'Please write down any specific directions you might have about these type of calls',
            'What is the time frame and fee for follow-up consultations?',
            'If the client is calling because they have a deadline (next court hearing, or removal, deportation, etc), how do you proceed?',
            'If the client has questions/concerns about the legal process, or\xa0they received new information or documents, how do you proceed?',
            'If the Client requests help filling out legal forms, how do you proceed?',
            'If the client calls to Cancel a Consultation, how do you proceed?',
            'If the client is calling because there have been changes in their contact information, how do you proceed?',
            'If a client calls stating, for example, he is in the courtroom and is unable to find the attorney, how do you proceed?',
            'If a client wants to file a complaint, how do you proceed?',
            'When a client is calling because their process was denied, how do you proceed? For example: Someone is calling upset because their process was denied and they want a reimbursement.',
            'How would you like us to manage incoming calls from the Court?',
            'Please, if you have any other directions on how you want us to handle this type of calls, write them down.',
            'Please fill all information:',
            'How do you handle returning clients with a new matter with the firm?',
            'Do you have a special price or discount for returning clients with a new matter?',
            'How do you manage an Existing Vendor?'
        ]

        output = {}
        for column in columns:

            if column.startswith('If the Client') or column.startswith('If a client') or column.startswith(
                    'If a Client') or column.startswith('If the client'):
                indexes = self._zoho_form[column]
                temp = []
                for column_index in itertools.batched(indexes, 2):
                    for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                        temp.append(element)

                output[column] = ". ".join(e for e in temp if e)

            else:
                indexes = self._zoho_form[column]
                for column_index in itertools.batched(indexes, 2):
                    for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                        output[column] = element

        return output

    def sales_pitch(self) -> list[str]:

        columns = [
            'Would you like for us to apply a sales speech to clients when they become overly focused on '
            'pricing?',
            '1. I understand money is important. Assuming that a “reputable” company can do it for less, which.',
            '2. I understand price is important. But equally as important is to know that your case is being handled '
            'by someone who cares about you and your situation. Every year people are fooled by people who take '
            'payment from clients just',
            '3. I understand money is important. These types of cases can be relatively simple, or become very '
            'complex. Anyone who gives you a price without understanding the pa',
            'If you have any other sales pitch or modifications you would like us to apply to the ones above, '
            'please write them down here',
            'What sales pitch would you like us to apply?'
        ]
        output = []
        for i, column in enumerate(columns):
            indexes = self._zoho_form[column]
            for column_index in itertools.batched(indexes, 2):
                for element in self._zoho_csv_loaded[2][slice(*column_index)]:
                    if i == 0 and element.lower() in 'no':
                        return output

                    if i not in [0, 4, 5]:
                        output.append(
                            column
                        )
                    elif i == 4:

                        output.append(
                            element
                        )

        return output


from jinja2 import Template


def render_caller_information(zoho_loader: ZohoLoader):
    with open("templates/caller_information.html", "r") as fd:
        template = Template(fd.read())

    return template.render(sales_pitches=zoho_loader.sales_pitch())


def render_point_of_contacts(zoho_loader: ZohoLoader):
    result = zoho_loader.point_of_contacts()

    with open("templates/_point_contacts.html", "r") as fd:
        template = Template(fd.read())

    return template.render(law_firm_workers=list(itertools.batched(result, 2)))


def master_form(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/0. Master Form - Master Tree_1714081380947.json', "r") as fp:
        json_template = json.load(fp)

    point_of_contacts = render_point_of_contacts(zoho_loader)
    general_information_data = zoho_loader.consultations()

    with open("templates/general_information.html", "r") as fd:
        general_information_template = Template(fd.read())

    general_information = general_information_template.render(
        general_information=general_information_data[1]
    )

    with open('templates/sales_pitch.html') as file_:
        template = Template(file_.read())
    result = template.render(sales_pitch=zoho_loader.sales_pitch())

    json_template["nodes"]["1006"]["content"] = """
<p>Caller name: #ma_caller_name#</p>
<p>Caller Phone number: #ma_dialpad_num#</p>
<p>Caller Email: #ma_caller_email#</p>
<p>Reason of the call: #ma_call_subject#</p>
{}
    """.format(result)
    json_template["nodes"]["1001"]["content"] = """{}""".format(point_of_contacts)
    json_template["nodes"]["1000"]["content"] = """{}""".format(general_information)


    with open("templates/welcome.html", "r") as fd:
        general_information_template = Template(fd.read())

    json_template["nodes"]["2"]["content"] = general_information_template.render(
        law_firm=general_information_data[0]['Law Firm']
    )

    return OutputFile(
        file_name=f"0. {general_information_data[0]['Law Firm']} - master.json",
        data=json_template
    )


def existing_client(zoho_loader: ZohoLoader) -> None:
    with open('zingtree_files/1. Master - Existing Clients Tree_1714081243884.json', "r") as fp:
        json_template = json.load(fp)

    general_information_data = zoho_loader.consultations()
    decisions = zoho_loader.decisions()

    json_template["nodes"]["122"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client is calling because they have a deadline (next court hearing, or removal, deportation, etc), how do you proceed?'
        ]
    )
    json_template["nodes"]["124"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client has questions/concerns about the legal process, or\xa0they received new information or documents, how do you proceed?']
    )

    json_template["nodes"]["124"]["content"] += """<p>{}</p>""".format(
        decisions[
            'How do you want us to manage an existing client who is calling?  (Existing client: a person who has an ongoing matter with the Law Firm)']
    )

    json_template["nodes"]["123"]["content"] += """<p>{}</p>""".format(
        decisions[
            'The client is calling for a follow-up call, how does you Law firm manage follow ups after a consultation?'
        ]
    )

    json_template["nodes"]["125"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client is calling because there have been changes in their contact information, how do you proceed?'
        ]
    )

    json_template["nodes"]["121"]["content"] += """<p>{}</p>""".format(
        decisions[
            'How would you like us to manage incoming calls from the Court?'
        ]
    )

    json_template["nodes"]["126"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If a client wants to file a complaint, how do you proceed?'
        ]
    )

    json_template["nodes"]["118"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the Client requests help filling out legal forms, how do you proceed?'

        ]
    )

    json_template["nodes"]["114"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client calls to Cancel a Consultation, how do you proceed?'

        ]
    )

    json_template["nodes"]["116"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client calls to Cancel a Consultation, how do you proceed?'
        ]
    )

    return OutputFile(
        file_name=f"1. {general_information_data[0]['Law Firm']} - Existing Clients.json",
        data=json_template
    )


def other_scenarios(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/2. Master - Other Scenarios Tree_1714081259389.json', "r") as fp:
        json_template = json.load(fp)

    decisions = zoho_loader.decisions()

    general_information_data = zoho_loader.consultations()

    json_template["nodes"]["105"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client calls to Cancel a Consultation, how do you proceed?'

        ]
    )

    json_template["nodes"]["134"]["content"] += """<p>{}</p>""".format(
        decisions[
            'If the client calls to Cancel a Consultation, how do you proceed?'

        ]
    )

    return OutputFile(
        file_name=f"2. {general_information_data[0]['Law Firm']} - Other Scenarios.json",
        data=json_template
    )


def attorney_calling(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/3. Master - Attorney Calling_1714081253074.json', "r") as fp:
        json_template = json.load(fp)

    general_information_data = zoho_loader.consultations()

    return OutputFile(
        file_name=f"3. {general_information_data[0]['Law Firm']} - Attorney Calling.json",
        data=json_template
    )


def past_matter(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/4. Returning Client - Calling for a Past Matter Tree_1714081267307.json', "r") as fp:
        json_template = json.load(fp)

    general_information_data = zoho_loader.consultations()

    return OutputFile(
        file_name=f"4. {general_information_data[0]['Law Firm']} - Past Matter.json",
        data=json_template
    )


def scheduling_tree(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/5. Master - Scheduling Tree_1714081400981.json', "r") as fp:
        json_template = json.load(fp)

    general_information_data = zoho_loader.consultations()

    return OutputFile(
        file_name=f"5. {general_information_data[0]['Law Firm']} - Scheduling Tree.json",
        data=json_template
    )


def closing_script(zoho_loader: ZohoLoader) -> OutputFile:
    with open('zingtree_files/5. Master - Scheduling Tree_1714081400981.json', "r") as fp:
        json_template = json.load(fp)

    general_information_data = zoho_loader.consultations()

    return OutputFile(
        file_name=f"6. {general_information_data[0]['Law Firm']} - Closing Script.json",
        data=json_template
    )


# Check if file exists

# more fine-grained control over ZIP files

def run_script(data: bytes) -> tuple[BytesIO, str]:
    from zipfile import ZipFile

    zoho_loaded = ZohoLoader(data)

    files = [
        master_form(zoho_loaded),
        existing_client(zoho_loaded),
        other_scenarios(zoho_loaded),
        attorney_calling(zoho_loaded),
        past_matter(zoho_loaded),
        scheduling_tree(zoho_loaded),
        closing_script(zoho_loaded)
    ]

    new_zip = BytesIO()
    with ZipFile(new_zip, "w") as newzip:
        for file in files:
            newzip.writestr(file.file_name, file.to_json())

    return new_zip, f"{zoho_loaded.law_firm}.zip"
