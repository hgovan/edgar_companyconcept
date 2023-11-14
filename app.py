import streamlit as st
from utils import filter_by_form, get_all_unique_tags, get_filing, get_statement_data, get_xml, ticker_to_cik, unique_forms
import pandas as pd


def main():
    """
    Main function for the Streamlit app to search and display company filings from EDGAR.
    """
    st.title("EDGAR Company Filings Search")

    company_query = st.text_input("Enter company ticker to search")
    process_company_query(company_query)


def process_company_query(company_query):
    """
    Processes the company query entered by the user.

    Args:
    company_query (str): The company ticker entered by the user.
    """
    if company_query:
        cik = ticker_to_cik(company_query.lower())
        if cik:
            display_company_info(company_query.upper(), cik)
        else:
            st.error("Invalid Ticker. Please enter a valid ticker symbol.")


def display_company_info(ticker, cik):
    """
    Displays information and filings for a given company.

    Args:
    ticker (str): The ticker symbol of the company.
    cik (str): The CIK of the company.
    """
    bio, filings = get_filing(ticker, cik)
    xml_filings = get_xml(filings)
    st.subheader(bio['name'])
    display_company_bio(bio, cik)
    display_gaap_items(cik, xml_filings)


def display_company_bio(bio, cik):
    """
    Displays biographical information of the company.

    Args:
    bio (dict): Biographical information of the company.
    cik (str): The CIK of the company.
    """
    st.success(
        f"CIK: {cik} | {bio['sicDescription']}( sic:{bio['sic'] }) | Fiscal Year End: {bio['fiscalYearEnd']}")
    st.text(f"Exchanges: {bio['Exchanges']}")


def display_filings(filings):
    """
    Displays the filings of the company.

    Args:
    filings (list): The filings of the company.
    """
    filing_types = unique_forms(filings)
    selected_filings = st.multiselect("Select filing types", filing_types)

    if selected_filings:
        filtered_filings = filter_by_form(filings, selected_filings)
        display_filings_table(filtered_filings)


def display_filings_table(filings):
    """
    Displays a table of filings with hyperlinks.

    Args:
    filings (list): The filings to be displayed in the table.
    """
    link_base = '<a href="https://www.sec.gov/Archives/edgar/data/'
    link_end = '" target="_blank">Link to Edgar filing</a>'
    data = {"reportDate": [], "filingDate": [], "form": [], "Link": []}

    for ii in filings:
        data['form'].append(ii.form)
        data['filingDate'].append(ii.filingDate)
        data['reportDate'].append(ii.reportDate)
        link = f'{link_base}{ii.cik}/{ii.accessionNumber.replace("-", "")}/{link_end}'
        data['Link'].append(link)

    df = pd.DataFrame(data)
    html = df.to_html(escape=False)
    st.markdown(html, unsafe_allow_html=True)


def display_gaap_items(cik, filings):
    """
    Displays the filings of the company.

    Args:
    filings (list): The filings of the company.
    """
    gaap_items = get_all_unique_tags(filings)
    selected_gaap_item = st.selectbox("Select GAAP Item", gaap_items)
    if selected_gaap_item:
        statement_objects = get_statement_data(cik, selected_gaap_item)
        if statement_objects:
            display_gaap_item_table(statement_objects)
        else:
            st.text("please select a new GAAP Item")


def display_gaap_item_table(statement_objects):
    """
    Displays a table of filings with hyperlinks.

    Args:
    filings (list): The filings to be displayed in the table.
    """
    link_base = '<a href="https://www.sec.gov/Archives/edgar/data/'
    link_end = '" target="_blank">Link to Edgar filing</a>'
    data = {"gaap_item": [], "year": [], "quarter": [],
            "form": [], "value": [], "Link": []}

    for ii in statement_objects:
        data['gaap_item'].append(ii.gaap_item)
        data['year'].append(ii.fy)
        data['quarter'].append(ii.fp)
        data['form'].append(ii.form)
        data['value'].append(ii.value)
        link = f'{link_base}{ii.cik}/{ii.accn.replace("-", "")}/{link_end}'
        data['Link'].append(link)

    df = pd.DataFrame(data)
    html = df.to_html(escape=False, index=False)
    csv = convert_df(df)
    st.download_button(
        "Download CSV",
        csv,
        "file.csv",
        "text/csv",
        key='download-csv'
    )
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


if __name__ == "__main__":
    main()
