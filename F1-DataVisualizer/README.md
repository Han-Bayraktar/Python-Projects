# 🏎️ F1 Data Visualizer

Welcome to the **F1 Data Visualizer** project! 🚀

This project brings Formula 1 history to life through **interactive data visualizations**, combining all-time statistics with season-by-season breakdowns for both **drivers** and **constructors**. Whether you’re a data enthusiast 📊 or an F1 superfan 🏁, this tool gives you a clear and engaging way to explore the sport.

---

## ✨ Features

### 📂 Data Loading & Preprocessing

- Loads official Kaggle F1 datasets (`drivers.csv`, `constructors.csv`, `results.csv`, `races.csv`, etc.).
- Cleans and merges datasets into **analysis-ready tables**.

### 🏆 Analytics

- **All-Time Driver Points Leaderboard**
- **All-Time Constructor Points Leaderboard**
- **Driver Championships per Season**
- **Constructor Championships per Season**
- Per-season **points standings**
- Driver **race-by-race performance**
- **Sprint race analysis** 🔥

### 📊 Visualizations

- Horizontal bar charts for top drivers & constructors
- Pie charts for championship distribution
- Line charts showing point progression throughout a season
- Responsive, publication-ready figures (no overlapping labels!)

### 🌐 Interactive App (Streamlit)

Choose your view:

- **All-Time** or a specific **Season** 📅
- Filter by **Driver** or **Constructor** 🧑‍🚀
- View **detailed race results**, including sprints ⚡
- Visualizations update instantly 🎨

---

## ⚙️ Installation

Clone the repository and set up your environment:

```bash
git clone https://github.com/yourusername/F1-DataVisualizer.git
cd F1-DataVisualizer
python -m venv .venv
source .venv/bin/activate  # (Linux/Mac)
.venv\Scripts\activate   # (Windows)
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### 🖥️ Exploratory Notebook

Run the Jupyter Notebook for step-by-step analysis:

```bash
jupyter notebook notebooks/exploratory.ipynb
```

### 🌐 Interactive Streamlit App

Launch the web app:

```bash
streamlit run app.py
```

Then open your browser at `http://localhost:8501` 🎉

---

## 📸 Preview

- **All-Time Driver Points Leaderboard**&#x20;
- **Constructor Championships Pie Chart**&#x20;
- **Race-by-Race Season Performance**&#x20;

---

## 📂 Project Structure

```
F1-DataVisualizer/
│
├── data/               # Raw CSV datasets from Kaggle
├── notebooks/          # Exploratory analysis (Jupyter)
├── src/                # Core Python modules
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── analytics.py
│   ├── visualizer.py
│   └── main.py
├── app.py              # Streamlit application
├── requirements.txt    # Dependencies
└── README.md           # Project documentation
```

---

## 🛠️ Tech Stack

- **Python** 🐍
- **Pandas** for data wrangling
- **Matplotlib & Seaborn** for visualization
- **Streamlit** for the interactive app

---

## 🙌 Contributing

Contributions are welcome! 💡 Feel free to submit a pull request, suggest new features, or open issues.

---

## 📜 License

MIT License © 2025

---

🚦 Start your engines and enjoy exploring F1 like never before! 🏁

