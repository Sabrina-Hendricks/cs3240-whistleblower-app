# CS 3240 Student-Athlete WhistleBlower App

__Names:__ _Sabrina Hendricks_, Laura Abood, Eric Weng, Daniel Worth, Gilbert Jany

## To Run the App Locally:
1. Create a virtual environment through an IDE or using `python3 -m venv .venv`.
2. Activate the virtual environment:
   - On Windows: `.\.venv\Scripts\activate`
   - On macOS and Linux: `source .venv/bin/activate`
3. Install the packages using `pip3 install -r requirements.txt`.
4. Set up environment variables:
   - Set your `SECRET_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, and `DATABASE_URL` in your environment.
5. Run the database migrations using `python3 manage.py migrate`.
6. Run the app using `python3 manage.py runserver 8000`.
7. Visit the development server at http://127.0.0.1:8000/.

## My Contributions

### Team Role - Requirements Manager
As the Requirements Manager, my primary responsibility was to lead the requirements elicitation process at the beginning of the project. I ensured that we had a comprehensive understanding of the features required for our project. Throughout the semester, I managed the feature/issue tracker in GitHub, monitoring the state of the project and updating the GitHub repository consistently to reflect the status of our project.

**Reasons I took on the role of Requirements Manager:**
- I was interested in learning how requirements are created.
- I wanted to understand what my fellow students were excited about with our project.
- I enjoy updating spreadsheets and keeping track of project progress.
- I liked knowing “what’s coming next” in a project.

### Code Contributions
In addition to my role as Requirements Manager, I contributed to the code base in the following ways:
- Setting up Google login functionality.
- Implementing functionality for users to submit reports.
- Allowing users to upload different file types and storing them in Amazon S3 storage.
- Implementing functionality to allow users to track the progress of their application.
- Creating custom Django models for our project's specific needs, such as UserForms.
- Allowing users to view all of their reports, delete reports, and manage their profile.
- Contributing to UI design to improve user experience.

## Data Disclaimer

This project was created for CS 3240: Advanced Software Development at UVA during Spring 2024.
As such, no real names, photos, cases, or other data will be uploaded to this repository. Reports will not be reviewed by administrators. 
