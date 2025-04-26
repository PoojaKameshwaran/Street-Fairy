# Street-Fairy: Business Recommendations ChatBot with Personalized Itinerary Planning

Street Fairy is a business recommendation system that leverages the Yelp dataset to provide personalized suggestions to users. The project integrates Snowflake and Streamlit to deliver real-time recommendations through a user-friendly interface.

## Overview

The project aims to recommend businesses to users based on their preferences and reviews. It processes data from the Yelp dataset, stores it in Snowflake, and utilizes embeddings to understand business characteristics. A Streamlit app serves as the front-end, allowing users to interact with the recommendation system seamlessly.

## Architecture

- **Data Ingestion**: Yelp dataset is stored in AWS S3.
- **Data Loading**: Snowpipe is used to load data from S3 into Snowflake tables (`business`, `reviews`, `users`).
- **Data Processing**:
  - Embeddings are created for businesses to capture their features.
  - User preferences are analyzed based on their reviews and interactions.
- **Recommendation Engine**: An LLM (Large Language Model) processes embeddings to generate personalized recommendations.
- **Front-End**: A Streamlit app provides an interface for users to receive and interact with recommendations.

  ![WhatsApp Image 2025-04-24 at 21 35 13_8cba642f](https://github.com/user-attachments/assets/f2e3c730-01be-4099-9ae4-e88687678c38)


## Features

- **Real-Time Recommendations**: Get instant business suggestions based on user preferences.
- **Interactive Interface**: User-friendly Streamlit app for seamless interaction.
- **Scalable Architecture**: Utilizes Snowflake and AWS S3 for efficient data storage and processing.
- **Advanced Analytics**: Employs embeddings and LLMs for deep understanding of business features and user preferences.

---



## 📂 Chatbot/

---

* **main.py**  
  Entry point for the app; starts the Streamlit UI.
  App entry point.
  Imports and launches the main Streamlit UI with screen_ui().
---



* **screen.py**  
  - Main UI router: sidebar, tabs (login & chat), navigation logic. Sets up the sidebar, manages tab navigation (Login/Register, Recommendations & Chat), and delegates control to the appropriate screen.
  
  - Main UI logic and navigation for the app.

  - Configures Streamlit’s page settings (title, layout).

  - Builds a sidebar with app info and user login status.

  - Uses two main tabs: Login/Register and Recommendations & Chat.

  - Delegates logic to screen_0 (login/register) and screen_2 (chat) based on user session state.

  - nsures users must log in before accessing chat/recommendations
---


* **screens/chat.py**  
  - Chat UI: manages chat history, user queries, recommendations, and conversation flow. Conversational chat interface. Handles user chat, displays chat history, handles user input, business   
    recommendations, and context-aware suggestions based on user actions and search queries.

  - Conversational chat screen with the Street Fairy assistant.

  - Shows a sticky, modern chat UI using Streamlit’s chat components and custom CSS.

  - Displays chat history (user and assistant messages). Accepts and processes user chat input.

  - Checks if the user is referencing a previously recommended business. Handles search for nearby places using embedding-based similarity.

  - Shows friendly, summarized recommendations with LLM-generated responses (via Ollama). Supports "planning mode" for navigation between places.

  - Updates and reruns UI after each new user input.

---


* **screens/login.py**  
  - User login/registration UI; connects to Snowflake for authentication and preference storage. User authentication and registration.
  - Manages user login and new user registration. Connects to Snowflake to check credentials or create a new user. Loads and updates user preferences in session state.
  - User authentication and registration interface. Presents a radio button to switch between Login and Registration.
  - On login: Connects to Snowflake and verifies credentials. Loads user name, ID, and preference categories into session state. Initializes feedback tracking (liked/disliked categories).
  - On registration: Accepts user details and preferences. Inserts new user record into the Snowflake database. Handles errors (duplicate ID, missing fields). Provides clear feedback for success, errors, or incomplete forms.

---


* **utils/database.py**  
   - Database helper functions; handles connection and updates to user preferences in Snowflake. Database utilities. Connects to Snowflake using credentials in key.json. Provides functions to retrieve and update user preferences securely.

  - Helper functions for database operations (Snowflake).

  - Loads Snowflake credentials from a secure key.json (not in repo).

  - Creates and returns a Snowflake database connection object.

  - Updates user preferences (CATEGORIES) in the database when users like/dislike businesses.

  - Uses Streamlit toast/alerts for feedback on preference updates.

  - Handles connection cleanup and error reporting gracefully.

---


* **utils/query.py**  
  - Embedding search using ChromaDB, distance calculation, and calls to the LLM API (Ollama) for natural language recommendations. Embedding-based search and LLM integration.
    
  - Loads the ChromaDB business embeddings collection, runs semantic similarity search with SentenceTransformer embeddings, computes distances, and returns ranked business results. Also provides query_ollama() for generating recommendations using a local LLM via HTTP API.

  - Handles embedding search, vector retrieval, and LLM interaction. Loads a persistent ChromaDB collection with SentenceTransformer embeddings.

  - Performs semantic similarity searches for user queries: Returns metadata-rich business results (location, stars, categories, etc.).

  - Computes distances (using geopy) between user and business locations.

  - Handles missing data by generating default values (e.g., stars, distances).

  - Provides a function to send prompts to a local Ollama LLM server (or any compatible LLM API). Returns model-generated, contextually relevant recommendations for the chat UI.

Uses caching for fast repeated access to the ChromaDB collection.
---


### 1. **Multi_Turn_ChatBot.py**
*Main Streamlit application controlling the user interface and interactions.*

- **Snowflake Connection:** Connects to the Snowflake database to retrieve business and user data.
- **User Login & Registration:** Provides pages for both new user registration and existing user login.
- **Recommendation System:** Uses `load_data_from_snowflake()` and `run_similarity_search()` to generate business recommendations based on user input and preferences.
- **Multi-Turn Chat:** Supports conversational follow-ups, allowing users to ask additional questions after receiving initial recommendations.

**Main Functions:**
- `screen_0()`: Manages login and registration workflows.
- `screen_2()`: Handles recommendation display and chat-based interactions.
- `main()`: Entry point deciding which screen to show.

---


---

## 📁 DBT Models/

This directory contains all DBT models and configuration files used for transforming and enriching the business dataset for the recommendation engine.

---

### 1. **Attribute_Model.sql**
*Extracts and flattens business attributes from JSON.*

- Parses the `Attributes` column for open businesses in selected states.
- Flattens the JSON attributes into key-value pairs for easier downstream processing.

---

### 2. **Attribute_Processing_Model.sql**
*Processes and normalizes complex, nested attribute values.*

- Cleans up attribute values by handling quotes, `None`, and other string patterns.
- Further flattens nested JSON objects by concatenating attribute names and sub-keys.

---

### 3. **Business_Model.sql**
*Cleans and structures the business table.*

- Selects open businesses with at least a 3-star rating from specified states.
- Extracts business details including name, address, categories, and daily hours.

---

### 4. **Category_Model.sql**
*Splits and flattens business categories.*

- Splits the `Categories` field into individual values for each business.
- Produces a table of business-category pairs for flexible category analysis.

---

### 5. **Final_Attribute_Model.sql**
*Combines and cleans processed attributes.*

- Merges results from `Attribute_Model` and `Attribute_Processing_Model`.
- Removes invalid or placeholder values, standardizing the final attribute set for each business.

---

### 6. **dbt_project.yml**
*DBT project configuration file.*

- Defines project structure, model/materialization defaults, and folder paths for models, macros, seeds, etc.

---

### 7. **schema.yml**
*Schema and data quality tests for DBT models.*

- Documents each model and its columns.
- Adds tests for primary/foreign keys (e.g., uniqueness and not-null constraints) to ensure data quality.

---


## 📁 LLM/

This directory contains scripts for embedding generation, vector search, and LLM-powered business recommendation logic, integrated with Snowflake and FAISS.

---

### 1. **Embeddings_Snowflake.py**
*Generates sentence embeddings for businesses and loads them into Snowflake.*

- Connects to Snowflake and fetches business data.
- Processes and flattens business attributes and hours into descriptive text.
- Uses `SentenceTransformer` to generate embeddings for each business.
- Builds a FAISS index for fast vector search.
- Batch-inserts the business embeddings into the `BUSINESS_EMBEDDINGS` table in Snowflake.

---

### 2. **LLM_CODE.py**
*Performs similarity search and business recommendations via command line.*

- Connects to Snowflake and loads business embeddings.
- Retrieves user location via city input and filters businesses within a 5 km radius.
- Uses FAISS and `SentenceTransformer` to compute semantic similarity with user queries.
- Outputs and saves the top recommended businesses as a CSV file.

---

### 3. **LLM_CODE_Streamlit.py**
*Streamlit-based UI for LLM-powered business recommendations.*

- Loads business embeddings from Snowflake.
- Accepts user location and query through a Streamlit form.
- Filters businesses within a 5 km radius.
- Runs semantic similarity search with FAISS and `SentenceTransformer`.
- Displays top results in an interactive data table and allows CSV download.

---

**Dependencies:**  
- `streamlit`  
- `snowflake-connector-python`  
- `sentence-transformers`  
- `faiss-cpu`  
- `geopy`  
- `pandas`, `numpy`, `scikit-learn`

---

**Usage:**  
- Use `Embeddings_Snowflake.py` to (re)generate and store embeddings.
- Run `LLM_CODE.py` for terminal-based recommendations.
- Run `LLM_CODE_Streamlit.py` for an interactive Streamlit app:
  ```bash
  streamlit run LLM_CODE_Streamlit.py
---


## 📁 data-ingestion/

This folder contains scripts for data loading, transformation, S3/Snowflake operations, and vector database (ChromaDB) ingestion for the Street Fairy project.

---

### 1. **Filtered_Attribute_Creation.py**
*Filters and aggregates business attributes, then loads them into Snowflake.*

- Connects to Snowflake and queries for clean, non-null attribute values.
- Aggregates attributes per business and inserts them into the `Filtered_Attributes` table.

---

### 2. **S3_Data_Load.py**
*Uploads local CSV files to AWS S3 buckets.*

- Uses `boto3` to authenticate and interact with AWS S3.
- Uploads the main business dataset to an S3 bucket for further use.

---

### 3. **S3_Snowflake_DataLoad_Github.py**
*Loads CSV data from S3 into Snowflake tables.*

- Connects to Snowflake and runs a `COPY INTO` command to load CSV data from S3 stage into a Snowflake table.

---

### 4. **cleanup_kb.py**
*Deletes the persistent vector database collection.*

- Connects to ChromaDB and deletes the `street_fairy_business_kb` collection for a clean slate.

---

### 5. **ingest_business_kb.py**
*Ingests enriched business data from Snowflake into ChromaDB for vector search.*

- Pulls business records using Snowpark.
- Formats business metadata and descriptions for semantic search.
- Adds documents and metadata to ChromaDB with embeddings for later retrieval.

---

### 6. **ingest_kb.py**
*Joins filtered categories and attributes, formats, and ingests them into ChromaDB.*

- Merges categories and attributes from Snowflake.
- Flattens and cleans metadata for each business.
- Ingests into a persistent ChromaDB collection using semantic embeddings.

---

### 7. **query_vectordb.py**
*Runs semantic search queries against the local ChromaDB knowledge base.*

- Connects to the ChromaDB collection with SentenceTransformer embeddings.
- Accepts user questions, runs vector search, and prints top business matches and their metadata.

---

---

**Usage:**  
- Use ingestion scripts to process, clean, and load data into Snowflake, S3, and ChromaDB as needed.
- Use `query_vectordb.py` for testing semantic search over the vector database.
---


## 📁 app/

Contains the Streamlit application that serves as the user interface for the recommendation system.

- **streamlit_app.py**  
  The main entry point for the Streamlit app. It provides an interface for users to input their preferences or user ID and displays personalized business recommendations.

---


---

## 📁 notebooks/

Includes Jupyter notebooks used for exploratory data analysis, prototyping, and testing.

- **Data_preprocess_StreetFairy.ipynb**  
  Performs data preprocessing and analysis on the Yelp dataset to clean and understand data distributions, missing values, and other insights.
  Store the cleaned business and reviews table in a seperate table to be processed for embeddings.

---



## 📄 requirements.txt

Lists all Python dependencies required to run the project, including libraries for data processing, machine learning, and web application development.
