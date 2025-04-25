# Street-Fairy

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
