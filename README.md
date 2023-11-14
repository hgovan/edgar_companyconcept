# edgar_companyconcept
Python app that aggregates GAAP items associated with  a given company
<img width="643" alt="Screen Shot 2023-11-14 at 12 56 04 PM" src="https://github.com/hgovan/edgar_companyconcept/assets/93172468/b4fdf299-d8c9-42ff-81ac-a8a4bd5a1f9a">

# Edgar API Streamlit Application

## Overview
This Streamlit application enables users to search for companies in the EDGAR database using a ticker symbol. It aggregates GAAP financial tags associated with the company and displays the information across all the company's filings via the EDGAR API.

## Features
- Search for companies by ticker symbol
- Display company's GAAP financial data across all filings
- Interactive tables with hyperlinks to the official EDGAR filings

## Installation
To run this application, you need to have Python installed on your system. If you have Python set up, you can follow these steps:

1. Clone this repository to your local machine.
2. Navigate to the cloned directory.
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
4. Run the Streamlit application:
   ```sh
   streamlit run app.py

## Usage
After running the application, you should see a text input where you can enter a company's ticker. Upon submitting a valid ticker, the application will display:

- The company's bio and financial summary.
- A selection of filings to view.
- A dropdown to select a specific GAAP financial tag.
- A downloadable CSV file with GAAP financial data.

## Dependencies
- Streamlit
- Pandas
- Other dependencies that should be listed in `requirements.txt`

## Contributing
Contributions to improve this project are welcome. Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License
This project is open-sourced under the MIT License. See the LICENSE file for more information.

## Contact
For any queries or feedback, please open an issue on the GitHub repository issue tracker.
