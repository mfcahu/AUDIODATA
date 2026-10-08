# 🎵 AudioData - Music Data Analysis & Integration Platform

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)

## 📌 Overview
**AudioData** is a web application developed to extract, normalize, and compare music popularity data across four different platforms. The project implements a robust ETL (Extract, Transform, Load) pipeline to provide a unified view of music metrics.

## 🚀 Key Features
- **ETL Pipeline:** Seamlessly integrates data from various REST APIs and Web Scraping.
- **Data Normalization & Consensus:** Implements a custom consensus algorithm using Regex to accurately match and compare tracks/artists across different platforms.
- **Caching System:** Uses an SQLite caching layer to optimize API limits and reduce loading times.
- **Containerized Deployment:** Fully containerized using Docker and deployed on Google Cloud Run for high availability.

## 📂 Project Structure
The application follows a modular architecture:
- `audiodata_core/`: Core business logic, data normalization, and consensus algorithms.
- `audiodata_integrations/`: Third-party API integrations and web scraping modules (BeautifulSoup4).
- `audiodata_persistence/`: Database models and local caching system using SQLite.
- `audiodata_web/`: Flask-based web server and front-end dashboard.

## 🛠️ Built With
- **Backend:** Python, Flask
- **Data Extraction:** REST APIs, BeautifulSoup4
- **Database:** SQLite
- **DevOps:** Docker, Google Cloud Run

## ⚙️ How to Run Locally

Since the project is containerized with Docker, running it locally is very straightforward.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mfcahu/AUDIODATA.git](https://github.com/mfcahu/AUDIODATA.git)
   cd AUDIODATA
