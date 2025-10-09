# Gemini Project: Energy Load Analysis Application

## 1. Project Overview

This project is to create a web-based energy load analysis application. The primary purpose of this application is to allow users to visualize and analyze energy consumption data against energy generation data. Users will be able to upload their own hourly energy load data and overlay it with various energy generation sources to assess if the generation is sufficient to meet the demand.

The application should have a simple, clean, and corporate-style user interface. All data will be stored in a local SQLite database. The backend will be developed using Python with the Flask web framework, and the data visualization will be handled by a suitable Python charting library that can produce interactive, dual-axis graphs.

## 2. Core Functionality

- **User Management:** (Optional - for future consideration) Basic user authentication to manage different customer data.
- **Data Selection:** Users must be able to select the scope of their analysis by choosing a customer, one or more facilities, one or more buildings, or one or more meters.
- **Data Upload:**
    - Users can upload hourly energy load data at the meter level in CSV format.
    - This data should be processed and aggregated to the building, facility, and customer levels.
    - Users can also upload hourly generation data from existing sources in CSV format.
- **Generation Source Definition:**
    - Users can define anticipated generation sources with varying sizes and types (e.g., solar, wind, conventional).
    - Users can define a custom "block" of power purchased from a supplier, specifying the capacity and duration.
- **Data Visualization:**
    - The core of the application will be a graph that visualizes the energy load and generation.
    - The energy load should be displayed as a line graph on the left Y-axis.
    - The energy generation should be displayed as a stacked bar graph on the right Y-axis, with each segment of the bar representing a different generation source.
    - The X-axis will represent time in hourly intervals.
- **Analysis:** The visual representation will allow users to quickly identify periods of energy surplus or deficit.

## 3. Technology Stack

- **Backend:** Python
- **Web Framework:** Flask
- **Database:** SQLite
- **Data Visualization Library:** Plotly Dash or Chart.js (to be integrated with Flask)
- **Frontend:** HTML, CSS, JavaScript (for a clean, corporate look and feel)

## 4. Database Schema

The SQLite database should have the following tables:

- **`customers`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `name` (TEXT, NOT NULL)
- **`facilities`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `customer_id` (INTEGER, FOREIGN KEY to `customers.id`)
    - `name` (TEXT, NOT NULL)
- **`buildings`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `facility_id` (INTEGER, FOREIGN KEY to `facilities.id`)
    - `name` (TEXT, NOT NULL)
- **`meters`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `building_id` (INTEGER, FOREIGN KEY to `buildings.id`)
    - `name` (TEXT, NOT NULL)
- **`load_data`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `meter_id` (INTEGER, FOREIGN KEY to `meters.id`)
    - `timestamp` (DATETIME, NOT NULL)
    - `load_mw` (REAL, NOT NULL)
- **`generation_sources`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `name` (TEXT, NOT NULL)
    - `type` (TEXT) -- e.g., 'Solar', 'Wind', 'Purchased Block'
- **`generation_data`**:
    - `id` (INTEGER, PRIMARY KEY)
    - `source_id` (INTEGER, FOREIGN KEY to `generation_sources.id`)
    - `timestamp` (DATETIME, NOT NULL)
    - `generation_mw` (REAL, NOT NULL)

## 5. Application Structure (File Layout)
/energy-load-analysis
|-- app.py
|-- static/
| |-- css/
| | |-- style.css
| |-- js/
| |-- main.js
|-- templates/
| |-- index.html
| |-- layout.html
|-- database/
| |-- database.db
|-- uploads/
|-- requirements.txt
|-- gemini.md

## 6. Step-by-Step Implementation Guide

**Step 1: Project Setup**
- Create the project directory structure as outlined above.
- Initialize a Python virtual environment.
- Create a `requirements.txt` file with the following libraries:
    - `flask`
    - `pandas`
    - `plotly` (or other charting library)
    - `sqlalchemy` (for database interaction)
- Create a `database.py` script to set up the SQLite database and tables based on the schema in section 4.

**Step 2: Backend Development (Flask)**
- In `app.py`, create the main Flask application.
- Implement routes for:
    - The main dashboard page (`/`).
    - Data upload functionality (e.g., `/upload_load`, `/upload_generation`).
    - API endpoints to fetch data for the graph (e.g., `/api/load_data`, `/api/generation_data`).
- Implement the logic for processing uploaded CSV files using the pandas library and storing the data in the SQLite database.
- Implement the logic for aggregating meter-level data to building, facility, and customer levels.

**Step 3: Frontend Development**
- Create the base HTML template in `templates/layout.html` with a clean and corporate design.
- In `templates/index.html`, create the user interface with:
    - Dropdown menus to select customer, facility, building, and/or meters.
    - File upload forms for load and generation data.
    - A section to define custom generation sources.
    - A placeholder for the data visualization graph.
- Use CSS in `static/css/style.css` to style the application with a corporate look.
- Use JavaScript in `static/js/main.js` to handle user interactions, such as dynamically updating dropdowns and making AJAX calls to the backend to fetch data for the graph.

**Step 4: Data Visualization**
- Use a library like Plotly.js or Chart.js to create the interactive, dual-axis chart.
- The left Y-axis will display the load data as a line chart.
- The right Y-axis will display the generation data as a stacked bar chart.
- The JavaScript code will fetch the data from the Flask API endpoints and render the chart on the page.

**Step 5: Putting It All Together**
- Ensure the frontend and backend are correctly integrated.
- Test the application by uploading sample load and generation data.
- Verify that the data is correctly stored in the database and that the graph accurately reflects the uploaded and defined data.

## 7. Instructions for Gemini

- When generating code, please adhere to the PEP 8 style guide for Python.
- Add comments to the code to explain complex logic.
- For the frontend, prioritize a clean and user-friendly interface.
- Provide a clear and concise `README.md` file for the final project that explains how to set up and run the application.
