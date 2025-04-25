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
## 📁 Chatbot/
1. Multi_Turn_ChatBot.py
This is the main Python script that controls the Streamlit interface and user interactions. It allows users to register, log in, and request business recommendations based on their location and preferences.

Key Components:
Snowflake Connection: The script connects to a Snowflake database to retrieve user preferences and business data.

User Login & Registration: The script has a registration page for new users and a login page for existing users.

Recommendation System: It uses the load_data_from_snowflake() and run_similarity_search() functions to recommend businesses based on user input.

Multi-Turn Chat: After providing initial recommendations, the user can engage in a multi-turn chat, asking follow-up questions about the results.

Main Functions:
screen_0(): Manages user login and registration.

screen_2(): Displays the business recommendation interface and handles the chat input for follow-up questions.

main(): The entry point for the Streamlit app, deciding the flow between screens.

2. chatbotfunction.py
This file contains functions responsible for processing the chat input, handling user queries, and returning relevant results.

Key Components:
process_chat_input(): This function takes the user input from the chat and runs a similarity search using the run_similarity_search() function. It returns relevant business details based on similarity scores.

SentenceTransformer Model: It uses the paraphrase-MiniLM-L6-v2 model to encode the input text and perform semantic search over the business embeddings.

3. utils.py
This utility file provides helper functions for location-based calculations and similarity search.

Key Functions:
load_data_from_snowflake(): This function connects to Snowflake, fetches the business data, and loads it into a DataFrame. The data includes business IDs, names, categories, attributes, and embeddings.

get_lat_lon(): Uses Geopy to get the latitude and longitude of a user’s location based on input (e.g., city name).

run_similarity_search(): This is the core function for performing a similarity search. It filters businesses based on proximity to the user and calculates similarity scores using FAISS and SentenceTransformers. The top businesses are returned based on similarity scores.

## 📁 src/

This directory contains the core modules responsible for data processing, embedding generation, and recommendation logic.

- **data_loader.py**  
  Handles the ingestion of data from AWS S3 into Snowflake using Snowpipe. It defines functions to automate the loading process for the `business`, `reviews`, and `users` tables.

- **embedding_generator.py**  
  Processes the business table to generate embeddings that capture the features of each business. These embeddings are used to understand similarities between businesses.

- **user_profile_builder.py**  
  Constructs user profiles by analyzing their reviews and interactions. It aggregates user preferences to aid in personalized recommendations.

- **recommendation_engine.py**  
  Utilizes the business embeddings and user profiles to generate personalized business recommendations. It likely employs similarity metrics or machine learning models to rank businesses.

---

## 📁 app/

Contains the Streamlit application that serves as the user interface for the recommendation system.

- **app.py**  
  The main entry point for the Streamlit app. It provides an interface for users to input their preferences or user ID and displays personalized business recommendations.

- **utils.py**  
  Contains utility functions used by the Streamlit app, such as formatting outputs, handling user inputs, and interfacing with the recommendation engine.

---

## 📁 config/

Holds configuration files and parameters required for the project.

- **config.yaml**  
  A YAML file containing configuration parameters such as AWS credentials, Snowflake connection details, and other project-specific settings.

---

## 📁 notebooks/

Includes Jupyter notebooks used for exploratory data analysis, prototyping, and testing.

- **eda.ipynb**  
  Performs exploratory data analysis on the Yelp dataset to understand data distributions, missing values, and other insights.

- **embedding_visualization.ipynb**  
  Visualizes the business embeddings using dimensionality reduction techniques like PCA or t-SNE to understand the embedding space.

---

## 📁 tests/

Contains unit tests to ensure the reliability and correctness of the project's components.

- **test_data_loader.py**  
  Tests the functions responsible for loading data from S3 into Snowflake.

- **test_embedding_generator.py**  
  Validates the embedding generation process for the business table.

- **test_recommendation_engine.py**  
  Ensures that the recommendation engine produces valid and personalized recommendations.

---

## 📄 requirements.txt

Lists all Python dependencies required to run the project, including libraries for data processing, machine learning, and web application development.
