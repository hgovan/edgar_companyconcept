from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Set
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests
import time
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
USER_AGENT = os.getenv('USERAGENT')


@dataclass
class XMLContextObject:
    id: str
    entity_identifier: str
    segments: List[str]
    period_start_date: Optional[str] = None
    period_end_date: Optional[str] = None
    period_instant: Optional[str] = None


@dataclass
class XMLDataObject:
    tag: str
    context_ref: str
    elem_id: str
    value: str
    unit_ref: str
    decimals: int
    context: Optional[XMLContextObject] = None

    def __str__(self):
        context_ids = ', '.join(str(context.id) for context in self.context)
        context_str = f"Context(id='{context_ids}')" if self.context else "None"
        return (f"XMLDataObject(tag='{self.tag}', context_ref='{self.context_ref}', "
                f"id='{self.elem_id}', value='{self.value}', unit_ref='{self.unit_ref}', "
                f"decimals={self.decimals}, context={context_str})\n")


@dataclass
class Filing:
    cik: str
    ticker: str
    accessionNumber: str
    filingDate: datetime
    reportDate: datetime
    form: str
    primaryDocument: str
    primaryDocDescription: str
    summary: str
    xml_data: Optional[XMLDataObject] = None

    def get_unique_tags(self) -> Set[str]:
        """
        Returns a set of unique tags from the xml_data array.

        Returns:
            Set[str]: A set of unique tag strings.
        """
        if not self.xml_data:
            return set()

        return {xml_object.tag for xml_object in self.xml_data}


@dataclass
class StatementObject:
    cik: str
    gaap_item: str
    end_date: datetime
    accn: str
    form: str
    fy: str
    fp: str
    value: int

    def __str__(self):
        return (f"fp: {self.fp}\n"
                f"value: {self.value}\n"
                f"end_date: {self.end_date}\n")

# =======================================================================
# ===========================General Utilities===========================
# =======================================================================


