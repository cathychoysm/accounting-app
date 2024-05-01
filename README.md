# Accounting App

This project implements a user-friendly accounting application designed to manage personal or small business finances.

## Project Overview

This accounting app provides a platform to track income and expenses, categorise transactions, and generate financial reports. It aims to simplify financial management by offering an intuitive interface for data entry, visualisation, and analysis.

## Tech Stack

- **Frontend:** JavaScript, HTML, CSS, Bootstrap, Flowbite
- **Backend:** Python, Flask
- **Database:** SQLite

## App Features

- Transaction Management:
  - Add new income and expense entries.
  - Specify transaction details like date, amount, and category.
  - Edit or delete existing transactions.
- Categorization:
  - Create custom categories to organise transactions (e.g., Rent, Utilities, Groceries, Income).
  - Assign categories to each transaction for better financial insights.
- Reporting:
  - Generate reports on income, expenses, and overall financial performance over a specified period.
  - Reports can be presented in various formats (e.g., tables, charts) for easy visualisation.
- Data Persistence:
  - Implement data persistence mechanisms (e.g., local storage, databases) to save transactions and categories beyond application sessions.
  - Allow users to retrieve and manage their financial data across sessions.
- Security:
  - Integrate user authentication and authorisation features to restrict unauthorised access to financial data (consider for sensitive financial information).
  - Implement data encryption mechanisms to safeguard user privacy.

## Getting Started

To run this Flask app on your own server, follow these steps:

### Prerequisites

Make sure you have the following installed on your system:

- Python 3.x
- pip (Python package manager)

### Installation

1. Clone this repository to your local machine using:

`git clone https://github.com/cathychoysm/accounting-app/`

2. Navigate to the project directory:

`cd accounting-app`

3. Install the required Python packages using pip:

`pip install -r requirements.txt`

### Running the App

Once you've completed the installation steps, you can start the Flask app:

`flask run`

By default, the app will run on port 5000. You can access it in your web browser at `http://localhost:5000`.

## Demonstration

<video src="./account-app-demo.mp4" width="1080" autoplay="false" controls></video>
