~Library Management System
A simple desktop application built with Python and Tkinter for managing a library's book collection and borrowing records. This application features a modern graphical user interface and uses an SQLite database for data storage.
Features
- Book Management: Add, delete, and view books in a central catalog.
- Reader Management: Add new readers and manage their borrowing history.
- Borrowing & Returning: Handle book borrowing and returning, including automatic fine calculation for overdue books.
- Search Functionality: Quickly find books by title or author.
- Dashboard: View recent borrowing and return activity at a glance.
- Modern UI: The interface uses a clean, modern theme from the `ttkthemes` library.
 Prerequisites
Before running the application, ensure you have Python 3.x installed on your system. You will also need to install the required external library.

- Python 3.x
- **pip** (Python package installer)

 Installation
1.  Clone the repository (if applicable) or download the source code.
    Place all the Python files in a single directory.

2.  Install the required Python packages.
    Open a terminal or command prompt and run the following command in the project directory:

    ```bash
    pip install -r requirements.txt
    ```
    This will install `ttkthemes`, which is necessary for the application's visual style.
How to Run

1.  Navigate to the project directory in your terminal.
2.  Execute the main script:

    ```bash
    python library_app.py
    ```

    (Note: Replace `library_app.py` with the actual name of your Python file if it's different).

The application window will open. The database (`library.db`) will be automatically created in the same directory if it doesn't already exist.

## Changing the Theme

The application uses the `ttkthemes` library, allowing you to easily change its appearance.

1.  Open the `library_app.py` file.
2.  Find the following line in the "Main GUI Setup" section:

    ```python
    root = ThemedTk(theme="ubuntu")
    ```

3.  Change the `theme` parameter to any of the available themes, such as `"forest"`, `"azure"`, `"smog"`, or `"plastik"`.

    Example:
    ```python
    root = ThemedTk(theme="azure")
    ```

4.  Save the file and run the application again to see the new theme.

## Database Structure

The application uses an SQLite database with three tables:

-   `books`: Stores information about each book, including title, author, year, fine rate, and quantity.
-   `readers`: Stores reader details, such as their name.
-   `transactions`: Links books to readers and tracks borrowing and return dates, as well as any incurred fines.