def get_request(url):
    headers = {
        'User-Agent': USER_AGENT
    }
    time.sleep(.3)
    print(f"Connecting to: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(response, "\n")
        return response
    except:
        print(f"Failed to Connect")


def ticker_to_cik(ticker):
    '''
    Retrieves the CIK for a given ticker symbol.
    '''
    response = get_request('https://www.sec.gov/files/company_tickers.json')
    data = json.loads(response.text)
    ciks = {item['ticker']: str(item['cik_str']) for item in data.values()}
    cik = ciks.get(ticker.upper())
    if cik:
        cik = cik.zfill(10)
    return cik


def format_value_as_readable(value):
    if value >= 1_000_000_000:
        return "${:,.2f}B".format(value / 1_000_000_000)
    elif value >= 1_000_000:
        return "${:,.2f}M".format(value / 1_000_000)
    elif value >= 1_000:
        return "${:,.2f}K".format(value / 1_000)
    else:
        return "${:,.2f}".format(value)


# =======================================================================
# ===========================Filings Utilities===========================
# =======================================================================


def unique_forms(filings):
    unique_forms = set(filing.form for filing in filings)
    unique_forms_list = list(unique_forms)
    # unique forms
    return unique_forms_list


def filter_by_form(filings, filter: list):
    # Get the forms needed
    # Filter the list of filings to only include filings of the specified types
    filtered_filings = [
        filing for filing in filings if filing.form in filter]
    return filtered_filings


def get_filing(ticker, cik):

    # Fetch the filing for the company
    response = get_request(
        f'https://data.sec.gov/submissions/CIK{cik}.json')

    filings_data = response.json()
    bio = {'name': filings_data['name'],
           'sic': filings_data['sic'],
           'sicDescription': filings_data['sicDescription'],
           'EIN': filings_data['ein'],
           'fiscalYearEnd': f"{filings_data['fiscalYearEnd'][:2]}/{filings_data['fiscalYearEnd'][2:]}",
           'Exchanges': list(set(filings_data['exchanges']))}

    accessionNumber_list = filings_data["filings"]["recent"]["accessionNumber"]
    filingDate_list = filings_data["filings"]["recent"]["filingDate"]
    reportDate_list = filings_data["filings"]["recent"]["reportDate"]
    form_list = filings_data["filings"]["recent"]["form"]
    primaryDocument_list = filings_data["filings"]["recent"]["primaryDocument"]
    primaryDocDescription_list = filings_data["filings"]["recent"]["primaryDocDescription"]

    # Iterate over the lists and create a filing object for each item
    filings = [Filing(cik, ticker, accessionNumber, filingDate, reportDate, form, primaryDocument, primaryDocDescription, 'No summary')
               for accessionNumber, filingDate, reportDate, form, primaryDocument, primaryDocDescription in
               zip(accessionNumber_list, filingDate_list, reportDate_list, form_list, primaryDocument_list, primaryDocDescription_list)]
    return bio, filings


def get_filing_text(filing_obj):
    primary_num = filing_obj.accessionNumber.replace('-', '')
    url = f'https://www.sec.gov/Archives/edgar/data/{filing_obj.cik}/{primary_num}/{filing_obj.accessionNumber}.txt'
    response = get_request(url)
    return response.text


def get_primary_document(filing_obj):
    primary_num = filing_obj.accessionNumber.replace('-', '')
    document = filing_obj.primaryDocument.split('/')[1]
    url = f'https://www.sec.gov/Archives/edgar/data/{filing_obj.cik}/{primary_num}/{document}'
    response = get_request(url)
    return response.content


# =======================================================================
# ===========================Statement Utilities=========================
# =======================================================================

# Register namespaces if there are any
namespaces = {
    'xbrl': "http://www.xbrl.org/2003/instance",
    'xlink': "http://www.w3.org/1999/xlink",
    'iso4217': "http://www.xbrl.org/2003/iso4217",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'us-gaap': "http://fasb.org/us-gaap/2013-01-31",
    'dei': "http://xbrl.sec.gov/dei/2013-01-31",
    'aapl': "http://www.apple.com/20131228",
    'us-types': "http://fasb.org/us-types/2013-01-31",
    'xbrldt': "http://xbrl.org/2005/xbrldt",
    'xbrldi': "http://xbrl.org/2006/xbrldi",
    'stpr': "http://xbrl.sec.gov/stpr/2011-01-31",
    'country': "http://xbrl.sec.gov/country/2013-01-31",
    'currency': "http://xbrl.sec.gov/currency/2012-01-31",
    'exch': "http://xbrl.sec.gov/exch/2013-01-31",
    'invest': "http://xbrl.sec.gov/invest/2013-01-31",
    'num': "http://www.xbrl.org/dtr/type/numeric",
    'nonnum': "http://www.xbrl.org/dtr/type/non-numeric",
    'utr': "http://www.xbrl.org/2009/utr",
}

for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)


def sort_statements_by_date(statements):
    # based on the date organize the data objs
    return sorted(statements, key=lambda statement: statement.end_date)


def get_statement_data(cik: str, gaap_item: str):
    '''
    x = sort_statements_by_date(get_statement_data(
        "0000320193", "RevenueFromContractWithCustomerExcludingAssessedTax"))
    for ii in x:
        print(ii)
    '''
    # Edgar API to get the reporting values of the company based on a GAAP item
    url = f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{gaap_item}.json'
    response = get_request(url)
    if response.ok:
        data = json.loads(response.text)
        statement_objects = []
        unique_combinations = set()  # Set to track unique fp and end_date combinations

        # Assuming that the first unit type in the list is the one we are interested in
        units_list = list(data['units'].values())[0]

        for unit in units_list:
            # Create a tuple of the fp value and end_date for uniqueness check
            fp_end_date_tuple = (unit['fp'], unit['end'])

            if fp_end_date_tuple not in unique_combinations:
                # This combination is unique, so we process and add it to the set
                unique_combinations.add(fp_end_date_tuple)

                # Create the StatementObject
                statement_object = StatementObject(
                    cik=data['cik'],
                    gaap_item=data['tag'],
                    end_date=datetime.strptime(unit['end'], '%Y-%m-%d'),
                    accn=unit['accn'],
                    form=unit['form'],
                    fy=str(unit['fy']).split(".")[0],
                    fp=unit['fp'],
                    value=format_value_as_readable(int(unit['val']))
                )
                # Add the new object to our list
                statement_objects.append(statement_object)
        return statement_objects
    else:
        # Handle the case where the response is not OK
        return None


def extract_context(root, context_ref, namespaces):
    # Search for the 'context' elements with the matching 'id' attribute
    context_elements = root.findall(
        f".//xbrl:context[@id='{context_ref}']", namespaces=namespaces)
    context_objects = []

    for context_element in context_elements:
        entity_identifier_element = context_element.find(
            "xbrl:entity/xbrl:identifier", namespaces=namespaces)
        entity_identifier = entity_identifier_element.text if entity_identifier_element is not None else 'N/A'

        # Extracting the segments with their dimensions and text values
        segments = [
            # (xbrldi:explicitMember dimension,text)
            (member.attrib.get('dimension'), member.text)
            for member in context_element.findall(".//xbrldi:explicitMember", namespaces=namespaces)
        ]

        period_start_date = context_element.findtext(
            "xbrl:period/xbrl:startDate", namespaces=namespaces)
        period_end_date = context_element.findtext(
            "xbrl:period/xbrl:endDate", namespaces=namespaces)
        period_instant = context_element.findtext(
            "xbrl:period/xbrl:instant", namespaces=namespaces)

        context_object = XMLContextObject(
            id=context_ref,
            entity_identifier=entity_identifier,
            segments=segments,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            period_instant=period_instant
        )

        context_objects.append(context_object)

    return context_objects


def extract_tags(xml_data):
    root = ET.fromstring(xml_data)
    extracted_data = []

    for elem in root.iter():
        if 'fasb.org/us-gaap' in elem.tag:
            # Extract the local name (tag without namespace)
            tag = elem.tag.partition('}')[2]
            # Extract the attributes 'contextRef' and 'id'
            # Default 'N/A' if not present
            context_ref = elem.attrib.get('contextRef', 'N/A')
            # Default 'N/A' if not present
            elem_id = elem.attrib.get('id', 'N/A')
            # Default 'N/A' if not present
            unit_ref = elem.attrib.get('unitRef', 'N/A')
            # Default 'N/A' if not present
            decimals = elem.attrib.get('decimals', 'N/A')
            # Extract the text value of the element
            value = elem.text
            context = extract_context(root, context_ref, namespaces)
            # Create a new XMLDataObject and append it to the list
            extracted_data.append(XMLDataObject(
                tag, context_ref, elem_id, value, unit_ref, decimals, context))
    return extracted_data


def find_xml_link(html_content):
    soup = BeautifulSoup(html_content.text, 'html.parser')

    # Find the tbody tag
    tbody = soup.find('table')
    if not tbody:
        return "tbody tag not found"

    # Find all 'a' tags within the tbody tag
    a_tags = tbody.find_all('a')
    for tag in a_tags:
        href = tag.get('href')
        if href and href.endswith('_htm.xml'):
            return href.split('/')[-1]


def get_all_unique_tags(filings):
    unique_tags = set()
    for filing in filings:
        if filing.xml_data:
            unique_tags.update(filing.get_unique_tags())
    return list(unique_tags)


def get_xml(filings, limit=3):
    if not limit:
        limit = len(filings)+1
    base_url = "https://www.sec.gov/Archives/edgar/data/"
    updated_filings = filings
    count = 0
    for index, item in enumerate(filings):
        if item.form.upper() in ["10-Q", "10-K"] and count < limit:
            count += 1
            database_response = get_request(
                f'{base_url}{item.cik}/{item.accessionNumber.replace("-", "")}')
            xml_file_name = find_xml_link(database_response)
            xml_response = get_request(
                f'{base_url}{item.cik}/{item.accessionNumber.replace("-", "")}/{xml_file_name}').content
            data = extract_tags(xml_response)
            updated_filings[index].xml_data = data
    return updated_filings


if __name__ == "__main__":
    ticker = 't'
    cik = ticker_to_cik(ticker)
